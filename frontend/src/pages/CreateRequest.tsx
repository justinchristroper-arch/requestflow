import { useRef, useState } from 'react'
import type { SubmitEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { errorMessage, useApi } from '../lib/useApi'
import { categoryLabels, priorityLabels, rupiah } from '../requests/display'
import type { Category, Priority, RequestDetail } from '../requests/types'
import PageHeader from '../components/PageHeader'

type Field = 'title' | 'description' | 'business_justification' | 'estimated_cost'
const textFields = [
  { name: 'title' as const, label: 'Title', max: 160, rows: 0, placeholder: 'e.g. Monitor for the service desk' },
  { name: 'description' as const, label: 'Description', max: 10000, rows: 4, placeholder: 'Describe the item, access, or service you need.' },
  { name: 'business_justification' as const, label: 'Business justification', max: 5000, rows: 3, placeholder: 'Explain how this supports your work.' },
]

export default function CreateRequest() {
  const api = useApi()
  const navigate = useNavigate()
  const guard = useRef(false)
  const formRef = useRef<HTMLFormElement>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [errors, setErrors] = useState<Partial<Record<Field, string>>>({})
  const [form, setForm] = useState({ category: 'HARDWARE' as Category, title: '', description: '', business_justification: '', estimated_cost: '', priority: 'MEDIUM' as Priority })
  function update(field: keyof typeof form, value: string) {
    setForm((previous) => ({ ...previous, [field]: value }))
    setErrors((previous) => ({ ...previous, [field]: undefined }))
  }
  const moneyValid = /^\d{1,13}(\.\d{1,2})?$/.test(form.estimated_cost)
  async function submit(event: SubmitEvent<HTMLFormElement>) {
    event.preventDefault()
    if (guard.current) return
    const next: Partial<Record<Field, string>> = {}
    for (const field of textFields) if (!form[field.name].trim()) next[field.name] = `${field.label} is required.`
    if (!moneyValid) next.estimated_cost = 'Enter a non-negative amount, up to 13 whole digits and 2 decimal places.'
    setErrors(next)
    if (Object.keys(next).length) {
      formRef.current?.querySelector<HTMLElement>(`[name="${Object.keys(next)[0]}"]`)?.focus()
      return
    }
    guard.current = true
    setBusy(true)
    setError(null)
    try {
      const request = await api<RequestDetail>('/requests', { method: 'POST', body: JSON.stringify(form) })
      navigate(`/requests/${request.id}`, { replace: true, state: { submitted: true } })
    } catch (reason) { setError(errorMessage(reason)) } finally { guard.current = false; setBusy(false) }
  }
  return <div className="max-w-3xl">
    <PageHeader eyebrow="Request management" title="Create request" subtitle="Submit an internal IT or procurement request for your manager to review." />
    <form ref={formRef} noValidate className="panel space-y-6 p-6 sm:p-8" onSubmit={submit} aria-busy={busy}>
      <p className="text-xs text-slate-500">All fields are required. Enter 0 for requests with no cost.</p>
      <fieldset disabled={busy} className="space-y-6"><legend className="mb-5 text-base font-semibold text-slate-900">Request information</legend>
        <div className="grid gap-5 sm:grid-cols-2"><div><label htmlFor="category" className="field-label">Category</label><select id="category" className="field" value={form.category} onChange={(event) => update('category', event.target.value)}>{Object.entries(categoryLabels).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></div>
          <div><label htmlFor="priority" className="field-label">Priority</label><select id="priority" className="field" value={form.priority} onChange={(event) => update('priority', event.target.value)}>{Object.entries(priorityLabels).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></div></div>
        {textFields.map((field) => <div key={field.name}><label htmlFor={field.name} className="field-label">{field.label}</label>
          {field.rows ? <textarea id={field.name} name={field.name} className="field" rows={field.rows} required maxLength={field.max} value={form[field.name]} onChange={(event) => update(field.name, event.target.value)} placeholder={field.placeholder} aria-invalid={Boolean(errors[field.name])} aria-describedby={errors[field.name] ? `${field.name}-error` : undefined} /> : <input id={field.name} name={field.name} className="field" required maxLength={field.max} value={form[field.name]} onChange={(event) => update(field.name, event.target.value)} placeholder={field.placeholder} aria-invalid={Boolean(errors[field.name])} aria-describedby={errors[field.name] ? `${field.name}-error` : undefined} />}
          {errors[field.name] && <p id={`${field.name}-error`} role="alert" className="mt-2 text-xs text-red-700">{errors[field.name]}</p>}
        </div>)}
        <div className="border-t border-slate-100 pt-6"><label htmlFor="estimated_cost" className="field-label">Estimated cost (IDR)</label><input id="estimated_cost" name="estimated_cost" className="field max-w-sm" inputMode="decimal" required maxLength={16} value={form.estimated_cost} onChange={(event) => update('estimated_cost', event.target.value)} placeholder="2000000" aria-invalid={Boolean(errors.estimated_cost)} aria-describedby="cost-help cost-error" />
          <p id="cost-help" className="mt-2 text-xs leading-5 text-slate-500">{moneyValid ? rupiah(form.estimated_cost) : 'Use digits without thousands separators; use a dot for decimals.'}</p>
          <p id="cost-error" role={errors.estimated_cost ? 'alert' : undefined} className="mt-1 text-xs text-red-700">{errors.estimated_cost}</p>
        </div>
      </fieldset>
      {error && <p role="alert" className="rounded-lg bg-red-50 p-4 text-sm text-red-800">{error}</p>}
      <p className="text-xs leading-5 text-slate-500">Your manager reviews the request first. The system calculates its deadline and any required Finance approval.</p>
      <div className="flex flex-wrap items-center gap-4 border-t border-slate-100 pt-6"><button className="primary-button" disabled={busy} type="submit">{busy ? 'Submitting…' : 'Submit request'}</button><Link to="/requests" className="text-sm font-medium text-slate-600 hover:underline">Back to requests</Link></div>
    </form>
  </div>
}
