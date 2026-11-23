import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { api, CONCLUSION_LABEL, STATUS_LABEL, type CaseDetail, type Evidence, type Progress } from '../api'
import { Badge, Button, Card, conclusionTone, statusTone } from '../components/ui'
import { ORIGIN_TONE } from './Queue'

const SYSTEMS = ['cardiovascular', 'renal', 'respiratory', 'coagulation', 'liver', 'cns'] as const
const SYSTEM_LABEL: Record<string, string> = {
  cardiovascular: 'Cardiovascular (blood pressure, vasopressors)', renal: 'Renal (creatinine)', respiratory: 'Respiratory (oxygenation)',
  coagulation: 'Coagulation (platelets)', liver: 'Liver (bilirubin)', cns: 'Central nervous system (mental status)',
}
const SOFA_STATUS: Record<string, { label: string; tone: string }> = {
  scored: { label: 'Scored', tone: 'green' },
  not_documented: { label: 'Not documented', tone: 'amber' },
  not_formally_assessable: { label: 'Not formally assessable', tone: 'amber' },
  baseline_uncertain: { label: 'Baseline uncertain', tone: 'red' },
}
const GAP_LABEL: Record<string, { label: string; tone: string }> = {
  missing: { label: 'Missing', tone: 'amber' }, conflicting: { label: 'Conflicting', tone: 'red' },
  coding_question: { label: 'Coding question (for coder)', tone: 'violet' },
}

export default function CaseReview() {
  const { id = '' } = useParams()
  const [detail, setDetail] = useState<CaseDetail | null>(null)
  const [error, setError] = useState('')
  const [runId, setRunId] = useState<string | null>(null)
  const [selected, setSelected] = useState<Evidence | null>(null)
  const [page, setPage] = useState(1)

  const load = useCallback(() => api.caseDetail(id).then(d => { setDetail(d); setError('') }).catch(e => setError(e.message)), [id])
  useEffect(() => { load() }, [load])
  useEffect(() => {
    if (detail?.review?.run.status === 'running') setRunId(detail.review.run.id)
  }, [detail])

  if (error) return <div className="text-sm text-rose-700">{error}</div>
  if (!detail) return <div className="text-sm text-muted">Loading…</div>
  const { review } = detail

  const start = async (mode: 'live' | 'replay') => {
    try {
      const r = await api.startReview(id, mode)
      setRunId(r.run_id)
    } catch (e) { setError((e as Error).message) }
  }

  return (
    <div className="space-y-4">
      <div className="text-sm"><Link to="/" className="text-brand hover:underline">← Review queue</Link></div>
      <CaseHeader detail={detail} />
      <WhyCard detail={detail} />

      {!detail.chart && <UploadPanel caseId={id} onUploaded={load} />}

      {runId && <ProgressPanel runId={runId} onDone={() => { setRunId(null); load() }} />}

      {detail.chart && !review && !runId && (
        <Card title="Records attached. Ready for the assistant">
          <p className="text-sm text-muted mb-3">{detail.chart.page_count} pages. The assistant will read the record, cite evidence for each criterion, flag gaps, and draft a conclusion for your review.</p>
          <div className="flex gap-2">
            <Button onClick={() => start('live')}>Run review (live)</Button>
            {detail.has_saved_run && <Button variant="secondary" onClick={() => start('replay')}>Replay saved run (offline)</Button>}
          </div>
        </Card>
      )}

      {review && !runId && (
        <>
          <div className="grid grid-cols-12 gap-4">
            <ClaimCard detail={detail} className="col-span-12 lg:col-span-4" />
            <CriteriaCard detail={detail} className="col-span-12 lg:col-span-3" />
            <DraftCard detail={detail} onAction={load} onRerun={start} className="col-span-12 lg:col-span-5" />
          </div>
          <div className="grid grid-cols-12 gap-4 items-start">
            <div className="col-span-12 xl:col-span-7 space-y-4">
              <EvidenceBoard detail={detail} selected={selected} onSelect={e => { setSelected(e); setPage(e.page) }} />
              <GapsCard detail={detail} />
              <RecordsRequestCard detail={detail} onChange={load} />
              <SofaCard detail={detail} />
            </div>
            <div className="col-span-12 xl:col-span-5 xl:sticky xl:top-4 space-y-4">
              <RecordViewer caseId={id} pages={detail.pages} page={page} setPage={setPage} quote={selected?.page === page ? selected.quote : undefined} />
              <TraceCard runId={review.run.id} run={review.run} />
              <AuditCard detail={detail} />
            </div>
          </div>
        </>
      )}
    </div>
  )
}

