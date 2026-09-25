import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../auth/context'
import { useResource } from '../lib/useResource'
import { LoadState, Pagination, RequestTable } from '../requests/components'
import type { RequestPage } from '../requests/types'
import PageHeader from '../components/PageHeader'
import EmptyState from '../components/EmptyState'

export default function RequestList() {
  const { user } = useAuth()
  const [offset, setOffset] = useState(0)
  const [team, setTeam] = useState(false)
  const admin = user?.role === 'ADMIN'
  const { data, loading, error, retry } = useResource<RequestPage>(`/requests?own=${!admin && !team}&offset=${offset}&limit=20`)
  return <>
    <PageHeader eyebrow="Request management" title={admin ? 'All requests' : 'My requests'} subtitle="Track requests from submission to completion. Dates are shown in Jakarta time." action={!admin && <Link className="primary-button" to="/requests/new">Create request</Link>} />
    {user?.role === 'MANAGER' && <label className="mb-5 flex items-center gap-2 text-sm"><input type="checkbox" checked={team} onChange={(event) => { setTeam(event.target.checked); setOffset(0) }} />Include my direct reports</label>}
    <LoadState loading={loading} error={error} retry={retry} />
    {data && (data.items.length ? <><RequestTable page={data} /><Pagination page={data} onPage={setOffset} /></> : <EmptyState title={offset ? 'No requests on this page' : admin || team ? 'No requests yet' : "You haven't submitted any requests yet"} description={offset ? 'Return to the first page to see current requests.' : admin || team ? 'Submitted requests will appear here.' : 'Create your first IT or procurement request to get started.'} action={offset ? <button className="secondary-button" onClick={() => setOffset(0)}>First page</button> : !admin && <Link className="primary-button" to="/requests/new">Create request</Link>} />)}
  </>
}
