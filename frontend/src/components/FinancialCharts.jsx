import { useState, useEffect } from 'react'
import { BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { getFinancialData } from '../api/documents'
import { BarChart3 } from 'lucide-react'

export default function FinancialCharts({ docId, documents, darkMode }) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!docId) return
    setLoading(true)
    setError('')
    getFinancialData(docId)
      .then(setData)
      .catch(err => setError(err.response?.data?.detail || 'Failed to load financial data'))
      .finally(() => setLoading(false))
  }, [docId])

  if (!docId) {
    return (
      <div className={`flex items-center justify-center h-full text-sm ${darkMode ? 'text-gray-600' : 'text-gray-400'}`}>
        Select a document to view charts
      </div>
    )
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="animate-spin rounded-full h-6 w-6 border-2 border-indigo-500/30 border-t-indigo-500" />
      </div>
    )
  }

  if (error) {
    return <div className="p-4 text-red-400 text-sm">{error}</div>
  }

  if (!data?.data_points?.length) {
    return (
      <div className={`flex items-center justify-center h-full text-sm ${darkMode ? 'text-gray-600' : 'text-gray-400'}`}>
        No financial data could be extracted
      </div>
    )
  }

  const chartData = data.data_points.map(dp => ({
    year: dp.year,
    revenue: dp.revenue_millions,
    netIncome: dp.net_income_millions,
    operatingIncome: dp.operating_income_millions,
    eps: dp.eps,
    grossMargin: dp.gross_margin_pct,
  }))

  const hasRevenueData = chartData.some(d => d.revenue != null)
  const hasMarginData = chartData.some(d => d.grossMargin != null)

  const chartCardClass = darkMode
    ? 'bg-white/[0.04] border border-white/[0.06] rounded-xl'
    : 'bg-white/60 border border-gray-200/50 rounded-xl'

  const gridStroke = darkMode ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.06)'
  const tickFill = darkMode ? '#6b7280' : '#9ca3af'
  const tooltipStyle = darkMode
    ? { background: 'rgba(15,15,35,0.9)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '12px' }
    : { borderRadius: '12px' }

  return (
    <div className="p-4 space-y-4">
      <h3 className={`text-xs font-semibold uppercase tracking-wider flex items-center gap-2 ${
        darkMode ? 'text-gray-500' : 'text-gray-400'
      }`}>
        <BarChart3 className="w-4 h-4" />
        {data.company_name || 'Financial'} Data
      </h3>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {hasRevenueData && (
          <div className={`${chartCardClass} p-4`}>
            <h4 className={`text-xs font-medium mb-2 ${darkMode ? 'text-gray-500' : 'text-gray-400'}`}>
              Revenue & Income (Millions USD)
            </h4>
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke={gridStroke} />
                <XAxis dataKey="year" tick={{ fontSize: 12, fill: tickFill }} />
                <YAxis tick={{ fontSize: 12, fill: tickFill }} />
                <Tooltip formatter={(v) => v != null ? `$${v.toLocaleString()}M` : 'N/A'} contentStyle={tooltipStyle} />
                <Legend />
                <Bar dataKey="revenue" fill="#667eea" name="Revenue" radius={[6, 6, 0, 0]} />
                <Bar dataKey="netIncome" fill="#10b981" name="Net Income" radius={[6, 6, 0, 0]} />
                <Bar dataKey="operatingIncome" fill="#f59e0b" name="Operating Income" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}

        {hasMarginData && (
          <div className={`${chartCardClass} p-4`}>
            <h4 className={`text-xs font-medium mb-2 ${darkMode ? 'text-gray-500' : 'text-gray-400'}`}>
              Gross Margin (%)
            </h4>
            <ResponsiveContainer width="100%" height={200}>
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke={gridStroke} />
                <XAxis dataKey="year" tick={{ fontSize: 12, fill: tickFill }} />
                <YAxis tick={{ fontSize: 12, fill: tickFill }} />
                <Tooltip formatter={(v) => v != null ? `${v}%` : 'N/A'} contentStyle={tooltipStyle} />
                <Line type="monotone" dataKey="grossMargin" stroke="#8B5CF6" name="Gross Margin" strokeWidth={2} dot={{ r: 4 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}

        {chartData.some(d => d.eps != null) && (
          <div className={`${chartCardClass} p-4`}>
            <h4 className={`text-xs font-medium mb-2 ${darkMode ? 'text-gray-500' : 'text-gray-400'}`}>
              Earnings Per Share (USD)
            </h4>
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke={gridStroke} />
                <XAxis dataKey="year" tick={{ fontSize: 12, fill: tickFill }} />
                <YAxis tick={{ fontSize: 12, fill: tickFill }} />
                <Tooltip formatter={(v) => v != null ? `$${v}` : 'N/A'} contentStyle={tooltipStyle} />
                <Bar dataKey="eps" fill="#ec4899" name="EPS" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>
    </div>
  )
}