function CaseHeader({ detail }: { detail: CaseDetail }) {
  const c = detail.case
  return (
    <div className="bg-white border border-line rounded-lg px-5 py-4 flex flex-wrap items-center gap-x-8 gap-y-2">
      <div>
        <div className="text-lg font-semibold">{c.patient_name} <span className="text-muted font-normal text-sm">{c.age}{c.sex}</span></div>
        <div className="text-xs text-muted">{c.claim_id} · {c.hospital}</div>
      </div>
      <div><div className="text-xs text-muted">Billed DRG</div><div className="text-sm font-medium">{c.billed_drg} · {c.drg_title}</div></div>
      <div><div className="text-xs text-muted">Stay</div><div className="text-sm">{c.admit_date} → {c.discharge_date} ({c.los} days{c.icu_days ? `, ICU ${c.icu_days}` : ''})</div></div>
      <div className="flex gap-2 ml-auto">
        <Badge tone={ORIGIN_TONE[c.review_origin ?? ''] ?? 'gray'}>{c.review_origin ?? 'Review'}</Badge>
        <Badge tone={statusTone(c.status)}>{STATUS_LABEL[c.status] ?? c.status}</Badge>
      </div>
    </div>
  )
}

function WhyCard({ detail }: { detail: CaseDetail }) {
  const c = detail.case
  if (!c.review_reason) return null
  const rows: [string, string | null, string?][] = [
    ['Selected by', c.review_reason],
    ['The concern', c.review_concern],
    ['Your question', c.review_question, 'font-medium text-ink'],
    ['Not your question', c.review_not_yours],
    ['Context', c.review_context],
  ]
  return (
    <Card title="Why this claim is being reviewed" right={<Badge tone={ORIGIN_TONE[c.review_origin ?? ''] ?? 'gray'}>{c.review_origin}</Badge>}>
      <dl className="grid grid-cols-[10rem_1fr] gap-x-4 gap-y-2 text-sm">
        {rows.filter(([, v]) => v).map(([k, v, cls]) => (
          <div key={k} className="contents">
            <dt className="text-muted">{k}</dt>
            <dd className={cls ?? 'text-ink/90'}>{v}</dd>
          </div>
        ))}
      </dl>
    </Card>
  )
}

function UploadPanel({ caseId, onUploaded }: { caseId: string; onUploaded: () => void }) {
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState('')
  const [drag, setDrag] = useState(false)
  const input = useRef<HTMLInputElement>(null)
  const send = async (file?: File) => {
    if (!file) return
    setBusy(true); setErr('')
    try { await api.upload(caseId, file); onUploaded() } catch (e) { setErr((e as Error).message) } finally { setBusy(false) }
  }
  return (
    <Card title="Medical records not received yet">
      <div
        onDragOver={e => { e.preventDefault(); setDrag(true) }} onDragLeave={() => setDrag(false)}
        onDrop={e => { e.preventDefault(); setDrag(false); send(e.dataTransfer.files[0]) }}
        className={`border-2 border-dashed rounded-lg p-8 text-center ${drag ? 'border-brand bg-brand-soft' : 'border-line'}`}>
        <div className="text-sm font-medium">Drop the hospital's medical record (PDF) here</div>
        <div className="text-xs text-muted mt-1">The record is read page by page. Pages without readable text are flagged for OCR rather than guessed.</div>
        <div className="mt-4">
          <Button onClick={() => input.current?.click()} disabled={busy}>{busy ? 'Reading the record…' : 'Choose PDF'}</Button>
          <input ref={input} type="file" accept="application/pdf" className="hidden" onChange={e => send(e.target.files?.[0])} />
        </div>
        {err && <div className="text-sm text-rose-700 mt-3">{err}</div>}
      </div>
    </Card>
  )
}

