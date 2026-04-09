import { useState, useCallback, useEffect } from 'react'
import { listDocuments, uploadDocument, deleteDocument } from '../api/documents'

export default function useDocuments() {
  const [documents, setDocuments] = useState([])
  const [selectedDocId, setSelectedDocId] = useState(null)
  const [uploading, setUploading] = useState(false)
  const [uploadMsg, setUploadMsg] = useState(null) // {type: 'success'|'error', text: '...'}

  const refresh = useCallback(async () => {
    try {
      const docs = await listDocuments()
      setDocuments(docs)
    } catch (err) {
      console.error('Failed to list documents', err)
    }
  }, [])

  useEffect(() => { refresh() }, [refresh])

  const upload = useCallback(async (file) => {
    setUploading(true)
    setUploadMsg(null)
    try {
      const result = await uploadDocument(file)
      await refresh()
      setUploadMsg({ type: 'success', text: `${file.name} uploaded (${result.chunk_count} chunks)` })
      return result
    } catch (err) {
      const detail = err.response?.data?.detail || err.message || 'Upload failed'
      setUploadMsg({ type: 'error', text: detail })
    } finally {
      setUploading(false)
    }
  }, [refresh])

  const remove = useCallback(async (docId) => {
    await deleteDocument(docId)
    if (selectedDocId === docId) setSelectedDocId(null)
    await refresh()
  }, [refresh, selectedDocId])

  return { documents, selectedDocId, setSelectedDocId, uploading, uploadMsg, upload, remove, refresh }
}
