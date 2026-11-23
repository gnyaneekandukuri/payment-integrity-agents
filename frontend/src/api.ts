export type QueueItem = {
  id: string; patient_name: string; age: number; sex: string; source: string; source_detail: string;
  status: string; assigned_to: string | null; due_date: string | null; claim_id: string; billed_drg: string;
  drg_title: string; admit_date: string; discharge_date: string; los: number; paid_amount: number;
  hospital: string; has_records: number; draft_conclusion: string | null;
  review_origin: string | null; review_reason: string | null;
}

export type Evidence = {
  ref: number; criterion: string; system: string | null; value: string; unit: string | null;
  observed_at: string | null; page: number; quote: string; stance: 'supports' | 'contradicts' | 'context';
}
export type Gap = { kind: 'missing' | 'conflicting' | 'coding_question'; item: string; why_it_matters: string }
export type Sofa = { system: string; baseline: number | null; worst: number | null; change: number | null; status: string; detail: string }
export type Draft = { conclusion: string; rationale: string; evidence_ids: number[]; validator_result: Record<string, unknown>;
  sections: { summary: string; documented: string; uncertain: string; would_resolve: string } | null }
export type Run = { id: string; status: string; model: string | null; mode: string; steps: number; input_tokens: number;
  output_tokens: number; started_at: string; finished_at: string | null; error: string | null }

export type CaseDetail = {
  case: QueueItem & { principal_dx: string; secondary_dx: { code: string; poa: string; desc: string }[]; icu_days: number;
    transfer_in: number; discharge_status: string; hospital_id: string;
    review_concern: string | null; review_question: string | null; review_not_yours: string | null; review_context: string | null };
  contract: { sepsis_criteria: string; summary: string };
  chart: { id: string; page_count: number } | null;
  pages: { page: number; section: string; chars: number }[];
  review: { run: Run; evidence: Evidence[]; gaps: Gap[]; sofa: Sofa[]; draft: Draft | null } | null;
  actions: { actor: string; action: string; before: string | null; after: string | null; reason: string | null; at: string }[];
  has_saved_run: boolean;
  records_request: RecordsRequest | null;
  has_saved_request: boolean;
}

export type RecordsRequest = {
  id: number; case_id: string; mode: string; status: 'draft' | 'approved';
  items: { request: string; reason: string; pages: number[] }[]; letter: string;
  created_at: string; approved_by: string | null; approved_at: string | null;
}

export type Step = { n: number; tool: string; label: string; detail: string; accepted: boolean; reason: string }
export type Progress = { run: Partial<Run> & { id: string; status: string }; steps: Step[] }

async function j<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let msg = res.statusText
    try { msg = (await res.json()).detail ?? msg } catch { /* ignore */ }
    throw new Error(msg)
  }
  return res.json() as Promise<T>
}

export const api = {
  queue: () => fetch('/api/queue').then(r => j<QueueItem[]>(r)),
  caseDetail: (id: string) => fetch(`/api/cases/${id}`).then(r => j<CaseDetail>(r)),
  page: (id: string, page: number) => fetch(`/api/cases/${id}/pages/${page}`).then(r => j<{ page: number; section: string; text: string }>(r)),
  upload: (id: string, file: File) => {
    const fd = new FormData()
    fd.append('file', file)
    return fetch(`/api/cases/${id}/records`, { method: 'POST', body: fd })
      .then(r => j<{ filename: string; pages: { page: number; section: string; chars: number; needs_ocr: boolean }[]; needs_ocr: number[] }>(r))
  },
  startReview: (id: string, mode: 'live' | 'replay') =>
    fetch(`/api/cases/${id}/review`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ mode }) })
      .then(r => j<{ run_id: string }>(r)),
  progress: (runId: string) => fetch(`/api/runs/${runId}`).then(r => j<Progress>(r)),
  draftRequest: (id: string, mode: 'live' | 'replay') =>
    fetch(`/api/cases/${id}/records-request`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ mode }) })
      .then(r => j<RecordsRequest>(r)),
  editRequest: (rid: number, letter: string) =>
    fetch(`/api/records-requests/${rid}`, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ letter }) })
      .then(r => j<{ ok: boolean }>(r)),
  approveRequest: (rid: number) => fetch(`/api/records-requests/${rid}/approve`, { method: 'POST' }).then(r => j<{ ok: boolean }>(r)),
  action: (id: string, body: { action: string; conclusion?: string; rationale?: string; reason?: string }) =>
    fetch(`/api/cases/${id}/actions`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) })
      .then(r => j<{ ok: boolean }>(r)),
}

export const CONCLUSION_LABEL: Record<string, string> = {
  demonstrated: 'Supported by the record',
  not_demonstrated: 'Not supported by the record',
  cannot_determine: 'Unable to determine from the record',
}

export const STATUS_LABEL: Record<string, string> = {
  ready: 'Ready for review', in_review: 'In review', awaiting_records: 'Awaiting records', completed: 'Completed',
  reviewed: 'Reviewed', escalated: 'Escalated to physician advisor', sent_to_coder: 'Sent to coder', queued: 'Queued',
}
