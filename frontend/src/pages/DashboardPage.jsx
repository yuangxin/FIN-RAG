import { useState, useCallback, useRef, useEffect } from 'react'
import { Moon, Sun, GripHorizontal } from 'lucide-react'
import DocumentSidebar from '../components/DocumentSidebar'
import ChatPanel from '../components/ChatPanel'
import FinancialCharts from '../components/FinancialCharts'
import useChat from '../hooks/useChat'
import useDocuments from '../hooks/useDocuments'

const MIN_CHART_HEIGHT = 100
const MAX_CHART_HEIGHT = 600

export default function DashboardPage({ darkMode, setDarkMode }) {
  const chat = useChat()
  const docs = useDocuments()
  const [chartHeight, setChartHeight] = useState(256)
  const dragging = useRef(false)
  const startY = useRef(0)
  const startHeight = useRef(0)

  const onMouseDown = useCallback((e) => {
    dragging.current = true
    startY.current = e.clientY
    startHeight.current = chartHeight
    document.body.style.cursor = 'row-resize'
    document.body.style.userSelect = 'none'
    e.preventDefault()
  }, [chartHeight])

  useEffect(() => {
    const onMouseMove = (e) => {
      if (!dragging.current) return
      const delta = startY.current - e.clientY
      const newHeight = Math.min(MAX_CHART_HEIGHT, Math.max(MIN_CHART_HEIGHT, startHeight.current + delta))
      setChartHeight(newHeight)
    }
    const onMouseUp = () => {
      if (!dragging.current) return
      dragging.current = false
      document.body.style.cursor = ''
      document.body.style.userSelect = ''
    }

    window.addEventListener('mousemove', onMouseMove)
    window.addEventListener('mouseup', onMouseUp)
    return () => {
      window.removeEventListener('mousemove', onMouseMove)
      window.removeEventListener('mouseup', onMouseUp)
    }
  }, [])

  return (
    <div className="h-screen flex flex-col">
      {/* Header */}
      <header className={`flex items-center justify-between px-6 py-3 ${darkMode ? 'glass-header' : 'glass-header-light'}`}>
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center shadow-lg shadow-indigo-500/20">
            <span className="text-white text-sm font-bold">10K</span>
          </div>
          <h1 className="text-lg font-bold bg-gradient-to-r from-indigo-400 to-purple-400 bg-clip-text text-transparent">
            10-K QA
          </h1>
          <span className="text-xs px-2 py-0.5 rounded-full bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
            Beta
          </span>
        </div>
        <button
          onClick={() => setDarkMode(!darkMode)}
          className={`p-2.5 rounded-xl transition-all duration-200 ${
            darkMode
              ? 'hover:bg-white/10 text-gray-400 hover:text-yellow-400'
              : 'hover:bg-black/5 text-gray-500 hover:text-indigo-600'
          }`}
        >
          {darkMode ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
        </button>
      </header>

      {/* Main content */}
      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar */}
        <DocumentSidebar
          documents={docs.documents}
          selectedDocId={docs.selectedDocId}
          onSelect={docs.setSelectedDocId}
          onUpload={docs.upload}
          onRemove={docs.remove}
          uploading={docs.uploading}
          uploadMsg={docs.uploadMsg}
          darkMode={darkMode}
        />

        {/* Main area */}
        <div className="flex-1 flex flex-col">
          {/* Chat */}
          <div className="flex-1 overflow-hidden">
            <ChatPanel
              messages={chat.messages}
              streamingText={chat.streamingText}
              activeSteps={chat.activeSteps}
              completedSteps={chat.completedSteps}
              stepLabels={chat.stepLabels}
              isLoading={chat.isLoading}
              onSend={chat.sendQuestion}
              darkMode={darkMode}
            />
          </div>

          {/* Financial Charts + Resize Handle */}
          {docs.selectedDocId && (
            <>
              <div
                onMouseDown={onMouseDown}
                className={`flex items-center justify-center h-5 cursor-row-resize transition-colors ${
                  darkMode
                    ? 'hover:bg-indigo-500/10 border-y border-white/5'
                    : 'hover:bg-indigo-50 border-y border-gray-200'
                }`}
              >
                <GripHorizontal className={`w-4 h-4 ${darkMode ? 'text-gray-600' : 'text-gray-300'}`} />
              </div>
              <div
                style={{ height: chartHeight }}
                className="overflow-y-auto"
              >
                <FinancialCharts docId={docs.selectedDocId} documents={docs.documents} darkMode={darkMode} />
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
