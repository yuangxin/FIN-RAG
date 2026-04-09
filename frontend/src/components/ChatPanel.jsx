import { useState } from 'react'
import { Send, Sparkles } from 'lucide-react'
import ChatMessage from './ChatMessage'
import WorkflowStatus from './WorkflowStatus'
import ReactMarkdown from 'react-markdown'

export default function ChatPanel({ messages, streamingText, activeSteps, completedSteps, stepLabels, isLoading, onSend, darkMode }) {
  const [input, setInput] = useState('')

  const handleSubmit = (e) => {
    e.preventDefault()
    const q = input.trim()
    if (!q || isLoading) return
    onSend(q)
    setInput('')
  }

  return (
    <div className="flex flex-col h-full">
      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-1">
        {messages.length === 0 && !streamingText && (
          <div className="flex items-center justify-center h-full">
            <div className="text-center max-w-md">
              <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center shadow-lg shadow-indigo-500/25">
                <Sparkles className="w-7 h-7 text-white" />
              </div>
              <h2 className={`text-xl font-semibold mb-2 ${darkMode ? 'text-gray-200' : 'text-gray-800'}`}>
                Welcome to 10-K Financial QA
              </h2>
              <p className={`text-sm leading-relaxed ${darkMode ? 'text-gray-500' : 'text-gray-400'}`}>
                Upload a 10-K/10-Q filing, then ask questions about financial data, risk factors, or any section of the report.
              </p>
              <div className={`mt-4 flex flex-wrap justify-center gap-2`}>
                {['Revenue trends', 'Key risk factors', 'Revenue vs Net Income'].map(q => (
                  <span
                    key={q}
                    className={`text-xs px-3 py-1.5 rounded-full ${
                      darkMode
                        ? 'bg-white/5 text-gray-400 border border-white/10'
                        : 'bg-gray-100 text-gray-500 border border-gray-200'
                    }`}
                  >
                    {q}
                  </span>
                ))}
              </div>
            </div>
          </div>
        )}
        {messages.map((msg, i) => (
          <ChatMessage key={i} message={msg} darkMode={darkMode} />
        ))}

        {/* Streaming text */}
        {streamingText && (
          <div className="flex justify-start mb-4">
            <div className={`max-w-[80%] rounded-2xl px-4 py-3 ${
              darkMode ? 'chat-bubble-bot' : 'chat-bubble-bot-light'
            }`}>
              <div className={`text-sm prose prose-sm max-w-none ${darkMode ? 'dark:prose-invert' : ''}`}>
                <ReactMarkdown>{streamingText}</ReactMarkdown>
                <span className="inline-block w-1.5 h-4 bg-indigo-400 animate-pulse ml-0.5 rounded-full" />
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Workflow Status */}
      <div className="px-4 pb-2">
        <WorkflowStatus
          activeSteps={activeSteps}
          completedSteps={completedSteps}
          stepLabels={stepLabels}
          darkMode={darkMode}
        />
      </div>

      {/* Input */}
      <form onSubmit={handleSubmit} className={`p-4 pt-2 ${darkMode ? 'border-white/5' : 'border-black/5'} border-t`}>
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask about financial reports..."
            className={`flex-1 px-4 py-3 rounded-xl text-sm ${
              darkMode ? 'glass-input text-gray-200 placeholder-gray-500' : 'glass-input-light text-gray-900 placeholder-gray-400'
            } focus:outline-none`}
            disabled={isLoading}
          />
          <button
            type="submit"
            disabled={isLoading || !input.trim()}
            className="btn-gradient px-4 py-3 text-white rounded-xl disabled:opacity-30 disabled:cursor-not-allowed disabled:shadow-none disabled:transform-none"
          >
            <Send className="w-4 h-4" />
          </button>
        </div>
      </form>
    </div>
  )
}
