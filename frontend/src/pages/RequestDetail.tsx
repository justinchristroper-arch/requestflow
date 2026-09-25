import { useEffect, useRef, useState } from 'react'
import { Link, useLocation, useNavigate, useParams } from 'react-router-dom'
import { useApi, errorMessage } from '../lib/useApi'
import { useResource } from '../lib/useResource'
import { LoadState, StatusBadge } from '../requests/components'
import { categoryLabels, dateTime, priorityLabels, rupiah } from '../requests/display'
import type { RequestDetail as Detail } from '../requests/types'
import AuditTimeline from '../requests/AuditTimeline'
import SlaBadge from '../requests/SlaBadge'
import ConfirmationDialog from '../components/ConfirmationDialog'

const actionLabels: Record<string, string> = { cancel: 'Cancel request', manager_approve: 'Approve request', finance_approve: 'Approve request', manager_reject: 'Reject request', finance_reject: 'Reject request', start_processing: 'Start Processing', complete: 'Complete Request' }

export default function RequestDetail() {
  const { id } = useParams()
  return <RequestDetailContent key={id} />
}

function RequestDetailContent() {
  const { id } = useParams()
  const location = useLocation()
  const navigate = useNavigate()
  const api = useApi()
  const resource = useResource<Detail>(`/requests/${id}`)
  const [busy, setBusy] = useState(false)
  const guard = useRef(false)
  const [comment, setComment] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [pendingAction, setPendingAction] = useState<string | null>(null)
  const commentField = useRef<HTMLTextAreaElement>(null)
  const [success, setSuccess] = useState(location.state?.submitted ? 'Request submitted successfully. Your manager can now review it.' : '')
  useEffect(() => {
    if (location.state?.submitted) navigate(location.pathname, { replace: true, state: null })
  }, [location.pathname, location.state, navigate])
  function confirm(action: string) {
    if (busy) return
    setError(null)
    if (action.endsWith('reject') && !comment.trim()) {
      setError('Please enter a rejection reason.')
      commentField.current?.focus()
      return
    }
    setPendingAction(action)
  }
  async function act(action: string) {
    if (guard.current) return
    if (action.endsWith('reject') && !comment.trim()) { setError('Please enter a rejection reason.'); return }
    guard.current = true
    setBusy(true)
    setError(null)
    try {
      const cancel = action === 'cancel'
      const fulfillment = action === 'start_processing' || action === 'complete'
      const endpoint = fulfillment ? (action === 'start_processing' ? 'start-processing' : 'complete') : cancel ? 'cancel' : action.startsWith('manager') ? 'manager-approval' : 'finance-approval'
      await api<Detail>(`/requests/${id}/${endpoint}`, {
        method: cancel ? 'PATCH' : 'POST', ...(cancel ? {} : { body: JSON.stringify(fulfillment ? { note: comment.trim() || null } : { decision: action.endsWith('reject') ? 'REJECT' : 'APPROVE', comment: comment.trim() || null }) }),
      })
      setComment('')
      setSuccess(fulfillment ? action === 'complete' ? 'Request completed.' : 'Processing started. This request is now assigned to you.' : cancel ? 'Request cancelled.' : 'Your decision has been recorded.')
      resource.retry()
    } catch (reason) { setError(errorMessage(reason)); resource.retry() } finally { guard.current = false; setBusy(false); setPendingAction(null) }
  }
  const request = resource.data
  return <>
    <Link to="/" className="text-sm font-medium text-teal-700 hover:underline">← Dashboard</Link>
    <div className="mt-5"><LoadState loading={resource.loading} error={resource.error} retry={resource.retry} label="request details" /></div>
    {request && <>
      <div className="mb-7 flex flex-col items-start justify-between gap-4 sm:flex-row"><div className="w-full min-w-0 sm:flex-1"><p className="eyebrow">{request.request_number}</p><h1 className="page-title break-words">{request.title}</h1><p className="mt-3 break-words text-sm text-slate-500">Requested by {request.requester.name} · {request.requester.email}</p></div><div className="flex flex-wrap items-center gap-2"><StatusBadge status={request.status} /><SlaBadge status={request.sla_status} /></div></div>
      {success && <p role="status" className="mb-5 rounded-lg border border-teal-200 bg-teal-50 p-4 text-sm text-teal-900">{success}</p>}
      {(request.allowed_actions.length > 0 || error) && <section className="panel mb-6 border-teal-200 p-6"><h2 className="text-lg font-semibold">Available actions</h2>
        {error && <p role="alert" className="mt-4 rounded-lg bg-red-50 p-3 text-sm text-red-800">{error}</p>}
        {request.allowed_actions.some((action) => action.endsWith('approve')) && <label className="field-label mt-4 max-w-2xl">Decision comment <span className="font-normal text-slate-500">(required when rejecting)</span><textarea ref={commentField} className="field" rows={3} maxLength={2000} disabled={busy} value={comment} onChange={(event) => setComment(event.target.value)} /></label>}
        {request.allowed_actions.some((action) => action === 'start_processing' || action === 'complete') && <label className="field-label mt-4 max-w-2xl">Operational note (optional)<textarea className="field" rows={3} maxLength={2000} disabled={busy} value={comment} onChange={(event) => setComment(event.target.value)} /></label>}
        <p className="mt-3 text-xs text-slate-500">You can review your action before it is recorded.</p>
        <div className="mt-4 flex flex-wrap gap-3">{request.allowed_actions.map((action) => <button disabled={busy} key={action} onClick={() => confirm(action)} className={action.endsWith('reject') ? 'danger-button' : action === 'cancel' ? 'secondary-button' : 'primary-button'}>{busy ? 'Saving…' : actionLabels[action]}</button>)}</div>
      </section>}
      <div className="grid items-start gap-6 xl:grid-cols-[minmax(0,1fr)_360px]">
        <section className="panel min-w-0 p-6 sm:p-8"><h2 className="text-lg font-semibold text-slate-900">Request information</h2>
          <dl className="mt-6 grid gap-6 sm:grid-cols-2">{[['Category', categoryLabels[request.category]], ['Priority', priorityLabels[request.priority]], ['Estimated cost', rupiah(request.estimated_cost)], ['Submitted (Jakarta)', dateTime(request.created_at)], ['Due date (Jakarta)', dateTime(request.due_date)]].map(([label, value]) => <div key={label}><dt className="text-xs text-slate-500">{label}</dt><dd className="mt-1 text-sm font-medium text-slate-800">{value}</dd></div>)}</dl>
          <h3 className="mt-8 text-sm font-semibold">Description</h3><p className="mt-2 whitespace-pre-wrap break-words text-sm leading-7 text-slate-600">{request.description}</p>
          <h3 className="mt-6 text-sm font-semibold">Business justification</h3><p className="mt-2 whitespace-pre-wrap break-words text-sm leading-7 text-slate-600">{request.business_justification}</p>
        </section>
        <section className="panel p-6"><h2 className="text-lg font-semibold text-slate-900">Approval workflow</h2><ol className="mt-5 space-y-5">
          {(['MANAGER', 'FINANCE'] as const).map((stage, index) => {
            const approval = request.approvals.find((item) => item.approval_type === stage)
            const label = approval ? { PENDING: 'Pending', APPROVED: 'Approved', REJECTED: 'Rejected', CANCELLED: 'Cancelled' }[approval.status] : !request.finance_required ? 'Not required' : ['REJECTED', 'CANCELLED'].includes(request.status) ? 'Not reached' : 'Awaiting manager approval'
            return <li key={stage} className="border-b border-slate-100 pb-5 last:border-0 last:pb-0"><p className="text-xs font-semibold uppercase tracking-wide text-slate-500">0{index + 1} · {stage === 'MANAGER' ? 'Manager approval' : 'Finance approval'}</p><p className="mt-2 font-semibold text-slate-800"><span aria-hidden="true" className="mr-2 text-teal-700">{approval?.status === 'APPROVED' ? '✓' : approval?.status === 'REJECTED' ? '×' : approval?.status === 'PENDING' ? '○' : '—'}</span>{label}</p>
              {approval?.approver && <p className="mt-1 text-sm text-slate-500">{approval.approver.name}</p>}
              {approval?.decided_at && <p className="mt-1 text-xs text-slate-500">{dateTime(approval.decided_at)}</p>}
              {approval?.comment && <p className="mt-3 whitespace-pre-wrap break-words rounded-lg bg-slate-50 p-3 text-sm leading-6 text-slate-700">{approval.comment}</p>}
            </li>
          })}
          <li className="border-t border-slate-100 pt-5"><p className="text-xs font-semibold uppercase tracking-wide text-slate-500">03 · Procurement / IT</p><p className="mt-2 font-semibold text-slate-800">{request.status === 'COMPLETED' ? '✓ Completed' : request.status === 'PROCESSING' ? '● Processing' : request.status === 'APPROVED' ? 'Ready to process' : ['REJECTED', 'CANCELLED'].includes(request.status) ? 'Not reached' : 'Awaiting approval'}</p></li>
        </ol></section>
      </div>
      <section className="panel mt-6 p-6" aria-label="Service deadline"><div className="flex flex-wrap items-center justify-between gap-3"><h2 className="text-lg font-semibold">Service deadline</h2><SlaBadge status={request.sla_status} /></div>
        <p className="mt-3 text-sm text-slate-700">Due (Jakarta): {dateTime(request.due_date)}</p>
        <p className="mt-2 text-sm text-slate-500">{request.status === 'COMPLETED' ? 'Timeliness is based on the recorded completion time.' : request.sla_status === 'NOT_APPLICABLE' ? 'This request is excluded from SLA compliance.' : 'Due Soon means within 24 hours of the deadline. Breached means the deadline has passed.'}</p>
        <button className="mt-3 text-sm font-semibold text-teal-700 hover:underline" onClick={resource.retry}>Refresh SLA status</button>
      </section>
      <section className="panel mt-6 p-6"><h2 className="text-lg font-semibold">Fulfillment</h2>
        <dl className="mt-4 grid gap-5 sm:grid-cols-3">
          <div><dt className="text-xs text-slate-500">Assigned to</dt><dd className="mt-1 text-sm font-medium">{request.processing_owner?.name ?? 'Unassigned'}</dd></div>
          <div><dt className="text-xs text-slate-500">Started (Jakarta)</dt><dd className="mt-1 text-sm">{request.processing_started_at ? dateTime(request.processing_started_at) : '—'}</dd></div>
          <div><dt className="text-xs text-slate-500">Completed (Jakarta)</dt><dd className="mt-1 text-sm">{request.completed_at ? dateTime(request.completed_at) : '—'}</dd></div>
        </dl>
        <p className="mt-4 text-sm text-slate-500">{request.status === 'APPROVED' ? 'Ready for Procurement / IT to start processing.' : request.status === 'PROCESSING' ? 'Processing. Only the assigned operator can complete this request.' : request.status === 'COMPLETED' ? 'Fulfillment completed.' : ['REJECTED', 'CANCELLED'].includes(request.status) ? 'This request will not proceed to fulfillment.' : 'Fulfillment begins after all required approvals.'}</p>
      </section>
      <AuditTimeline requestId={request.id} />
      {pendingAction && <ConfirmationDialog title={`${actionLabels[pendingAction]}?`} description={`${request.request_number} · ${request.title}\n\n${pendingAction.endsWith('reject') || pendingAction === 'cancel' ? 'This stops the request. It cannot be reopened.' : pendingAction === 'complete' ? 'Confirm that fulfillment is finished.' : pendingAction === 'start_processing' ? 'This assigns fulfillment to you.' : 'Your decision will be recorded in the audit timeline.'}${comment.trim() ? `\n\nNote: ${comment.trim()}` : ''}`} confirmLabel={`Confirm ${pendingAction.endsWith('approve') ? 'approval' : pendingAction.endsWith('reject') ? 'rejection' : pendingAction === 'cancel' ? 'cancellation' : pendingAction === 'complete' ? 'completion' : 'processing'}`} busy={busy} destructive={pendingAction.endsWith('reject') || pendingAction === 'cancel'} onClose={() => setPendingAction(null)} onConfirm={() => act(pendingAction)} />}
    </>}
  </>
}


