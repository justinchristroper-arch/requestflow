import { useResource } from '../lib/useResource'
import { LoadState } from './components'
import { auditLabels, dateTime, statusLabels } from './display'
import type { AuditEvent } from './types'

export default function AuditTimeline({ requestId }: { requestId: number }) {
  const { data, loading, error, retry } = useResource<AuditEvent[]>(`/requests/${requestId}/audit`)
  return <section className="panel mt-6 p-6 sm:p-8" aria-label="Audit timeline">
    <h2 className="text-lg font-semibold text-slate-900">Audit timeline</h2>
    <p className="mb-6 mt-2 text-sm text-slate-500">Workflow history, oldest first. All times are in Jakarta.</p>
    <LoadState loading={loading} error={error} retry={retry} label="audit history" />
    {data && (data.length ? <ol className="ml-2 border-l border-teal-200">{data.map((event) => <li key={event.id} className="relative pb-7 pl-6 last:pb-0">
      <span aria-hidden="true" className={`absolute -left-1.5 top-1.5 size-3 rounded-full border-2 border-white ${event.actor ? 'bg-teal-600' : 'bg-slate-400'}`} />
      <p className="text-xs text-slate-500"><time dateTime={event.created_at}>{dateTime(event.created_at)}</time></p>
      <h3 className="mt-1 font-semibold text-slate-800">{auditLabels[event.action]}</h3>
      <p className="mt-1 break-words text-sm text-slate-600">{event.actor?.name ?? 'System'}{!event.actor && <span className="ml-2 rounded bg-slate-100 px-2 py-0.5 text-xs">Automatic</span>}</p>
      {event.new_status && <p className="mt-2 text-xs text-slate-500">{event.previous_status ? `${statusLabels[event.previous_status]} → ` : ''}{statusLabels[event.new_status]}</p>}
      {event.details && <p className="mt-3 whitespace-pre-wrap break-words rounded-lg bg-slate-50 p-3 text-sm leading-6 text-slate-700">{event.details}</p>}
    </li>)}</ol> : <p className="text-sm text-slate-500">No audit events recorded.</p>)}
  </section>
}
