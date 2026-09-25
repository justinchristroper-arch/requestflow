import { useEffect, useId, useRef } from 'react'

export default function ConfirmationDialog({ title, description, confirmLabel, busy, destructive, onConfirm, onClose }: {
  title: string; description: string; confirmLabel: string; busy: boolean; destructive?: boolean; onConfirm: () => void; onClose: () => void;
}) {
  const dialog = useRef<HTMLDialogElement>(null)
  const titleId = useId()
  const descriptionId = useId()
  useEffect(() => {
    const element = dialog.current
    const previous = document.activeElement as HTMLElement | null
    element?.showModal()
    return () => { element?.close(); previous?.focus() }
  }, [])
  return <dialog ref={dialog} aria-labelledby={titleId} aria-describedby={descriptionId} onCancel={(event) => { event.preventDefault(); if (!busy) onClose() }} className="m-auto w-[calc(100%-2rem)] max-w-md rounded-xl border border-slate-200 bg-white p-6 text-slate-800 shadow-xl backdrop:bg-slate-900/40">
    <h2 id={titleId} className="text-lg font-semibold">{title}</h2><p id={descriptionId} className="mt-3 whitespace-pre-wrap break-words text-sm leading-6 text-slate-600">{description}</p>
    <div className="mt-6 flex flex-wrap justify-end gap-3"><button autoFocus className="secondary-button" disabled={busy} onClick={onClose}>Go back</button><button className={destructive ? 'danger-button' : 'primary-button'} disabled={busy} onClick={onConfirm}>{busy ? 'Saving…' : confirmLabel}</button></div>
  </dialog>
}
