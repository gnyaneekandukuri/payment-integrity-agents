import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Badge, Button, Card } from '../components/ui'
import { ProgressPanel } from './CaseReview'

type Metric = { id: string; label: string; value: number | string; unit: string; note: string }
type Explanation = { name: string; label: string; status: string; summary: string; confirmed_by: string | null;
  citations: { id: string; label: string; value: string }[] }
type Stay = { id: string; admit_date: string; los: number; paid_amount: number; case_id: string | null; patient_name: string | null }
type Detail = {
  question: { id: string; hospital: string; drg: string; title: string }
  metrics: Record<string, Metric>
  trend: { period: string; value: number }[]
  explanations: Explanation[]
  rationale: string | null
  run: { id: string; mode: string; model: string; steps: number; status: string } | null
  has_saved_run: boolean
  sensitivity: { stays: number; billed_871: number; referral_rate: number; above_peer_rate: number }
  sample: { stays: Stay[]; eligible: number; approved: boolean; approved_note: string | null }
}

const QID = 'Q-RIV-871'
const STATUS: Record<string, { label: string; tone: string }> = {
  supported: { label: 'Supported', tone: 'green' }, supported_in_part: { label: 'Supported in part', tone: 'blue' },
  weakened: { label: 'Weakened', tone: 'gray' }, unresolved: { label: 'Unresolved', tone: 'amber' },
}
const money = (n: number) => n.toLocaleString('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 })

async function post(url: string, body?: unknown) {
  const r = await fetch(url, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: body ? JSON.stringify(body) : undefined })
  if (!r.ok) throw new Error((await r.json().catch(() => ({}))).detail ?? r.statusText)
  return r.json()
}

