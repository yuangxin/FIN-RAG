import api from './client'

export async function sendQuestion(question) {
  const res = await api.post('/api/chat', { question })
  return res.data
}

export function createChatWS() {
  return new WebSocket('ws://localhost:8000/api/chat/ws')
}
