import { useState, useRef, useCallback } from 'react'
import { createChatWS } from '../api/chat'

const STEP_LABELS = {
  query_rewriter: 'Query Rewrite',
  metadata_extractor: 'Metadata Extract',
  retriever: 'Retrieval',
  answer_generator: 'Generating',
}

export default function useChat() {
  const [messages, setMessages] = useState([])
  const [streamingText, setStreamingText] = useState('')
  const [activeSteps, setActiveSteps] = useState([])
  const [completedSteps, setCompletedSteps] = useState([])
  const [isLoading, setIsLoading] = useState(false)
  const wsRef = useRef(null)
  const pendingQuestion = useRef(null)

  const handleWSMessage = useCallback((event) => {
    const data = JSON.parse(event.data)

    switch (data.type) {
      case 'step':
        if (data.status === 'started') {
          setActiveSteps(prev => [...prev, data.node])
        } else {
          setCompletedSteps(prev => [...prev, data.node])
          setActiveSteps(prev => prev.filter(n => n !== data.node))
        }
        break

      case 'token':
        setStreamingText(prev => prev + data.content)
        break

      case 'done':
        setMessages(prev => [...prev, {
          role: 'assistant',
          content: data.answer,
          citations: data.citations || [],
          chart: data.chart_data || null,
        }])
        setStreamingText('')
        setActiveSteps([])
        setCompletedSteps(data.workflow_steps || [])
        setIsLoading(false)
        break

      case 'error':
        setMessages(prev => [...prev, {
          role: 'assistant',
          content: `Error: ${data.message}`,
          citations: [],
        }])
        setStreamingText('')
        setActiveSteps([])
        setIsLoading(false)
        break
    }
  }, [])

  const connect = useCallback(() => {
    const ws = createChatWS()

    ws.onopen = () => {
      console.log('WebSocket connected')
      // Send pending question if there is one
      if (pendingQuestion.current) {
        ws.send(JSON.stringify({ type: 'question', question: pendingQuestion.current }))
        pendingQuestion.current = null
      }
    }

    ws.onmessage = handleWSMessage

    ws.onerror = (err) => {
      console.error('WebSocket error', err)
      setIsLoading(false)
    }

    ws.onclose = () => {
      console.log('WebSocket closed')
      wsRef.current = null
    }

    wsRef.current = ws
  }, [handleWSMessage])

  const sendQuestion = useCallback((question) => {
    setMessages(prev => [...prev, { role: 'user', content: question }])
    setStreamingText('')
    setCompletedSteps([])
    setActiveSteps([])
    setIsLoading(true)

    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'question', question }))
    } else {
      // Store question and connect - it will be sent in onopen
      pendingQuestion.current = question
      connect()
    }
  }, [connect])

  return {
    messages,
    streamingText,
    activeSteps,
    completedSteps,
    isLoading,
    sendQuestion,
    stepLabels: STEP_LABELS,
  }
}
