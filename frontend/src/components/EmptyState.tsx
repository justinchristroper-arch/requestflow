import type { ReactNode } from 'react'

export default function EmptyState({ title, description, action }: { title: string; description: string; action?: ReactNode }) {
  return <section className="panel px-6 py-12 text-center"><h2 className="font-semibold text-slate-900">{title}</h2><p className="mx-auto mt-2 max-w-md text-sm leading-6 text-slate-500">{description}</p>{action && <div className="mt-5">{action}</div>}</section>
}
