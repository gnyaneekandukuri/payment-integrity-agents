import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api, CONCLUSION_LABEL, STATUS_LABEL, type QueueItem } from '../api'
import { Badge, Card, conclusionTone, statusTone } from '../components/ui'

export const ORIGIN_TONE: Record<string, string> = {
  'Billing-pattern review': 'violet', 'Data-mining rule': 'blue', 'Pre-payment rule': 'amber',
  'Quality-assurance sample': 'gray', 'Appeal': 'red',
}

export default function Queue() {
  const [items, setItems] = useState<QueueItem[] | null>(null)
  const [error, setError] = useState('')
  useEffect(() => { api.queue().then(setItems).catch(e => setError(String(e.message))) }, [])

  const counts = (items ?? []).reduce<Record<string, number>>((acc, i) => { acc[i.status] = (acc[i.status] ?? 0) + 1; return acc }, {})

  return (
    <div className="space-y-5">
      <div className="flex items-end justify-between">
        <div>
          <h1 className="text-xl font-semibold">My clinical review queue</h1>
          <p className="text-sm text-muted mt-1">Inpatient claims selected for clinical validation. The assistant prepares the evidence; you decide.</p>
        </div>
        <div className="flex gap-2 text-xs">
          {['ready', 'in_review', 'awaiting_records', 'completed'].map(s => (
            <Badge key={s} tone={statusTone(s)}>{STATUS_LABEL[s]}: {counts[s] ?? 0}</Badge>
          ))}
        </div>
      </div>

      {error && <div className="text-sm text-rose-700">Could not load the queue: {error}</div>}

      <Card>
        <div className="-m-4 overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="text-left text-xs uppercase tracking-wide text-muted bg-gray-50">
              <tr>
                <th className="px-4 py-2.5 font-medium">Patient</th>
                <th className="px-4 py-2.5 font-medium">Hospital</th>
                <th className="px-4 py-2.5 font-medium">Billed DRG</th>
                <th className="px-4 py-2.5 font-medium">Review reason</th>
                <th className="px-4 py-2.5 font-medium">Status</th>
                <th className="px-4 py-2.5 font-medium">Assistant draft</th>
                <th className="px-4 py-2.5 font-medium">Due</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-line">
              {(items ?? []).map(i => (
                <tr key={i.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3">
                    <Link to={`/cases/${i.id}`} className="font-medium text-brand hover:underline">{i.patient_name}</Link>
                    <div className="text-xs text-muted">{i.age}{i.sex} · {i.claim_id}</div>
                  </td>
                  <td className="px-4 py-3">{i.hospital}</td>
                  <td className="px-4 py-3">
                    <div className="font-medium">{i.billed_drg}</div>
                    <div className="text-xs text-muted max-w-56 truncate" title={i.drg_title}>{i.drg_title}</div>
                  </td>
                  <td className="px-4 py-3">
                    <Badge tone={ORIGIN_TONE[i.review_origin ?? ''] ?? 'gray'}>{i.review_origin ?? 'Review'}</Badge>
                    <div className="text-xs text-muted mt-1 max-w-md">{i.review_reason ?? i.source_detail}</div>
                  </td>
                  <td className="px-4 py-3"><Badge tone={statusTone(i.status)}>{STATUS_LABEL[i.status] ?? i.status}</Badge></td>
                  <td className="px-4 py-3">
                    {i.draft_conclusion ? <Badge tone={conclusionTone(i.draft_conclusion)}>{CONCLUSION_LABEL[i.draft_conclusion]}</Badge>
                      : <span className="text-xs text-muted">{i.has_records ? 'Not run yet' : 'No records yet'}</span>}
                  </td>
                  <td className="px-4 py-3 text-xs whitespace-nowrap">{i.due_date}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {items === null && !error && <div className="p-6 text-sm text-muted">Loading…</div>}
        </div>
      </Card>
    </div>
  )
}
