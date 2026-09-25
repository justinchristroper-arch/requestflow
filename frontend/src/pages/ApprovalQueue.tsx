import { useState } from 'react'
import { useAuth } from '../auth/context'
import { useResource } from '../lib/useResource'
import { LoadState, Pagination, RequestTable } from '../requests/components'
import type { RequestPage } from '../requests/types'
import PageHeader from '../components/PageHeader'
import EmptyState from '../components/EmptyState'

export default function ApprovalQueue() {
  const { user } = useAuth()
  const [offset, setOffset] = useState(0)
  const { data, loading, error, retry } = useResource<RequestPage>(`/approvals/pending?offset=${offset}&limit=20`)
  return <>
    <PageHeader eyebrow="Action required" title={user?.role === 'FINANCE' ? 'Finance approvals' : 'Manager approvals'} subtitle="Review requests waiting for your decision. Oldest submissions appear first." action={<button className="secondary-button" onClick={retry} disabled={loading}>Refresh approvals</button>} />
    <LoadState loading={loading} error={error} retry={retry} />
    {data && (data.items.length ? <><RequestTable page={data} queue /><Pagination page={data} onPage={setOffset} /></> : <EmptyState title={offset ? 'No requests on this page' : 'You’re all caught up'} description={offset ? 'The queue has changed. Return to the first page.' : 'No requests are currently waiting for your approval.'} action={offset > 0 && <button className="secondary-button" onClick={() => setOffset(0)}>First page</button>} />)}
  </>
}
