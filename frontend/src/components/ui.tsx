import type { ReactNode } from 'react'
import { Link, useLocation } from 'react-router-dom'

const PEOPLE = {
  sam: { name: 'Sam Okoro', role: 'Clinical reviewer (RN)', initials: 'SO', area: 'Clinical review assistant' },
  maya: { name: 'Maya Chen', role: 'Payment integrity analyst', initials: 'MC', area: 'Lead investigation assistant' },
}

export function Shell({ children }: { children: ReactNode }) {
  const { pathname } = useLocation()
  const onPatterns = pathname.startsWith('/leads') || pathname.startsWith('/patterns')
  const who = onPatterns ? PEOPLE.maya : PEOPLE.sam
  const item = (active: boolean) => `block rounded-md px-3 py-2 ${active ? 'bg-white/10' : 'text-white/75 hover:bg-white/5'}`
  return (
    <div className="min-h-screen flex">
      <aside className="w-56 shrink-0 bg-brand text-white flex flex-col">
        <div className="px-5 py-5 border-b border-white/10">
          <div className="text-[11px] uppercase tracking-wider text-white/60">Northstar Health Plan</div>
          <div className="font-semibold leading-tight mt-0.5">Payment Integrity</div>
        </div>
        <nav className="px-3 py-4 text-sm space-y-1">
          <Link to="/leads" className={item(onPatterns)}>Leads<span className="block text-[10px] text-white/50">Maya Chen, analyst</span></Link>
          <Link to="/" className={item(!onPatterns)}>Clinical review queue<span className="block text-[10px] text-white/50">Sam Okoro, reviewer</span></Link>
        </nav>
        <div className="mt-auto px-5 py-4 text-[11px] text-white/55 border-t border-white/10">
          Fictional data for demonstration. Not medical or billing advice.
        </div>
      </aside>
      <div className="flex-1 min-w-0 flex flex-col">
        <header className="h-14 bg-white border-b border-line flex items-center justify-between px-6">
          <div className="text-sm text-muted">{who.area}</div>
          <div className="flex items-center gap-3 text-sm">
            <div className="text-right leading-tight">
              <div className="font-medium">{who.name}</div>
              <div className="text-xs text-muted">{who.role}</div>
            </div>
            <div className="h-8 w-8 rounded-full bg-brand-soft text-brand grid place-items-center font-semibold text-xs">{who.initials}</div>
          </div>
        </header>
        <main className="flex-1 min-w-0 p-6">{children}</main>
      </div>
    </div>
  )
}

export function Card({ title, right, children, className = '' }: { title?: ReactNode; right?: ReactNode; children: ReactNode; className?: string }) {
  return (
    <section className={`bg-white border border-line rounded-lg ${className}`}>
      {title && (
        <div className="flex items-center justify-between px-4 py-3 border-b border-line">
          <h2 className="text-sm font-semibold">{title}</h2>
          {right}
        </div>
      )}
      <div className="p-4">{children}</div>
    </section>
  )
}

const TONES: Record<string, string> = {
  green: 'bg-emerald-50 text-emerald-800 ring-emerald-200',
  amber: 'bg-amber-50 text-amber-800 ring-amber-200',
  red: 'bg-rose-50 text-rose-800 ring-rose-200',
  blue: 'bg-sky-50 text-sky-800 ring-sky-200',
  gray: 'bg-gray-50 text-gray-700 ring-gray-200',
  violet: 'bg-violet-50 text-violet-800 ring-violet-200',
}

export function Badge({ tone = 'gray', children }: { tone?: keyof typeof TONES | string; children: ReactNode }) {
  return <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ring-1 ring-inset ${TONES[tone] ?? TONES.gray}`}>{children}</span>
}

export const conclusionTone = (c?: string | null) =>
  c === 'demonstrated' ? 'green' : c === 'not_demonstrated' ? 'blue' : c === 'cannot_determine' ? 'amber' : 'gray'

export const statusTone = (s: string) =>
  ({ ready: 'blue', in_review: 'violet', awaiting_records: 'amber', completed: 'gray', reviewed: 'green', escalated: 'red', sent_to_coder: 'green' } as Record<string, string>)[s] ?? 'gray'

export function Button({ children, onClick, variant = 'primary', disabled, type = 'button' }:
  { children: ReactNode; onClick?: () => void; variant?: 'primary' | 'secondary' | 'ghost'; disabled?: boolean; type?: 'button' | 'submit' }) {
  const base = 'inline-flex items-center gap-1.5 rounded-md px-3 py-1.5 text-sm font-medium transition disabled:opacity-50 disabled:cursor-not-allowed'
  const style = variant === 'primary' ? 'bg-brand text-white hover:bg-brand/90'
    : variant === 'secondary' ? 'bg-white text-ink ring-1 ring-inset ring-line hover:bg-gray-50' : 'text-brand hover:bg-brand-soft'
  return <button type={type} className={`${base} ${style}`} onClick={onClick} disabled={disabled}>{children}</button>
}
