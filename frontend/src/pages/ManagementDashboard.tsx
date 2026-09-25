import { Bar, BarChart, CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { useResource } from '../lib/useResource'
import { categoryLabels, dateTime, priorityLabels, statusLabels } from '../requests/display'
import { slaLabels } from '../requests/display'
import PageHeader from '../components/PageHeader'
import EmptyState from '../components/EmptyState'
import { LoadState } from '../requests/components'

type Bucket = { key: string; count: number }
interface Analytics {
  as_of: string; timezone: string;
  kpis: { total_requests: number; pending_approval: number; processing: number; completed: number; rejected: number; completed_on_time: number; sla_compliance_percent: number | null; average_resolution_hours: number | null };
  by_category: Bucket[]; by_priority: Bucket[]; by_status: Bucket[]; by_sla: Bucket[]; monthly_trend: Bucket[];
}
const labels: Record<string, string> = { ...categoryLabels, ...priorityLabels, ...statusLabels, ...slaLabels }

function Chart({ title, data, trend = false }: { title: string; data: Bucket[]; trend?: boolean }) {
  const rows = data.map((item) => ({ ...item, name: labels[item.key] ?? item.key }))
  const total = rows.reduce((sum, item) => sum + item.count, 0)
  return <section className="panel min-w-0 p-5 sm:p-6" aria-label={title}>
    <h2 className="text-base font-semibold text-slate-900">{title}</h2>
    {total === 0 ? <p className="py-12 text-sm text-slate-500">No requests in this period.</p> : <div className="mt-5" style={{ height: trend ? 250 : Math.max(210, rows.length * 42), minWidth: 0 }}>
      <ResponsiveContainer width="100%" height="100%" minWidth={0}>
        {trend ? <LineChart data={rows} margin={{ top: 10, right: 18, bottom: 5, left: -22 }} accessibilityLayer>
          <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" /><XAxis dataKey="name" tick={{ fontSize: 11 }} tickFormatter={(value: string) => new Intl.DateTimeFormat('en', { month: 'short', year: '2-digit', timeZone: 'UTC' }).format(new Date(`${value}-01T00:00:00Z`))} /><YAxis allowDecimals={false} tick={{ fontSize: 11 }} /><Tooltip /><Line type="linear" dataKey="count" name="Requests" stroke="#0f766e" strokeWidth={2} dot={{ r: 4 }} isAnimationActive={false} />
        </LineChart> : <BarChart data={rows} layout="vertical" margin={{ top: 0, right: 18, bottom: 0, left: 0 }} accessibilityLayer>
          <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#e2e8f0" /><XAxis type="number" allowDecimals={false} tick={{ fontSize: 11 }} /><YAxis type="category" dataKey="name" width={130} tick={{ fontSize: 11 }} interval={0} /><Tooltip /><Bar dataKey="count" name="Requests" fill="#0f766e" radius={[0, 3, 3, 0]} maxBarSize={20} isAnimationActive={false} />
        </BarChart>}
      </ResponsiveContainer>
    </div>}
    <details className="mt-3 text-xs text-slate-500"><summary className="cursor-pointer font-medium text-teal-700">View exact counts</summary><dl className="mt-3 space-y-2">{rows.map((row) => <div key={row.key} className="flex justify-between gap-3"><dt>{row.name}</dt><dd className="font-semibold text-slate-800">{row.count}</dd></div>)}</dl></details>
  </section>
}

export default function ManagementDashboard() {
  const { data, loading, error, retry } = useResource<Analytics>('/analytics/summary')
  return <>
    <PageHeader eyebrow="Management overview" title="Operational performance" subtitle="Workload, completion, and service timeliness across all requests." action={<button className="secondary-button" disabled={loading} onClick={retry}>Refresh dashboard</button>} />
    <LoadState loading={loading} error={error} retry={retry} label="analytics" />
    {data && <>
      <p className="mt-3 text-xs leading-6 text-slate-500">Snapshot: {dateTime(data.as_of)} (Jakarta). All-time metrics; trend covers the latest six months. Includes labeled synthetic demo data.</p>
      {data.kpis.total_requests === 0 && <div className="mt-6"><EmptyState title="No analytics data available yet" description="Metrics will appear as requests enter the workflow." /></div>}
      <section aria-label="Key performance indicators" className="mt-6 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {[
          ['Total Requests', data.kpis.total_requests.toLocaleString(), 'All requests, including rejected and cancelled'],
          ['Pending Approval', data.kpis.pending_approval.toLocaleString(), 'Awaiting Manager or Finance'],
          ['Processing', data.kpis.processing.toLocaleString(), 'Currently being fulfilled'],
          ['Completed', data.kpis.completed.toLocaleString(), 'Fulfillment finished'],
          ['Rejected', data.kpis.rejected.toLocaleString(), 'Declined during approval'],
          ['SLA Compliance', data.kpis.sla_compliance_percent === null ? '—' : `${data.kpis.sla_compliance_percent.toFixed(1)}%`, data.kpis.completed ? `${data.kpis.completed_on_time} on time / ${data.kpis.completed} completed` : 'No completed requests yet'],
          ['Average Resolution', data.kpis.average_resolution_hours === null ? '—' : `${data.kpis.average_resolution_hours.toFixed(1)} h`, 'Submission to completion; completed only'],
        ].map(([label, value, description]) => <article key={label} aria-label={label} className="panel p-5"><h2 className="text-sm font-medium text-slate-500">{label}</h2><p className="mt-3 text-3xl font-semibold tracking-tight text-slate-900">{value}</p><p className="mt-3 text-xs leading-5 text-slate-500">{description}</p></article>)}
      </section>
      <div className="mt-6"><Chart title="Monthly Request Trend" data={data.monthly_trend} trend /></div>
      <div className="mt-6 grid items-start gap-6 xl:grid-cols-2"><Chart title="Requests by Category" data={data.by_category} /><Chart title="Requests by Priority" data={data.by_priority} /><Chart title="SLA Status Breakdown" data={data.by_sla} /><Chart title="Requests by Status" data={data.by_status} /></div>
      <section className="mt-6 rounded-xl border border-slate-200 bg-white p-6 text-sm leading-6 text-slate-500"><h2 className="font-semibold text-slate-800">Reading these metrics</h2><p className="mt-2">SLA compliance = completed on time ÷ all completed requests × 100. Rejected, cancelled, draft, and active requests are excluded from this denominator. No completed requests means no percentage yet.</p><p className="mt-2">Active requests become Due Soon in their final 24 hours, including the exact deadline, and Breached after it. Completion at the deadline counts as on time. These figures are operational indicators, not evidence of measured business improvement.</p></section>
    </>}
  </>
}

