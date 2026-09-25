import type { Role } from '../auth/api'
import type { AuditAction, Category, Priority, Status, SLAStatus } from './types'

export const auditLabels: Record<AuditAction, string> = {
  REQUEST_CREATED: 'Request submitted', REQUEST_CANCELLED: 'Request cancelled', MANAGER_APPROVED: 'Manager approved', MANAGER_REJECTED: 'Manager rejected', FINANCE_APPROVAL_REQUIRED: 'Finance approval required', FINANCE_APPROVED: 'Finance approved', FINANCE_REJECTED: 'Finance rejected', PROCESSING_STARTED: 'Processing started', REQUEST_COMPLETED: 'Request completed', HISTORY_BASELINE: 'Audit tracking enabled',
}

export const categoryLabels: Record<Category, string> = { HARDWARE: 'Hardware', SOFTWARE: 'Software', ACCESS: 'Access', REPAIR_MAINTENANCE: 'Repair / Maintenance', OTHER: 'Other' }
export const priorityLabels: Record<Priority, string> = { LOW: 'Low', MEDIUM: 'Medium', HIGH: 'High' }
export const roleLabels: Record<Role, string> = { EMPLOYEE: 'Employee', MANAGER: 'Manager', FINANCE: 'Finance', PROCUREMENT: 'Procurement / IT', ADMIN: 'Admin' }
export const statusLabels: Record<Status, string> = { DRAFT: 'Draft', PENDING_MANAGER_APPROVAL: 'Pending manager approval', PENDING_FINANCE_APPROVAL: 'Pending Finance approval', APPROVED: 'Approved', PROCESSING: 'Processing', COMPLETED: 'Completed', REJECTED: 'Rejected', CANCELLED: 'Cancelled' }
export function rupiah(value: string) {
  // Preserve exact decimal digits for money. No binary floating-point conversion.
  const [whole, fraction = ''] = value.split('.')
  return `Rp${BigInt(whole || '0').toLocaleString('id-ID')}${fraction && /[1-9]/.test(fraction) ? `,${fraction.padEnd(2, '0')}` : ''}`
}
export function dateTime(value: string) {
  return new Intl.DateTimeFormat('id-ID', { dateStyle: 'medium', timeStyle: 'short', timeZone: 'Asia/Jakarta' }).format(new Date(value))
}

export const slaLabels: Record<SLAStatus, string> = {
  ON_TRACK: 'On Track', DUE_SOON: 'Due Soon', BREACHED: 'Breached',
  COMPLETED_ON_TIME: 'Completed On Time', COMPLETED_LATE: 'Completed Late', NOT_APPLICABLE: 'Not Applicable',
}
