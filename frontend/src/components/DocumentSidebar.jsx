import { FileText, Trash2, CheckCircle, XCircle } from 'lucide-react'
import UploadArea from './UploadArea'

const MAX_DOCS = 10

export default function DocumentSidebar({ documents, selectedDocId, onSelect, onUpload, onRemove, uploading, uploadMsg, darkMode }) {
  return (
    <div className={`w-80 flex-shrink-0 flex flex-col ${darkMode ? 'glass-sidebar' : 'glass-sidebar-light'}`}>
      <div className="p-4">
        <h2 className={`text-xs font-semibold uppercase tracking-wider mb-3 ${
          darkMode ? 'text-gray-500' : 'text-gray-400'
        }`}>
          Documents <span className="text-indigo-400">{documents.length}</span>/{MAX_DOCS}
        </h2>
        <UploadArea onUpload={onUpload} uploading={uploading} docCount={documents.length} maxDocs={MAX_DOCS} darkMode={darkMode} />
        {uploadMsg && (
          <div className={`mt-2 flex items-center gap-1.5 text-xs px-3 py-2 rounded-xl ${
            uploadMsg.type === 'success'
              ? 'text-emerald-400 bg-emerald-500/10 border border-emerald-500/20'
              : 'text-red-400 bg-red-500/10 border border-red-500/20'
          }`}>
            {uploadMsg.type === 'success'
              ? <CheckCircle className="w-3.5 h-3.5 flex-shrink-0" />
              : <XCircle className="w-3.5 h-3.5 flex-shrink-0" />
            }
            <span className="truncate">{uploadMsg.text}</span>
          </div>
        )}
      </div>

      <div className="flex-1 overflow-y-auto p-4 pt-0 space-y-2">
        {documents.map((doc) => {
          const isActive = selectedDocId === doc.id
          const cardClass = darkMode
            ? isActive ? 'doc-card-active' : 'doc-card'
            : isActive ? 'doc-card-active-light' : 'doc-card-light'

          return (
            <div
              key={doc.id}
              onClick={() => onSelect(doc.id)}
              className={`p-3 rounded-xl cursor-pointer ${cardClass}`}
            >
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-2.5 min-w-0">
                  <div className={`w-7 h-7 rounded-lg flex items-center justify-center flex-shrink-0 ${
                    isActive
                      ? 'bg-indigo-500/20 text-indigo-400'
                      : darkMode ? 'bg-white/5 text-gray-500' : 'bg-gray-100 text-gray-400'
                  }`}>
                    <FileText className="w-3.5 h-3.5" />
                  </div>
                  <span className="text-sm truncate">{doc.filename}</span>
                </div>
                <button
                  onClick={(e) => { e.stopPropagation(); onRemove(doc.id) }}
                  className={`opacity-50 hover:opacity-100 transition-opacity p-1 rounded-lg ${
                    darkMode ? 'text-gray-500 hover:text-red-400 hover:bg-red-500/10' : 'text-gray-400 hover:text-red-500 hover:bg-red-50'
                  }`}
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </div>
              <div className={`mt-1.5 flex gap-2 text-xs ${darkMode ? 'text-gray-500' : 'text-gray-400'}`}>
                {doc.company_name && <span>{doc.company_name}</span>}
                {doc.year && <span>{doc.year}</span>}
                <span>{doc.chunk_count} chunks</span>
              </div>
            </div>
          )
        })}

        {documents.length === 0 && (
          <p className={`text-xs text-center mt-4 ${darkMode ? 'text-gray-600' : 'text-gray-400'}`}>
            No documents yet
          </p>
        )}
      </div>
    </div>
  )
}
