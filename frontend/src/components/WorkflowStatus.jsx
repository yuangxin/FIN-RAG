import { Check, Loader2 } from 'lucide-react'

const STEPS = [
  { key: 'query_rewriter', label: 'Rewrite' },
  { key: 'metadata_extractor', label: 'Extract' },
  { key: 'retriever', label: 'Retrieve' },
  { key: 'answer_generator', label: 'Generate' },
]

export default function WorkflowStatus({ activeSteps, completedSteps, stepLabels, darkMode }) {
  const visible = activeSteps.length > 0 || completedSteps.length > 0
  if (!visible) return null

  return (
    <div className={`flex items-center gap-1.5 px-4 py-2 rounded-xl ${
      darkMode ? 'bg-white/[0.03] border border-white/5' : 'bg-gray-100/50 border border-gray-200/50'
    }`}>
      {STEPS.map((step, i) => {
        const isActive = activeSteps.includes(step.key)
        const isCompleted = completedSteps.includes(step.key)

        let pillClass = darkMode ? 'step-pill' : 'bg-gray-100 border border-gray-200'
        if (isCompleted) pillClass = 'step-done'
        else if (isActive) pillClass = 'step-active'

        return (
          <div key={step.key} className="flex items-center gap-1">
            {i > 0 && (
              <span className={`mx-0.5 ${darkMode ? 'text-gray-700' : 'text-gray-300'}`}>→</span>
            )}
            <div className={`flex items-center gap-1 px-2.5 py-1 rounded-lg text-xs ${
              isCompleted
                ? 'text-emerald-400'
                : isActive
                  ? 'text-indigo-400'
                  : darkMode ? 'text-gray-600' : 'text-gray-400'
            } ${pillClass}`}>
              {isCompleted && <Check className="w-3 h-3" />}
              {isActive && <Loader2 className="w-3 h-3 animate-spin" />}
              {step.label}
            </div>
          </div>
        )
      })}
    </div>
  )
}
