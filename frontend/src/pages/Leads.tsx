import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { Badge, Card } from '../components/ui'
import Patterns from './Patterns'

type Lead = {
  id: string; lead_type: string; type_label: string; hospital_id: string; hospital: string; title: string; measure: string;
  value: number; peer_value: number; earlier_value: number | null; unit: string; stays: number; rule: string;
  status: string; status_note: string | null; flagged_on: string; question_id: string | null; peer_label: string
  detected_by: string[]; evidence: string[]
}

const METHOD: Record<string, { label: string; tone: string; help: string }> = {
  rule: { label: 'Rule', tone: 'gray', help: 'A defined check written in advance (an audit concept)' },
  peer_profiling: { label: 'Peer profiling', tone: 'blue', help: 'Compared across every severity family with no pattern named in advance' },
  change_detection: { label: 'Change detection', tone: 'violet', help: "A lasting step up in the hospital's own history" },
}

function Methods({ list }: { list: string[] }) {
  return <div className="flex flex-wrap gap-1">{list.map(m => <span key={m} title={METHOD[m]?.help}><Badge tone={METHOD[m]?.tone}>{METHOD[m]?.label ?? m}</Badge></span>)}</div>
}
type LeadDetail = Lead & {
  years: { year: number; value: number; count: number; of: number; peer_median: number }[]
  quarters: { period: string; value: number }[]
  notes: { source: string; note_date: string; text: string }[]
}

export const LEAD_STATUS: Record<string, { label: string; tone: string }> = {
  new: { label: 'New', tone: 'amber' }, in_analysis: { label: 'In analysis', tone: 'violet' },
  records_requested: { label: 'Records requested', tone: 'blue' }, closed_no_findings: { label: 'Closed: no findings', tone: 'gray' },
}

function trendWord(l: Lead) {
  if (l.earlier_value == null) return ''
  const d = l.value - l.earlier_value
  return Math.abs(d) < 3 ? `steady (${l.earlier_value}% in 2023)` : d > 0 ? `rising (from ${l.earlier_value}% in 2023)` : `falling (from ${l.earlier_value}% in 2023)`
}

