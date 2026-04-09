import api from './client'

export async function uploadDocument(file) {
  const formData = new FormData()
  formData.append('file', file)
  const res = await api.post('/api/documents/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return res.data
}

export async function listDocuments() {
  const res = await api.get('/api/documents')
  return res.data
}

export async function deleteDocument(docId) {
  const res = await api.delete(`/api/documents/${docId}`)
  return res.data
}

export async function getFinancialData(docId) {
  const res = await api.get(`/api/financial-data/${docId}`)
  return res.data
}
