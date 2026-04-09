import ReactMarkdown from 'react-markdown'
import { BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'

export default function ChatMessage({ message, darkMode }) {
  const isUser = message.role === 'user'

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}>
      <div className={`max-w-[80%] ${isUser ? 'rounded-2xl rounded-tr-md' : 'rounded-2xl rounded-tl-md'} px-4 py-3 ${
        isUser
          ? 'chat-bubble-user text-white'
          : darkMode ? 'chat-bubble-bot' : 'chat-bubble-bot-light'
      }`}>
        {isUser ? (
          <p className="text-sm whitespace-pre-wrap">{message.content}</p>
        ) : (
          <div className={`text-sm prose prose-sm max-w-none ${darkMode ? 'dark:prose-invert' : ''}`}>
            <ReactMarkdown>{message.content}</ReactMarkdown>
          </div>
        )}

        {!isUser && message.chart && (
          <div className={`mt-3 p-3 rounded-xl ${darkMode ? 'bg-black/20' : 'bg-gray-50/50'}`}>
            <p className={`text-xs font-medium mb-2 ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>
              {message.chart.title}
            </p>
            <ResponsiveContainer width="100%" height={220}>
              {message.chart.chart_type === 'line' ? (
                <LineChart data={message.chart.data}>
                  <CartesianGrid strokeDasharray="3 3" stroke={darkMode ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.06)'} />
                  <XAxis dataKey={message.chart.x_key} tick={{ fontSize: 12, fill: darkMode ? '#9ca3af' : '#6b7280' }} />
                  <YAxis tick={{ fontSize: 12, fill: darkMode ? '#9ca3af' : '#6b7280' }} />
                  <Tooltip
                    contentStyle={darkMode ? { background: 'rgba(15,15,35,0.9)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '12px' } : { borderRadius: '12px' }}
                  />
                  <Legend />
                  {message.chart.series.map(s => (
                    <Line key={s.key} type="monotone" dataKey={s.key}
                          name={s.name} stroke={s.color} strokeWidth={2} dot={{ r: 4 }} />
                  ))}
                </LineChart>
              ) : (
                <BarChart data={message.chart.data}>
                  <CartesianGrid strokeDasharray="3 3" stroke={darkMode ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.06)'} />
                  <XAxis dataKey={message.chart.x_key} tick={{ fontSize: 12, fill: darkMode ? '#9ca3af' : '#6b7280' }} />
                  <YAxis tick={{ fontSize: 12, fill: darkMode ? '#9ca3af' : '#6b7280' }} />
                  <Tooltip
                    contentStyle={darkMode ? { background: 'rgba(15,15,35,0.9)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '12px' } : { borderRadius: '12px' }}
                  />
                  <Legend />
                  {message.chart.series.map(s => (
                    <Bar key={s.key} dataKey={s.key}
                         name={s.name} fill={s.color} radius={[6, 6, 0, 0]} />
                  ))}
                </BarChart>
              )}
            </ResponsiveContainer>
          </div>
        )}

        {!isUser && message.citations?.length > 0 && (
          <div className={`mt-2 pt-2 ${darkMode ? 'border-white/10' : 'border-black/5'} border-t`}>
            <CitationList citations={message.citations} darkMode={darkMode} />
          </div>
        )}
      </div>
    </div>
  )
}

function CitationList({ citations, darkMode }) {
  return (
    <details className={`text-xs ${darkMode ? 'text-gray-500' : 'text-gray-400'}`}>
      <summary className={`cursor-pointer hover:text-indigo-400 transition-colors`}>
        Sources ({citations.length})
      </summary>
      <div className="mt-1.5 space-y-1">
        {citations.map((cite, i) => (
          <div key={i} className="flex gap-2">
            <span className="font-medium text-indigo-400/80">p.{cite.page_no}</span>
            <span className="truncate">{cite.section}</span>
          </div>
        ))}
      </div>
    </details>
  )
}