export function ProgressPanel({ runId, onDone }: { runId: string; onDone: () => void }) {
  const [p, setP] = useState<Progress | null>(null)
  useEffect(() => {
    let stop = false
    const tick = async () => {
      try {
        const next = await api.progress(runId)
        if (stop) return
        setP(next)
        if (['completed', 'failed', 'incomplete'].includes(next.run.status)) { setTimeout(onDone, 1200); return }
      } catch { /* keep polling */ }
      if (!stop) setTimeout(tick, 900)
    }
    tick()
    return () => { stop = true }
  }, [runId, onDone])
  const steps = p?.steps ?? []
  const evidence = steps.filter(s => s.tool === 'record_evidence' && s.accepted).length
  const rejected = steps.filter(s => !s.accepted).length
  return (
    <Card title={<span>Assistant is reviewing the record <span className="text-muted font-normal">· {p?.run.mode === 'replay' ? 'replay of a saved run' : 'live'}</span></span>}
      right={<Badge tone={p?.run.status === 'failed' ? 'red' : 'violet'}>{p?.run.status ?? 'starting'}</Badge>}>
      <div className="flex gap-6 text-sm mb-3">
        <div><span className="font-semibold">{steps.length}</span> <span className="text-muted">steps</span></div>
        <div><span className="font-semibold">{evidence}</span> <span className="text-muted">evidence recorded</span></div>
        <div><span className="font-semibold">{rejected}</span> <span className="text-muted">rejected by checks</span></div>
      </div>
      {p?.run.error && <div className="text-sm text-rose-700 mb-2">{p.run.error}</div>}
      <ol className="max-h-80 overflow-y-auto space-y-1 text-sm font-mono">
        {steps.map(s => (
          <li key={s.n} className={`flex gap-2 ${s.accepted ? '' : 'text-rose-700'}`}>
            <span className="text-muted w-6 text-right">{s.n}</span>
            <span>{s.accepted ? '✓' : '✗'}</span>
            <span className="font-sans">{s.label}{s.detail && <span className="text-muted"> · {s.detail}</span>}
              {!s.accepted && s.reason && <span className="block text-xs">Rejected: {s.reason}</span>}</span>
          </li>
        ))}
        {steps.length === 0 && <li className="text-muted font-sans">Starting…</li>}
      </ol>
    </Card>
  )
}

function ClaimCard({ detail, className }: { detail: CaseDetail; className?: string }) {
  const c = detail.case
  return (
    <Card title="Claim" className={className}>
      <div className="text-sm space-y-2">
        <div><span className="text-muted">Principal diagnosis:</span> <span className="font-medium">{c.principal_dx}</span></div>
        <div className="text-muted">Secondary diagnoses</div>
        <ul className="space-y-1">
          {c.secondary_dx.map(d => (
            <li key={d.code} className="flex gap-2"><span className="font-mono text-xs bg-gray-100 rounded px-1.5 py-0.5">{d.code}</span><span>{d.desc}</span></li>
          ))}
        </ul>
        <p className="text-xs text-muted pt-1">Clinical review answers the clinical question only. The MCC and complete coding are validated by the coder.</p>
      </div>
    </Card>
  )
}

