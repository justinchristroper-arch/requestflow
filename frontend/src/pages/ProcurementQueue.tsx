import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useResource } from '../lib/useResource'
import { LoadState, Pagination, StatusBadge } from '../requests/components'
import { categoryLabels, dateTime, priorityLabels, rupiah } from '../requests/display'
import type { RequestPage } from '../requests/types'
import SlaBadge from '../requests/SlaBadge'
import PageHeader from '../components/PageHeader'
import EmptyState from '../components/EmptyState'

export default function ProcurementQueue() {
  const [status, setStatus] = useState('APPROVED')
  const [offset, setOffset] = useState(0)
  const { data, loading, error, retry } = useResource<RequestPage>(`/procurement/queue?status=${status}&offset=${offset}&limit=20`)
  return <>
    <PageHeader eyebrow="Procurement / IT" title="Procurement queue" subtitle="Fulfill approved requests. Breached and Due Soon items appear first, then priority and deadline." action={<button className="secondary-button" disabled={loading} onClick={retry}>Refresh queue</button>} />
    <div className="mb-6 flex flex-wrap gap-3" aria-label="Queue filters">{[['APPROVED', 'Ready to Process'], ['PROCESSING', 'In Progress']].map(([value, label]) => <button key={value} aria-pressed={status === value} className={status === value ? 'primary-button' : 'secondary-button'} onClick={() => { setStatus(value); setOffset(0) }}>{label}</button>)}</div>
    <LoadState loading={loading} error={error} retry={retry} />
    {data && (data.items.length ? <><div className="overflow-x-auto rounded-xl border border-slate-200 bg-white"><table className="w-full min-w-[940px] text-left text-sm">
      <caption className="sr-only">Fulfillment requests. Dates are in Jakarta time.</caption>
      <thead className="border-b bg-slate-50 text-xs uppercase tracking-wide text-slate-500"><tr>{['Request', 'Requester', 'Category', 'Priority', 'Cost', 'Due date', 'Status'].map((label) => <th key={label} className="p-4">{label}</th>)}</tr></thead>
      <tbody>{data.items.map((item) => <tr key={item.id} className="border-b border-slate-100 last:border-0 hover:bg-slate-50">
        <td className="max-w-xs p-4"><Link to={`/requests/${item.id}`} className="font-semibold text-teal-800 hover:underline">{item.request_number}<span className="mt-1 block break-words font-normal text-slate-700">{item.title}</span></Link><div className="mt-2 md:hidden"><SlaBadge status={item.sla_status} /></div></td>
        <td className="p-4">{item.requester.name}</td><td className="p-4">{categoryLabels[item.category]}</td><td className="p-4">{priorityLabels[item.priority]}</td><td className="whitespace-nowrap p-4">{rupiah(item.estimated_cost)}</td><td className="p-4 text-xs text-slate-500">{dateTime(item.due_date)}</td><td className="p-4"><StatusBadge status={item.status} /><div className="mt-2"><SlaBadge status={item.sla_status} /></div></td>
      </tr>)}</tbody>
    </table></div><Pagination page={data} onPage={setOffset} /></> : <EmptyState title={offset ? 'No requests on this page' : status === 'APPROVED' ? 'No requests ready to process' : 'No requests in progress'} description={offset ? 'The queue has changed. Return to the first page.' : status === 'APPROVED' ? 'Approved requests will appear here.' : 'Requests appear here when processing starts.'} action={offset > 0 && <button className="secondary-button" onClick={() => setOffset(0)}>First page</button>} />)}
  </>
}