export function LeadsList() {
  const [leads, setLeads] = useState<Lead[] | null>(null)
  useEffect(() => { fetch('/api/leads').then(r => r.json()).then(setLeads) }, [])
  const counts = (leads ?? []).reduce<Record<string, number>>((a, l) => { a[l.status] = (a[l.status] ?? 0) + 1; return a }, {})
  return (
    <div className="space-y-5">
      <div className="flex items-end justify-between">
        <div>
          <h1 className="text-xl font-semibold">Leads: anomalous trends flagged by monitoring</h1>
          <p className="text-sm text-muted mt-1 max-w-3xl">The monitoring job compares every hospital with its peers across the plan's claims and flags patterns that are both large and material. A lead is a question to investigate, not a finding.</p>
        </div>
        <div className="flex gap-2 text-xs">{Object.entries(LEAD_STATUS).map(([k, v]) => <Badge key={k} tone={v.tone}>{v.label}: {counts[k] ?? 0}</Badge>)}</div>
      </div>
      <Card>
        <div className="-m-4 overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="text-left text-xs uppercase tracking-wide text-muted bg-gray-50">
              <tr>
                <th className="px-4 py-2.5 font-medium">Lead</th>
                <th className="px-4 py-2.5 font-medium">Hospital</th>
                <th className="px-4 py-2.5 font-medium">What looks off (2025)</th>
                <th className="px-4 py-2.5 font-medium">Trend</th>
                <th className="px-4 py-2.5 font-medium">Detected by</th>
                <th className="px-4 py-2.5 font-medium">Stays involved</th>
                <th className="px-4 py-2.5 font-medium">Status</th>
                <th className="px-4 py-2.5 font-medium">Flagged</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-line">
              {(leads ?? []).map(l => {
                const st = LEAD_STATUS[l.status]
                return (
                  <tr key={l.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3">
                      <Link to={`/leads/${l.id}`} className="font-medium text-brand hover:underline">{l.title}</Link>
                      <div className="text-xs text-muted">{l.id} · {l.type_label}</div>
                    </td>
                    <td className="px-4 py-3">{l.hospital}</td>
                    <td className="px-4 py-3">
                      <span className="font-semibold">{l.value}%</span> <span className="text-muted">vs {l.peer_value}% ({l.peer_label} median)</span>
                      <div className="text-xs text-muted max-w-72">{l.measure}</div>
                    </td>
                    <td className="px-4 py-3 text-xs">{trendWord(l)}</td>
                    <td className="px-4 py-3"><Methods list={l.detected_by} />
                      {l.detected_by.length === 1 && l.detected_by[0] === 'change_detection' && l.value <= l.peer_value + 10 &&
                        <div className="text-[11px] text-muted mt-1 max-w-40">Own history only; level is close to peers</div>}</td>
                    <td className="px-4 py-3">{l.stays.toLocaleString()}</td>
                    <td className="px-4 py-3"><Badge tone={st?.tone}>{st?.label ?? l.status}</Badge>
                      {l.status_note && <div className="text-xs text-muted mt-1 max-w-56">{l.status_note}</div>}</td>
                    <td className="px-4 py-3 text-xs whitespace-nowrap">{l.flagged_on}</td>
                  </tr>
                )
              })}
            </tbody>
          </table>
          {leads === null && <div className="p-6 text-sm text-muted">Loading…</div>}
        </div>
      </Card>
      <Card title="How leads are detected">
        <div className="grid md:grid-cols-3 gap-3 text-sm">
          <div><Badge tone="gray">Rule</Badge><p className="text-xs text-muted mt-1">Checks written in advance (audit concepts): e.g. DRG 871 share at least 10 points and 1.25x above the peer median; very short stays at least 8 points and 1.8x; readmissions at least 5 points above. Catch known patterns.</p></div>
          <div><Badge tone="blue">Peer profiling</Badge><p className="text-xs text-muted mt-1">No pattern named in advance: every hospital is compared with its peers across every DRG severity family. Finds patterns nobody wrote a rule for.</p></div>
          <div><Badge tone="violet">Change detection</Badge><p className="text-xs text-muted mt-1">Each hospital against its own history: a lasting step up, and when it started. Noisier on its own; strongest when it agrees with another method.</p></div>
        </div>
        <p className="text-xs text-muted mt-3">Leads caught by more methods are listed first. Production would add anomaly models, network analysis and outside signals (tips, regulator alerts). All data fictional.</p>
      </Card>
    </div>
  )
}

export function LeadPage() {
  const { id = '' } = useParams()
  const [d, setD] = useState<LeadDetail | null>(null)
  useEffect(() => { fetch(`/api/leads/${id}`).then(r => r.json()).then(setD) }, [id])
  if (!d) return <div className="text-sm text-muted">Loading…</div>
  const st = LEAD_STATUS[d.status]
  return (
    <div className="space-y-4">
      <div className="text-sm"><Link to="/leads" className="text-brand hover:underline">← Leads</Link></div>
      <div className="bg-white border border-line rounded-lg px-5 py-4 flex flex-wrap items-center gap-x-8 gap-y-2">
        <div>
          <div className="text-lg font-semibold">{d.title}</div>
          <div className="text-xs text-muted">{d.id} · {d.type_label} · {d.hospital} · flagged {d.flagged_on}</div>
        </div>
        <div className="ml-auto flex items-center gap-3"><Methods list={d.detected_by} /><Badge tone={st?.tone}>{st?.label}</Badge></div>
      </div>
      {d.question_id ? <Patterns embedded /> : <GenericLead d={d} />}
    </div>
  )
}

function GenericLead({ d }: { d: LeadDetail }) {
  return (
    <>
      <Card title="What the monitoring job found">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          {d.years.map(y => (
            <div key={y.year} className={`rounded-lg border p-3 ${y.year === 2025 ? 'border-amber-300 bg-amber-50/50' : 'border-line'}`}>
              <div className="text-xs text-muted">{d.hospital.split(' ')[0]}, {y.year}</div>
              <div className="text-2xl font-semibold">{y.value}%</div>
              <div className="text-xs text-muted">{y.count.toLocaleString()} of {y.of.toLocaleString()} stays · {d.peer_label} median {y.peer_median}%</div>
            </div>
          ))}
        </div>
        <div className="mt-4">
          <div className="text-xs text-muted mb-1">{d.measure}, by quarter</div>
          <div className="flex flex-wrap gap-1.5">
            {d.quarters.map(q => <div key={q.period} className="text-center rounded-md bg-gray-50 px-2.5 py-1.5 text-xs"><div className="text-muted">{q.period}</div><div className="font-semibold text-sm">{q.value}%</div></div>)}
          </div>
        </div>
        <div className="mt-4">
          <div className="text-xs text-muted mb-1">How it was detected</div>
          <Methods list={d.detected_by} />
          <ul className="mt-2 text-sm space-y-1">{d.evidence.map((e, i) => <li key={i}>• {e}</li>)}</ul>
        </div>
        <p className="text-xs text-muted mt-3">A lead is a question, not evidence that any stay was billed incorrectly.</p>
      </Card>
      <Card title="What the plan already knows about this hospital">
        {d.notes.length ? (
          <ul className="space-y-2 text-sm">{d.notes.map((n, i) => <li key={i}><span className="text-xs text-muted">{n.note_date} · {n.source}</span><div>{n.text}</div></li>)}</ul>
        ) : <p className="text-sm text-muted">No provider-relations notes on file.</p>}
      </Card>
      <Card title="Investigation">
        <p className="text-sm text-muted">{d.status === 'closed_no_findings' ? d.status_note
          : d.status_note ?? 'Not started. In this demo, the full investigation (explanations tested by the assistant, sensitivity, targeted sample) is built for the Riverside General DRG 871 lead.'}</p>
      </Card>
    </>
  )
}
