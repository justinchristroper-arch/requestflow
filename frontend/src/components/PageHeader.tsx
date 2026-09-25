import type { ReactNode } from 'react'

export default function PageHeader({ title, subtitle, eyebrow, action }: { title: string; subtitle?: string; eyebrow?: string; action?: ReactNode }) {
  return <header className="mb-7 flex flex-wrap items-start justify-between gap-4">
    <div className="min-w-0">{eyebrow && <p className="eyebrow">{eyebrow}</p>}<h1 className="page-title">{title}</h1>{subtitle && <p className="mt-3 max-w-2xl text-sm leading-6 text-slate-500">{subtitle}</p>}</div>
    {action && <div className="shrink-0">{action}</div>}
  </header>
}