export default function Patterns({ embedded = false }: { embedded?: boolean }) {
  const [d, setD] = useState<Detail | null>(null)
  const [runId, setRunId] = useState<string | null>(null)
  const [err, setErr] = useState('')
  const load = useCallback(() => fetch(`/api/patterns/${QID}`).then(r => r.json()).then(setD).catch(e => setErr(String(e))), [])
  useEffect(() => { load() }, [load])
  if (err) return <div className="text-sm text-rose-700">{err}</div>
  if (!d) return <div className="text-sm text-muted">Loading…</div>
  const m = d.metrics
  const start = async (mode: 'live' | 'replay') => {
    try { setRunId((await post(`/api/patterns/${QID}/review`, { mode })).run_id) } catch (e) { setErr((e as Error).message) }
  }

  return (
    <div className="space-y-4">
      {!embedded && (
        <div>
          <h1 className="text-xl font-semibold">Lead investigation</h1>
          <p className="text-sm text-muted mt-1">A pattern is a question, not a finding. The assistant tests each explanation against the plan's data; you decide what it supports.</p>
        </div>
      )}
      {embedded && <p className="text-sm text-muted">A lead is a question, not a finding. The assistant tests each explanation against the plan's data; you decide what it supports.</p>}

      {/* 1. The question */}
      <Card title={<span>{d.question.hospital} · DRG {d.question.drg} <span className="font-normal text-muted">{d.question.title}</span></span>}
        right={<Badge tone="violet">From the quarterly monitoring report</Badge>}>
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
          <Stat label="Riverside, 2025" value={`${m.share_riverside_2025.value}%`} note={`of infection stays billed as DRG 871 (${m.share_riverside_2025.note})`} strong />
          <Stat label="Riverside, 2023" value={`${m.share_riverside_2023.value}%`} note={m.share_riverside_2023.note} />
          <Stat label="Community peers, 2025 (14)" value={`${m.peer_median_community_2025.value}%`} note={`median; ${m.peer_median_community_2025.note.split(';')[0]}`} />
          <Stat label="Referral peers, 2025 (6)" value={`${m.peer_median_referral_2025.value}%`} note={`median; ${m.peer_median_referral_2025.note.split(';')[0]}`} />
        </div>
        <div className="mt-4">
          <div className="text-xs text-muted mb-1">Riverside DRG 871 share by quarter (computed from the plan's claims)</div>
          <div className="flex flex-wrap gap-1.5">
            {d.trend.map(t => (
              <div key={t.period} className={`text-center rounded-md px-2.5 py-1.5 text-xs ${t.value > 30 ? 'bg-amber-50 ring-1 ring-amber-200' : 'bg-gray-50'}`}>
                <div className="text-muted">{t.period}</div><div className="font-semibold text-sm">{t.value}%</div>
              </div>
            ))}
          </div>
        </div>
        <div className="grid md:grid-cols-2 gap-3 mt-4 text-sm">
          <div className="rounded-md bg-gray-50 p-3"><b>What this shows:</b> Riverside differs from similar hospitals, and the difference grew from the third quarter of 2024.</div>
          <div className="rounded-md bg-gray-50 p-3"><b>What it doesn't show:</b> that any stay was billed incorrectly, or that any money was overpaid. Different is not wrong.</div>
        </div>
      </Card>

      {/* 2. Explanations */}
      <Card title="Possible explanations" right={
        <div className="flex gap-2">
          <Button variant={d.explanations.length ? 'ghost' : 'primary'} onClick={() => start('live')}>{d.explanations.length ? 'Re-run' : 'Test explanations (live)'}</Button>
          {d.has_saved_run && <Button variant="secondary" onClick={() => start('replay')}>Replay saved run</Button>}
        </div>}>
        {runId && <div className="mb-4"><ProgressPanel runId={runId} onDone={() => { setRunId(null); load() }} /></div>}
        {!d.explanations.length && !runId && <p className="text-sm text-muted">The assistant hasn't tested the explanations yet.</p>}
        <div className="space-y-3">
          {d.explanations.map(e => <ExplanationRow key={e.name} e={e} onChange={load} />)}
        </div>
        {d.run && <p className="text-xs text-muted mt-3">Run {d.run.id} · {d.run.mode === 'replay' ? 'replayed from a saved run' : 'live'} · {d.run.model} · {d.run.steps} tool calls. Statuses: supported / supported in part / weakened / unresolved. Never "ruled out".</p>}
      </Card>

      {/* 3. Rationale */}
      {d.rationale && (
        <Card title="Rationale for a targeted records review (assistant draft)">
          <p className="text-sm leading-relaxed">{d.rationale}</p>
        </Card>
      )}

      {/* 4. Sensitivity */}
      <Sensitivity s={d.sensitivity} />

      {/* 5. Sample */}
      <SampleCard d={d} onApproved={load} />
    </div>
  )
}

function Stat({ label, value, note, strong }: { label: string; value: string; note: string; strong?: boolean }) {
  return (
    <div className={`rounded-lg border p-3 ${strong ? 'border-amber-300 bg-amber-50/50' : 'border-line'}`}>
      <div className="text-xs text-muted">{label}</div>
      <div className="text-2xl font-semibold mt-0.5">{value}</div>
      <div className="text-xs text-muted mt-0.5">{note}</div>
    </div>
  )
}

function ExplanationRow({ e, onChange }: { e: Explanation; onChange: () => void }) {
  const [editing, setEditing] = useState(false)
  const [status, setStatus] = useState(e.status)
  const [note, setNote] = useState('')
  const st = STATUS[e.status] ?? { label: e.status, tone: 'gray' }
  const save = async (s: string, n?: string) => { await post(`/api/patterns/${QID}/explanations/${e.name}`, { status: s, note: n || null }); setEditing(false); onChange() }
  return (
    <div className="rounded-md border border-line p-3">
      <div className="flex items-center gap-2">
        <div className="font-medium text-sm">{e.label}</div>
        <Badge tone={st.tone}>{st.label}</Badge>
        <span className="ml-auto text-xs">
          {e.confirmed_by ? <span className="text-emerald-700">✓ Confirmed by {e.confirmed_by}</span>
            : <span className="flex gap-1">
                <Button variant="secondary" onClick={() => save(e.status)}>Confirm</Button>
                <Button variant="ghost" onClick={() => setEditing(!editing)}>Change</Button>
              </span>}
        </span>
      </div>
      <p className="text-sm mt-1.5 leading-relaxed">{e.summary}</p>
      <div className="flex flex-wrap gap-1.5 mt-2">
        {e.citations.map(c => (
          <span key={c.id} title={c.label} className="text-[11px] rounded bg-gray-100 px-1.5 py-0.5">
            <span className="text-muted">{c.label.length > 60 ? c.label.slice(0, 60) + '…' : c.label}:</span> <b>{c.value}</b>
          </span>
        ))}
      </div>
      {editing && (
        <div className="mt-2 flex flex-wrap items-center gap-2">
          <select value={status} onChange={ev => setStatus(ev.target.value)} className="text-sm border border-line rounded-md px-2 py-1">
            {Object.entries(STATUS).map(([k, v]) => <option key={k} value={k}>{v.label}</option>)}
          </select>
          <input value={note} onChange={ev => setNote(ev.target.value)} placeholder="Reason" className="text-sm border border-line rounded-md px-2 py-1 flex-1 min-w-48" />
          <Button disabled={!note.trim()} onClick={() => save(status, note)}>Save</Button>
        </div>
      )}
    </div>
  )
}

function Sensitivity({ s }: { s: Detail['sensitivity'] }) {
  const [shares, setShares] = useState([0, 25, 50])
  const [diffs, setDiffs] = useState([3000, 6000])
  const num = (v: string) => Math.max(0, Number(v) || 0)
  return (
    <Card title="How much could be involved? (hypothetical sensitivity, not an overpayment estimate)">
      <div className="text-sm space-y-2">
        <p>At the referral-peer rate ({s.referral_rate}%), Riverside would bill about {Math.round(s.referral_rate / 100 * s.stays)} of its {s.stays.toLocaleString()} infection stays as DRG 871. It billed {s.billed_871}, so <b>{s.above_peer_rate} stays are above the peer rate</b>. That is a statistical gap, not a count of incorrect claims.</p>
        <div className="overflow-x-auto">
          <table className="text-sm">
            <thead><tr><th className="text-left pr-6 py-1 text-xs text-muted font-medium">Share regrouped after review (assumption)</th>
              {diffs.map((v, i) => <th key={i} className="px-3 py-1 text-xs text-muted font-medium">Avg difference <input value={v} onChange={e => setDiffs(diffs.map((x, j) => j === i ? num(e.target.value) : x))} className="w-20 border border-line rounded px-1 ml-1" /></th>)}</tr></thead>
            <tbody>
              {shares.map((sh, i) => (
                <tr key={i} className="border-t border-line">
                  <td className="pr-6 py-1.5"><input value={sh} onChange={e => setShares(shares.map((x, j) => j === i ? num(e.target.value) : x))} className="w-14 border border-line rounded px-1" /> %</td>
                  {diffs.map((df, j) => <td key={j} className="px-3 py-1.5 text-right font-medium">{money(s.above_peer_rate * sh / 100 * df)}</td>)}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="text-xs text-amber-800 bg-amber-50 rounded-md px-3 py-2">Used only to judge whether a records review is worth the cost and the burden on the hospital. Payment difference, validated overpayment and realized recovery are different numbers; none is known yet.</p>
      </div>
    </Card>
  )
}

function SampleCard({ d, onApproved }: { d: Detail; onApproved: () => void }) {
  const [busy, setBusy] = useState(false)
  const approve = async () => { setBusy(true); try { await post(`/api/patterns/${QID}/sample/approve`); onApproved() } finally { setBusy(false) } }
  return (
    <Card title={`Targeted records review: ${d.sample.stays.length} stays`}
      right={d.sample.approved ? <Badge tone="green">Approved</Badge> : <Badge tone="amber">Needs manager approval</Badge>}>
      <div className="text-sm space-y-3">
        <p>Selected to test the unresolved questions: DRG 871 stays in 2025 with a stay of <b>4 days or less</b>, <b>no ICU days</b>, <b>not transferred in</b>, <b>discharged home</b> ({d.sample.eligible} stays qualify; {d.sample.stays.length} selected).</p>
        <p className="text-xs bg-gray-50 rounded-md px-3 py-2"><b>A targeted sample is not a statistical sample.</b> Its findings describe only the stays reviewed and cannot be extrapolated to Riverside's other DRG 871 stays.</p>
        <div className="max-h-64 overflow-y-auto border border-line rounded-md">
          <table className="w-full text-xs">
            <thead className="bg-gray-50 text-muted text-left"><tr><th className="px-3 py-1.5">Claim</th><th>Admitted</th><th>Stay</th><th>Paid</th><th>Records</th></tr></thead>
            <tbody className="divide-y divide-line">
              {d.sample.stays.map(s => (
                <tr key={s.id}><td className="px-3 py-1.5 font-mono">{s.id}</td><td>{s.admit_date}</td><td>{s.los} days</td><td>{money(s.paid_amount)}</td>
                  <td>{s.case_id ? <Badge tone="blue">Received ({s.patient_name})</Badge> : <span className="text-muted">To be requested</span>}</td></tr>
              ))}
            </tbody>
          </table>
        </div>
        {d.sample.approved ? (
          <div className="rounded-md bg-emerald-50 text-emerald-900 px-3 py-2">
            {d.sample.approved_note}. The {d.sample.stays.length} stays are now in the clinical review queue. <Link to="/" className="underline font-medium">Open Sam's queue →</Link>
          </div>
        ) : (
          <div className="flex items-center gap-3">
            <Button onClick={approve} disabled={busy || !d.explanations.length}>Approve targeted review (manager)</Button>
            <span className="text-xs text-muted">{d.explanations.length ? 'Demo: approval by the payment integrity manager. Provider relations is informed before the hospital is contacted.' : 'Test the explanations first.'}</span>
          </div>
        )}
      </div>
    </Card>
  )
}