function CriteriaCard({ detail, className }: { detail: CaseDetail; className?: string }) {
  const silent = detail.contract.sepsis_criteria === 'silent'
  return (
    <Card title="Criteria applied" className={className}>
      <div className="text-sm space-y-2">
        <div className="font-medium">Sepsis-3</div>
        {silent ? <Badge tone="amber">Contract silent: plan default applied</Badge> : <Badge tone="green">Specified in contract</Badge>}
        <p className="text-xs text-muted">Suspected infection plus an acute change in total SOFA score of 2 or more. Baseline assumed 0 only when no pre-existing dysfunction is known.</p>
        <p className="text-xs text-muted border-t border-line pt-2">{detail.contract.summary}</p>
      </div>
    </Card>
  )
}

function DraftCard({ detail, onAction, onRerun, className }:
  { detail: CaseDetail; onAction: () => void; onRerun: (m: 'live' | 'replay') => void; className?: string }) {
  const d = detail.review?.draft
  const [mode, setMode] = useState<'none' | 'change' | 'escalate'>('none')
  const [conclusion, setConclusion] = useState('cannot_determine')
  const [reason, setReason] = useState('')
  const [err, setErr] = useState('')
  const last = detail.actions.filter(a => ['accept', 'change_conclusion', 'escalate', 'send_to_coder'].includes(a.action)).at(-1)
  const act = async (body: { action: string; conclusion?: string; reason?: string }) => {
    setErr('')
    try { await api.action(detail.case.id, body); setMode('none'); setReason(''); onAction() } catch (e) { setErr((e as Error).message) }
  }
  if (!d) return <Card title="Assistant draft" className={className}><p className="text-sm text-rose-700">The run ended without an accepted draft ({detail.review?.run.status}).</p></Card>
  return (
    <Card title="Assistant draft: is sepsis supported? (for your decision)" className={className}
      right={<Badge tone={conclusionTone(d.conclusion)}>{CONCLUSION_LABEL[d.conclusion]}</Badge>}>
      {d.sections ? (
        <div className="space-y-2.5 text-sm">
          <p className="font-medium leading-relaxed">{d.sections.summary}</p>
          {([['What the record shows', d.sections.documented], ['What is uncertain', d.sections.uncertain],
             ['What would resolve it', d.sections.would_resolve]] as const).map(([label, text]) => text && (
            <div key={label}>
              <div className="text-xs font-semibold uppercase tracking-wide text-muted">{label}</div>
              <p className="leading-relaxed mt-0.5">{text}</p>
            </div>
          ))}
        </div>
      ) : <p className="text-sm leading-relaxed">{d.rationale}</p>}
      {d.conclusion !== 'cannot_determine' && typeof d.validator_result?.gaps_addressed === 'string' && d.validator_result.gaps_addressed && (
        <p className="text-xs text-muted mt-2"><span className="font-medium">Why recorded gaps don't change it:</span> {d.validator_result.gaps_addressed as string}</p>
      )}
      {last && (
        <div className="mt-3 text-xs rounded-md bg-gray-50 px-3 py-2">
          <span className="font-medium">Your decision:</span> {last.action.replace(/_/g, ' ')}{last.after && last.action === 'change_conclusion' ? ` → ${CONCLUSION_LABEL[last.after]}` : ''}
          {last.reason && <> · “{last.reason}”</>} <span className="text-muted">({last.actor}, {last.at.replace('T', ' ').slice(0, 16)})</span>
        </div>
      )}
      <div className="flex flex-wrap gap-2 mt-4">
        <Button onClick={() => act({ action: 'accept' })}>Accept draft</Button>
        <Button variant="secondary" onClick={() => setMode(mode === 'change' ? 'none' : 'change')}>Change conclusion</Button>
        <Button variant="secondary" onClick={() => setMode(mode === 'escalate' ? 'none' : 'escalate')}>Escalate to physician advisor</Button>
        <Button variant="secondary" onClick={() => act({ action: 'send_to_coder' })}>Send to coder</Button>
        <span className="ml-auto flex gap-1">
          <Button variant="ghost" onClick={() => onRerun('live')}>Re-run</Button>
          {detail.has_saved_run && <Button variant="ghost" onClick={() => onRerun('replay')}>Replay</Button>}
        </span>
      </div>
      {mode !== 'none' && (
        <div className="mt-3 space-y-2 rounded-md border border-line p-3">
          {mode === 'change' && (
            <select value={conclusion} onChange={e => setConclusion(e.target.value)} className="text-sm border border-line rounded-md px-2 py-1">
              {Object.entries(CONCLUSION_LABEL).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
            </select>
          )}
          <textarea value={reason} onChange={e => setReason(e.target.value)} placeholder="Reason (required, kept in the audit log)"
            className="w-full text-sm border border-line rounded-md px-2 py-1.5 h-16" />
          <Button disabled={!reason.trim()} onClick={() => act(mode === 'change' ? { action: 'change_conclusion', conclusion, reason } : { action: 'escalate', reason })}>
            {mode === 'change' ? 'Save change' : 'Escalate'}
          </Button>
        </div>
      )}
      {err && <div className="text-sm text-rose-700 mt-2">{err}</div>}
    </Card>
  )
}

function stanceTone(s: string) { return s === 'supports' ? 'green' : s === 'contradicts' ? 'red' : 'gray' }

function EvidenceItem({ e, active, onSelect }: { e: Evidence; active: boolean; onSelect: (e: Evidence) => void }) {
  const tag = e.criterion === 'baseline' ? 'Baseline' : e.criterion === 'preexisting_condition' ? 'Pre-existing' : null
  return (
    <button onClick={() => onSelect(e)}
      className={`w-full text-left rounded-md border px-3 py-2 transition ${active ? 'border-brand bg-brand-soft' : 'border-line hover:bg-gray-50'}`}>
      <div className="flex items-center gap-2 text-sm">
        <span className="font-mono text-xs text-muted">E{e.ref}</span>
        <span className="font-medium">{e.value}</span>
        {tag && <Badge tone="blue">{tag}</Badge>}
        <span className="ml-auto flex items-center gap-2"><Badge tone={stanceTone(e.stance)}>{e.stance}</Badge><span className="text-xs text-brand">p.{e.page}</span></span>
      </div>
      <div className="text-xs text-muted mt-1 italic line-clamp-2">“{e.quote.replace(/\s+/g, ' ')}”</div>
    </button>
  )
}

function EvidenceBoard({ detail, selected, onSelect }: { detail: CaseDetail; selected: Evidence | null; onSelect: (e: Evidence) => void }) {
  const ev = detail.review?.evidence ?? []
  const sofa = Object.fromEntries((detail.review?.sofa ?? []).map(s => [s.system, s]))
  const infection = ev.filter(e => e.criterion === 'infection')
  const other = ev.filter(e => e.criterion !== 'infection' && !e.system)
  return (
    <Card title="Evidence board" right={<span className="text-xs text-muted">Click an item to see it on the page</span>}>
      <div className="space-y-5">
        <section>
          <h3 className="text-xs font-semibold uppercase tracking-wide text-muted mb-2">Infection</h3>
          <div className="space-y-1.5">
            {infection.map(e => <EvidenceItem key={e.ref} e={e} active={selected?.ref === e.ref} onSelect={onSelect} />)}
            {!infection.length && <div className="text-sm text-amber-800 bg-amber-50 rounded-md px-3 py-2">No infection evidence recorded.</div>}
          </div>
        </section>
        {SYSTEMS.map(sys => {
          const items = ev.filter(e => e.system === sys && e.criterion !== 'infection')
          const s = sofa[sys]
          const st = s ? SOFA_STATUS[s.status] : undefined
          return (
            <section key={sys}>
              <div className="flex items-center gap-2 mb-2">
                <h3 className="text-xs font-semibold uppercase tracking-wide text-muted">{SYSTEM_LABEL[sys]}</h3>
                {st && <Badge tone={st.tone}>{st.label}{s?.status === 'scored' ? ` · change ${s.change}` : ''}</Badge>}
              </div>
              <div className="space-y-1.5">
                {items.map(e => <EvidenceItem key={e.ref} e={e} active={selected?.ref === e.ref} onSelect={onSelect} />)}
                {!items.length && <div className="text-sm text-amber-800 bg-amber-50 rounded-md px-3 py-2">Not documented in the evidence. Not assumed normal.</div>}
              </div>
            </section>
          )
        })}
        {other.length > 0 && (
          <section>
            <h3 className="text-xs font-semibold uppercase tracking-wide text-muted mb-2">Other</h3>
            <div className="space-y-1.5">{other.map(e => <EvidenceItem key={e.ref} e={e} active={selected?.ref === e.ref} onSelect={onSelect} />)}</div>
          </section>
        )}
      </div>
    </Card>
  )
}

function GapsCard({ detail }: { detail: CaseDetail }) {
  const gaps = detail.review?.gaps ?? []
  return (
    <Card title={`Gaps and questions (${gaps.length})`}>
      {!gaps.length && <p className="text-sm text-muted">No gaps recorded.</p>}
      <ul className="space-y-2">
        {gaps.map((g, i) => (
          <li key={i} className="text-sm">
            <div className="flex items-center gap-2"><Badge tone={GAP_LABEL[g.kind]?.tone}>{GAP_LABEL[g.kind]?.label ?? g.kind}</Badge><span className="font-medium">{g.item}</span></div>
            <p className="text-xs text-muted mt-1 ml-1">{g.why_it_matters}</p>
          </li>
        ))}
      </ul>
    </Card>
  )
}

function RecordsRequestCard({ detail, onChange }: { detail: CaseDetail; onChange: () => void }) {
  const req = detail.records_request
  const conclusion = detail.review?.draft?.conclusion
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState('')
  const [letter, setLetter] = useState(req?.letter ?? '')
  const [editing, setEditing] = useState(false)
  useEffect(() => { setLetter(req?.letter ?? '') }, [req?.id, req?.letter])
  if (conclusion !== 'cannot_determine' && !req) return null

  const draft = async (mode: 'live' | 'replay') => {
    setBusy(true); setErr('')
    try { await api.draftRequest(detail.case.id, mode); onChange() } catch (e) { setErr((e as Error).message) } finally { setBusy(false) }
  }
  const save = async () => { if (!req) return; await api.editRequest(req.id, letter); setEditing(false); onChange() }
  const approve = async () => { if (!req) return; await api.approveRequest(req.id); onChange() }

  return (
    <Card title="Records follow-up request"
      right={req ? <Badge tone={req.status === 'approved' ? 'green' : 'amber'}>{req.status === 'approved' ? 'Approved, ready to send' : 'Draft for your approval'}</Badge> : undefined}>
      {!req && (
        <div className="text-sm">
          <p className="text-muted mb-3">The record can't settle the question. The assistant can draft a targeted request to the hospital, asking only for what is missing or conflicting, and why. You review and approve it.</p>
          <div className="flex gap-2">
            <Button onClick={() => draft('live')} disabled={busy}>{busy ? 'Drafting…' : 'Draft records request'}</Button>
            {detail.has_saved_request && <Button variant="secondary" onClick={() => draft('replay')} disabled={busy}>Use saved draft (offline)</Button>}
          </div>
        </div>
      )}
      {req && (
        <div className="space-y-3 text-sm">
          <ol className="space-y-2 list-decimal ml-5">
            {req.items.map((it, i) => (
              <li key={i}>
                <div className="font-medium">{it.request}</div>
                <div className="text-xs text-muted mt-0.5">{it.reason}{it.pages.length ? ` (see page${it.pages.length > 1 ? 's' : ''} ${it.pages.join(', ')})` : ''}</div>
              </li>
            ))}
          </ol>
          <details className="rounded-md border border-line" open={editing}>
            <summary className="cursor-pointer px-3 py-2 text-xs text-brand">Letter to the hospital{req.mode === 'template' ? ' (plain template: assistant unavailable)' : ''}</summary>
            {editing
              ? <textarea value={letter} onChange={e => setLetter(e.target.value)} className="w-full h-72 text-xs font-mono p-3 border-t border-line" />
              : <pre className="whitespace-pre-wrap text-xs font-mono p-3 border-t border-line bg-gray-50">{req.letter}</pre>}
          </details>
          {req.status === 'draft' ? (
            <div className="flex gap-2">
              {editing ? <Button onClick={save}>Save letter</Button> : <Button variant="secondary" onClick={() => setEditing(true)}>Edit letter</Button>}
              <Button onClick={approve} disabled={editing}>Approve request</Button>
              <Button variant="ghost" onClick={() => draft('live')} disabled={busy}>Redraft</Button>
            </div>
          ) : (
            <p className="text-xs text-muted">Approved by {req.approved_by} at {req.approved_at?.replace('T', ' ').slice(0, 16)}. The claim returns to "Awaiting records". Nothing is sent in this demo.</p>
          )}
        </div>
      )}
      {err && <div className="text-sm text-rose-700 mt-2">{err}</div>}
    </Card>
  )
}

function SofaCard({ detail }: { detail: CaseDetail }) {
  const rows = detail.review?.sofa ?? []
  const total = rows.filter(r => r.status === 'scored').reduce((a, r) => a + (r.change ?? 0), 0)
  return (
    <Card title="SOFA (calculated by fixed rules from cited values)" right={<span className="text-sm">Change from scored systems: <b>{total}</b> <span className="text-muted">(threshold 2)</span></span>}>
      <table className="w-full text-sm">
        <thead className="text-left text-xs text-muted"><tr><th className="py-1">System</th><th>Baseline</th><th>Worst</th><th>Change</th><th>Status</th></tr></thead>
        <tbody className="divide-y divide-line">
          {SYSTEMS.map(sys => rows.find(r => r.system === sys)).filter(Boolean).map(r => (
            <tr key={r!.system} title={r!.detail}>
              <td className="py-1.5 capitalize">{r!.system === 'cns' ? 'CNS' : r!.system}</td>
              <td>{r!.baseline ?? '—'}</td><td>{r!.worst ?? '—'}</td><td>{r!.change ?? '—'}</td>
              <td><Badge tone={SOFA_STATUS[r!.status]?.tone}>{SOFA_STATUS[r!.status]?.label ?? r!.status}</Badge></td>
            </tr>
          ))}
        </tbody>
      </table>
      <p className="text-xs text-muted mt-2">Hover a row for how its baseline was set. Unscored systems are never assumed normal.</p>
    </Card>
  )
}

function normalise(text: string) {
  const out: string[] = []; const map: number[] = []; let prevSpace = false
  for (let i = 0; i < text.length; i++) {
    const ch = text[i]
    const c = /[\s|]/.test(ch) ? ' ' : ch.toLowerCase()
    if (c === ' ') { if (prevSpace || !out.length) continue; prevSpace = true } else prevSpace = false
    out.push(c); map.push(i)
  }
  return { norm: out.join(''), map }
}

function Highlighted({ text, quote }: { text: string; quote?: string }) {
  const parts = useMemo(() => {
    if (!quote) return null
    const p = normalise(text), q = normalise(quote).norm.trim()
    const pos = p.norm.indexOf(q)
    if (pos < 0 || !q) return null
    return [p.map[pos], p.map[Math.min(pos + q.length - 1, p.map.length - 1)] + 1] as const
  }, [text, quote])
  if (!parts) return <>{text}</>
  return <>{text.slice(0, parts[0])}<mark className="quote">{text.slice(parts[0], parts[1])}</mark>{text.slice(parts[1])}</>
}

function RecordViewer({ caseId, pages, page, setPage, quote }:
  { caseId: string; pages: CaseDetail['pages']; page: number; setPage: (n: number) => void; quote?: string }) {
  const [text, setText] = useState('')
  useEffect(() => { api.page(caseId, page).then(p => setText(p.text)).catch(() => setText('')) }, [caseId, page])
  const section = pages.find(p => p.page === page)?.section
  return (
    <Card title="Medical record" right={<a className="text-xs text-brand hover:underline" href={`/api/cases/${caseId}/pdf#page=${page}`} target="_blank" rel="noreferrer">Open PDF page {page} ↗</a>}>
      <div className="flex flex-wrap gap-1 mb-3">
        {pages.map(p => (
          <button key={p.page} onClick={() => setPage(p.page)} title={p.section}
            className={`text-xs rounded px-2 py-1 ${p.page === page ? 'bg-brand text-white' : 'bg-gray-100 hover:bg-gray-200'}`}>{p.page}</button>
        ))}
      </div>
      <div className="text-xs text-muted mb-1">Page {page}{section ? ` · ${section}` : ''} · text as read by the assistant</div>
      <pre className="text-xs leading-relaxed whitespace-pre-wrap font-mono bg-gray-50 rounded-md p-3 max-h-[28rem] overflow-y-auto"><Highlighted text={text} quote={quote} /></pre>
    </Card>
  )
}

function TraceCard({ runId, run }: { runId: string; run: NonNullable<CaseDetail['review']>['run'] }) {
  const [open, setOpen] = useState(false)
  const [p, setP] = useState<Progress | null>(null)
  useEffect(() => { if (open && !p) api.progress(runId).then(setP) }, [open, p, runId])
  const rejected = p?.steps.filter(s => !s.accepted).length
  return (
    <Card title="How the assistant worked" right={<Button variant="ghost" onClick={() => setOpen(!open)}>{open ? 'Hide steps' : 'Show steps'}</Button>}>
      <div className="text-xs text-muted space-y-0.5">
        <div>Run {run.id} · {run.mode === 'replay' ? 'replayed from a saved run' : 'live'} · {run.model}</div>
        <div>{run.steps} tool calls · {run.input_tokens.toLocaleString()} / {run.output_tokens.toLocaleString()} tokens in/out{rejected !== undefined ? ` · ${rejected} rejected by checks` : ''}</div>
      </div>
      {open && (
        <ol className="mt-3 max-h-72 overflow-y-auto space-y-1 text-xs">
          {p?.steps.map(s => (
            <li key={s.n} className={s.accepted ? '' : 'text-rose-700'}>
              <span className="text-muted mr-1">{s.n}.</span>{s.accepted ? '✓' : '✗'} {s.label}{s.detail && <span className="text-muted"> · {s.detail}</span>}
              {!s.accepted && s.reason && <div className="ml-5">Rejected: {s.reason}</div>}
            </li>
          ))}
        </ol>
      )}
    </Card>
  )
}

function AuditCard({ detail }: { detail: CaseDetail }) {
  if (!detail.actions.length) return null
  return (
    <Card title="Audit log">
      <ul className="text-xs space-y-1">
        {detail.actions.map((a, i) => (
          <li key={i}><span className="text-muted">{a.at.replace('T', ' ').slice(0, 16)}</span> · {a.actor} · {a.action.replace(/_/g, ' ')}
            {a.after && a.action !== 'edit_rationale' ? ` → ${CONCLUSION_LABEL[a.after] ?? a.after}` : ''}{a.reason ? ` · “${a.reason}”` : ''}</li>
        ))}
      </ul>
    </Card>
  )
}
