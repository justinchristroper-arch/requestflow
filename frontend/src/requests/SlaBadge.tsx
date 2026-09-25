import type { SLAStatus } from './types'

import { slaLabels } from './display'

export default function SlaBadge({ status }: { status: SLAStatus }) {
  const color = status === 'BREACHED' || status === 'COMPLETED_LATE' ? 'bg-red-50 text-red-800' : status === 'DUE_SOON' ? 'bg-amber-50 text-amber-900' : status === 'NOT_APPLICABLE' ? 'bg-slate-100 text-slate-600' : 'bg-teal-50 text-teal-800'
  return <span aria-label={`SLA: ${slaLabels[status]}`} className={`inline-block rounded-md px-2 py-1 text-xs font-semibold ${color}`}>{slaLabels[status]}</span>
}


