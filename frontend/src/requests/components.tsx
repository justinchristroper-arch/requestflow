import { Link } from 'react-router-dom'
import { categoryLabels, dateTime, priorityLabels, rupiah, statusLabels } from './display'
import type { RequestPage, Status } from './types'
import SlaBadge from './SlaBadge'

export function StatusBadge({ status }: { status: Status }) {
  const color = status === 'APPROVED' || status === 'COMPLETED' ? 'bg-teal-50 text-teal-800' : status === 'REJECTED' ? 'bg-red-50 text-red-800' : status === 'CANCELLED' ? 'bg-slate-100 text-slate-600' : 'bg-amber-50 text-amber-900'
  return <span className={`inline-block rounded-full px-3 py-1 text-xs font-semibold ${color}`}>{statusLabels[status]}</span>
}

export function LoadState({ loading, error, retry, label = 'requests' }: { loading: boolean; error?: string; retry: () => void; label?: string }) {
  if (loading) return <div role="status" className="panel min-h-40 p-6 text-sm text-slate-500"><p>Loading {label}…</p><div aria-hidden="true" className="mt-5 space-y-3"><div className="h-3 w-2/3 rounded bg-slate-100" /><div className="h-3 w-5/6 rounded bg-slate-100" /><div className="h-3 w-1/2 rounded bg-slate-100" /></div></div>
  if (error) return <div role="alert" className="rounded-xl border border-red-200 bg-red-50 p-6"><h2 className="font-semibold text-red-900">We couldn't load {label}.</h2><p className="mt-2 text-sm text-red-800">{error}</p><button onClick={retry} className="secondary-button mt-4">Try again</button></div>
  return null
}

export function RequestTable({ page, queue = false }: { page: RequestPage; queue?: boolean }) {
  return <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white"><table className="w-full min-w-[920px] text-left text-sm">
    <caption className="sr-only">{queue ? 'Requests awaiting your decision' : 'Visible requests'}. Dates are in Jakarta time.</caption>
    <thead className="border-b border-slate-200 bg-slate-50 text-xs uppercase tracking-wide text-slate-500"><tr>
      <th className="p-4">Request</th><th className="p-4">{queue ? 'Requester' : 'Category'}</th><th className="p-4">Priority</th><th className="p-4">Status</th><th className="p-4">Estimated cost</th><th className="p-4">{queue ? 'Due date' : 'Submitted'}</th>{!queue && <th className="p-4">Due date</th>}
    </tr></thead>
    <tbody>{page.items.map((item) => <tr key={item.id} className="border-b border-slate-100 last:border-0 hover:bg-slate-50">
      <td className="max-w-xs p-4"><Link to={`/requests/${item.id}`} className="font-semibold text-teal-800 hover:underline">{item.request_number}<span className="mt-1 block break-words font-normal text-slate-700">{item.title}</span></Link><div className="mt-2 md:hidden"><SlaBadge status={item.sla_status} /></div></td>
      <td className="p-4">{queue ? item.requester.name : categoryLabels[item.category]}</td><td className="p-4">{priorityLabels[item.priority]}</td><td className="p-4"><StatusBadge status={item.status} /><div className="mt-2"><SlaBadge status={item.sla_status} /></div></td>
      <td className="whitespace-nowrap p-4 font-medium">{rupiah(item.estimated_cost)}</td><td className="p-4 text-xs text-slate-500">{dateTime(queue ? item.due_date : item.created_at)}</td>{!queue && <td className="p-4 text-xs text-slate-500">{dateTime(item.due_date)}</td>}
    </tr>)}</tbody>
  </table></div>
}

export function Pagination({ page, onPage }: { page: RequestPage; onPage: (offset: number) => void }) {
  return <div className="mt-4 flex flex-wrap items-center justify-between gap-3 text-sm text-slate-500"><p>{page.total === 0 ? '0 requests' : `${page.offset + 1}–${Math.min(page.offset + page.limit, page.total)} of ${page.total} requests`}</p><div className="flex gap-3">
    <button disabled={page.offset === 0} onClick={() => onPage(Math.max(0, page.offset - page.limit))} className="rounded-lg border px-3 py-2 disabled:opacity-40">Previous</button>
    <button disabled={page.offset + page.limit >= page.total} onClick={() => onPage(page.offset + page.limit)} className="rounded-lg border px-3 py-2 disabled:opacity-40">Next</button>
  </div></div>
}


