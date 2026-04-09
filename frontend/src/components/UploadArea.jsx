import { useCallback, useState } from 'react'
import { Upload, FileText } from 'lucide-react'

export default function UploadArea({ onUpload, uploading, docCount, maxDocs, darkMode }) {
  const [dragOver, setDragOver] = useState(false)
  const limitReached = docCount >= maxDocs

  const handleFiles = useCallback(async (files) => {
    for (const file of files) {
      if (file.name.endsWith('.pdf')) {
        await onUpload(file)
      }
    }
  }, [onUpload])

  const handleDrop = useCallback((e) => {
    e.preventDefault()
    setDragOver(false)
    handleFiles(e.dataTransfer.files)
  }, [handleFiles])

  const handleChange = useCallback((e) => {
    handleFiles(e.target.files)
  }, [handleFiles])

  return (
    <div>
      <div
        className={`border-2 border-dashed rounded-xl p-4 text-center cursor-pointer transition-all duration-200
          ${limitReached ? 'border-gray-700/30 opacity-40 cursor-not-allowed'
            : dragOver
              ? 'border-indigo-400/50 bg-indigo-500/10'
              : darkMode
                ? 'border-white/10 hover:border-white/20 hover:bg-white/[0.02]'
                : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50/50'
          }`}
        onDragOver={limitReached ? null : (e) => { e.preventDefault(); setDragOver(true) }}
        onDragLeave={() => setDragOver(false)}
        onDrop={limitReached ? null : handleDrop}
      >
        <input
          type="file"
          accept=".pdf"
          multiple
          className="hidden"
          id="pdf-upload"
          onChange={handleChange}
          disabled={uploading || limitReached}
        />
        <label htmlFor="pdf-upload" className={limitReached ? '' : 'cursor-pointer'}>
          {uploading ? (
            <div className="flex flex-col items-center gap-2">
              <div className="relative">
                <div className="animate-spin rounded-full h-6 w-6 border-2 border-indigo-500/30 border-t-indigo-500" />
              </div>
              <span className={`text-xs ${darkMode ? 'text-gray-500' : 'text-gray-400'}`}>Processing...</span>
            </div>
          ) : limitReached ? (
            <div className="flex flex-col items-center gap-2">
              <Upload className={`w-5 h-5 ${darkMode ? 'text-gray-600' : 'text-gray-300'}`} />
              <span className={`text-xs ${darkMode ? 'text-gray-600' : 'text-gray-400'}`}>Limit reached</span>
            </div>
          ) : (
            <div className="flex flex-col items-center gap-2">
              <Upload className={`w-5 h-5 ${darkMode ? 'text-gray-500' : 'text-gray-400'}`} />
              <span className={`text-xs ${darkMode ? 'text-gray-500' : 'text-gray-400'}`}>Drop PDF or click</span>
            </div>
          )}
        </label>
      </div>
      <p className={`text-xs mt-2 text-center ${darkMode ? 'text-gray-600' : 'text-gray-400'}`}>
        {docCount} / {maxDocs} docs
      </p>
    </div>
  )
}
