export type Category = 'HARDWARE' | 'SOFTWARE' | 'ACCESS' | 'REPAIR_MAINTENANCE' | 'OTHER'
export type Priority = 'LOW' | 'MEDIUM' | 'HIGH'
export type SLAStatus = 'ON_TRACK' | 'DUE_SOON' | 'BREACHED' | 'COMPLETED_ON_TIME' | 'COMPLETED_LATE' | 'NOT_APPLICABLE'
export type Status = 'DRAFT' | 'PENDING_MANAGER_APPROVAL' | 'PENDING_FINANCE_APPROVAL' | 'APPROVED' | 'PROCESSING' | 'COMPLETED' | 'REJECTED' | 'CANCELLED'
export interface Person { id: number; name: string; email: string }
export interface RequestSummary {
  sla_status: SLAStatus; completed_at: string | null;
  id: number; request_number: string; title: string; category: Category; priority: Priority;
  status: Status; estimated_cost: string; requester: Person;
  created_at: string; updated_at: string; due_date: string;
}
export interface Approval {
  id: number; approval_type: 'MANAGER' | 'FINANCE'; status: 'PENDING' | 'APPROVED' | 'REJECTED' | 'CANCELLED';
  approver: Person | null; comment: string | null; created_at: string; decided_at: string | null;
}
export interface RequestDetail extends RequestSummary {
  processing_owner: Person | null; processing_started_at: string | null; completed_at: string | null;
  description: string; business_justification: string; finance_required: boolean;
  approvals: Approval[]; allowed_actions: string[];
}
export type AuditAction = 'REQUEST_CREATED' | 'REQUEST_CANCELLED' | 'MANAGER_APPROVED' | 'MANAGER_REJECTED' | 'FINANCE_APPROVAL_REQUIRED' | 'FINANCE_APPROVED' | 'FINANCE_REJECTED' | 'PROCESSING_STARTED' | 'REQUEST_COMPLETED' | 'HISTORY_BASELINE'
export interface AuditEvent { id: number; actor: Person | null; action: AuditAction; previous_status: Status | null; new_status: Status | null; details: string | null; created_at: string }
export interface RequestPage { items: RequestSummary[]; total: number; offset: number; limit: number }
