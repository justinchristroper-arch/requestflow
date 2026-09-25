import { Link } from 'react-router-dom'
import { useAuth } from '../auth/context'
import PageHeader from '../components/PageHeader'

export default function Overview() {
  const { user } = useAuth()
  const creator = user?.role === 'EMPLOYEE' || user?.role === 'MANAGER'
  const approver = user?.role === 'MANAGER' || user?.role === 'FINANCE'
  const tasks = [
    ...(creator ? [{ to: '/requests/new', title: 'Create a request', detail: 'Explain the item, access, or service you need.' }, { to: '/requests', title: 'Track your requests', detail: 'See decisions, deadlines, and fulfillment history.' }] : []),
    ...(approver ? [{ to: '/approvals', title: 'Review approvals', detail: 'Review the business need and record your decision.' }] : []),
    ...(user?.role === 'PROCUREMENT' ? [{ to: '/procurement', title: 'Open Procurement Queue', detail: 'Prioritize urgent requests and manage fulfillment.' }] : []),
  ]
  return <>
    <PageHeader eyebrow="Your workspace" title={`Welcome, ${user?.name.split(' ')[0] ?? 'there'}`} subtitle="Keep IT and procurement requests moving, with clear responsibilities and a complete history." />
    <section aria-label="Workspace actions" className="grid gap-5 md:grid-cols-2 xl:grid-cols-3">{tasks.map((task) => <Link key={task.to} to={task.to} className="panel group p-6 transition-colors hover:border-teal-400"><h2 className="font-semibold text-teal-800">{task.title} <span aria-hidden="true">→</span></h2><p className="mt-3 text-sm leading-6 text-slate-500">{task.detail}</p></Link>)}</section>
    <section className="mt-10 border-t border-slate-200 pt-7"><h2 className="text-lg font-semibold text-slate-900">From request to resolution</h2><ol className="mt-6 grid gap-5 sm:grid-cols-4">{['Submit request', 'Manager review', 'Finance if required', 'Fulfill & complete'].map((step, index) => <li key={step}><span className="text-xs font-bold text-teal-700">0{index + 1}</span><p className="mt-2 text-sm font-medium">{step}</p></li>)}</ol><p className="mt-6 text-sm leading-6 text-slate-500">Open a request to view its current status, service deadline, and audit timeline.</p></section>
  </>
}
