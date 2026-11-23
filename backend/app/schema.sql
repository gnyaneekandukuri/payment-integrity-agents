-- Payment integrity agents schema. All data is fictional.

CREATE TABLE hospitals (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    region TEXT NOT NULL,
    beds INTEGER NOT NULL,
    teaching INTEGER NOT NULL,
    referral_center INTEGER NOT NULL,
    peer_group TEXT NOT NULL,          -- 'subject' | 'A' (community) | 'B' (referral)
    base_rate REAL NOT NULL            -- approximate, illustrative
);

CREATE TABLE contracts (
    hospital_id TEXT PRIMARY KEY REFERENCES hospitals(id),
    sepsis_criteria TEXT NOT NULL,     -- 'Sepsis-3' | 'silent'
    summary TEXT NOT NULL
);

CREATE TABLE notes (
    id INTEGER PRIMARY KEY,
    hospital_id TEXT REFERENCES hospitals(id),
    source TEXT NOT NULL,
    note_date TEXT NOT NULL,
    text TEXT NOT NULL
);

CREATE TABLE drg_weights (
    drg TEXT PRIMARY KEY,
    title TEXT NOT NULL,               -- MS-DRG v43.0 titles
    weight REAL NOT NULL,              -- approximate, illustrative (not official FY2026 values)
    family TEXT NOT NULL
);

CREATE TABLE claims (
    id TEXT PRIMARY KEY,
    hospital_id TEXT NOT NULL REFERENCES hospitals(id),
    member_id TEXT NOT NULL,
    year INTEGER NOT NULL,
    quarter INTEGER NOT NULL,
    admit_date TEXT NOT NULL,
    discharge_date TEXT NOT NULL,
    los INTEGER NOT NULL,
    billed_drg TEXT NOT NULL REFERENCES drg_weights(drg),
    principal_dx TEXT NOT NULL,
    secondary_dx TEXT NOT NULL,        -- JSON list of {code, poa, desc}
    icu_days INTEGER NOT NULL,
    transfer_in INTEGER NOT NULL,
    discharge_status TEXT NOT NULL,
    paid_amount REAL NOT NULL,
    member_risk REAL NOT NULL,
    is_case INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX idx_claims_hosp_year ON claims(hospital_id, year);
CREATE INDEX idx_claims_drg ON claims(billed_drg);
CREATE INDEX idx_claims_member ON claims(member_id, hospital_id, admit_date);

CREATE TABLE cases (
    id TEXT PRIMARY KEY,
    claim_id TEXT NOT NULL REFERENCES claims(id),
    patient_name TEXT NOT NULL,
    age INTEGER NOT NULL,
    sex TEXT NOT NULL,
    source TEXT NOT NULL,              -- 'investigation_sample' | 'routine'
    source_detail TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'queued', -- 'ready' | 'awaiting_records' | 'in_review' | 'completed'
    assigned_to TEXT,
    due_date TEXT,
    review_origin TEXT,                -- data-mining rule | billing-pattern review | pre-payment rule | QA sample | appeal
    review_reason TEXT,
    review_concern TEXT,
    review_question TEXT,
    review_not_yours TEXT,
    review_context TEXT,
    in_queue INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE charts (
    id TEXT PRIMARY KEY,
    case_id TEXT NOT NULL REFERENCES cases(id),
    pdf_path TEXT NOT NULL,
    page_count INTEGER NOT NULL
);

CREATE TABLE chart_pages (
    chart_id TEXT NOT NULL REFERENCES charts(id),
    page INTEGER NOT NULL,
    section TEXT NOT NULL,
    text TEXT NOT NULL,
    PRIMARY KEY (chart_id, page)
);

CREATE TABLE answer_keys (
    case_id TEXT PRIMARY KEY REFERENCES cases(id),
    json TEXT NOT NULL                 -- our own test expectations, not clinical validation
);

-- ---- agent outputs (written only through validators) ----
CREATE TABLE agent_runs (
    id TEXT PRIMARY KEY,
    agent TEXT NOT NULL,               -- 'claim_review' | 'pattern_review'
    subject_id TEXT NOT NULL,          -- case id or question id
    model TEXT,
    mode TEXT NOT NULL,                -- 'live' | 'replay'
    status TEXT NOT NULL,
    started_at TEXT NOT NULL,
    finished_at TEXT,
    steps INTEGER DEFAULT 0,
    input_tokens INTEGER DEFAULT 0,
    output_tokens INTEGER DEFAULT 0,
    error TEXT
);

CREATE TABLE agent_steps (
    run_id TEXT NOT NULL REFERENCES agent_runs(id),
    n INTEGER NOT NULL,
    tool TEXT NOT NULL,
    args TEXT NOT NULL,
    result TEXT NOT NULL,
    accepted INTEGER NOT NULL,
    PRIMARY KEY (run_id, n)
);

CREATE TABLE evidence (
    id INTEGER PRIMARY KEY,
    run_id TEXT NOT NULL REFERENCES agent_runs(id),
    case_id TEXT NOT NULL REFERENCES cases(id),
    ref INTEGER NOT NULL,              -- E1, E2... numbered within the run (stable across replays)
    criterion TEXT NOT NULL,
    system TEXT,
    value TEXT,
    unit TEXT,
    observed_at TEXT,
    page INTEGER NOT NULL,
    quote TEXT NOT NULL,
    char_start INTEGER NOT NULL,
    char_end INTEGER NOT NULL,
    stance TEXT NOT NULL               -- 'supports' | 'contradicts' | 'context'
);

CREATE TABLE gaps (
    id INTEGER PRIMARY KEY,
    run_id TEXT NOT NULL REFERENCES agent_runs(id),
    case_id TEXT NOT NULL REFERENCES cases(id),
    kind TEXT NOT NULL,                -- 'missing' | 'conflicting' | 'coding_question'
    item TEXT NOT NULL,
    why_it_matters TEXT NOT NULL
);

CREATE TABLE sofa_results (
    run_id TEXT NOT NULL REFERENCES agent_runs(id),
    case_id TEXT NOT NULL REFERENCES cases(id),
    system TEXT NOT NULL,
    baseline INTEGER,
    worst INTEGER,
    change INTEGER,
    status TEXT NOT NULL,              -- 'scored' | 'not_documented' | 'baseline_uncertain' | 'not_formally_assessable'
    detail TEXT NOT NULL,
    evidence_ids TEXT NOT NULL,
    PRIMARY KEY (run_id, system)
);

CREATE TABLE drafts (
    id INTEGER PRIMARY KEY,
    run_id TEXT NOT NULL REFERENCES agent_runs(id),
    case_id TEXT NOT NULL REFERENCES cases(id),
    conclusion TEXT NOT NULL,          -- 'demonstrated' | 'not_demonstrated' | 'cannot_determine'
    rationale TEXT NOT NULL,
    sections TEXT,                     -- JSON {summary, documented, uncertain, would_resolve}
    evidence_ids TEXT NOT NULL,
    validator_result TEXT NOT NULL
);

CREATE TABLE review_actions (
    id INTEGER PRIMARY KEY,
    case_id TEXT NOT NULL REFERENCES cases(id),
    actor TEXT NOT NULL,
    action TEXT NOT NULL,
    before TEXT,
    after TEXT,
    reason TEXT,
    at TEXT NOT NULL
);

-- ---- Maya's flow ----
CREATE TABLE pattern_questions (
    id TEXT PRIMARY KEY,
    hospital_id TEXT NOT NULL REFERENCES hospitals(id),
    drg TEXT NOT NULL,
    metrics TEXT NOT NULL
);

CREATE TABLE explanations (
    id INTEGER PRIMARY KEY,
    question_id TEXT NOT NULL REFERENCES pattern_questions(id),
    run_id TEXT,
    name TEXT NOT NULL,
    status TEXT NOT NULL,              -- 'supported' | 'weakened' | 'unresolved'
    summary TEXT NOT NULL,
    citations TEXT NOT NULL,
    confirmed_by TEXT
);

CREATE TABLE samples (
    id TEXT PRIMARY KEY,
    question_id TEXT NOT NULL REFERENCES pattern_questions(id),
    claim_ids TEXT NOT NULL,
    rationale TEXT NOT NULL,
    approved INTEGER NOT NULL DEFAULT 0
);

-- ---- records follow-up requests (drafted by the assistant, approved by the reviewer; never sent in the demo) ----
CREATE TABLE records_requests (
    id INTEGER PRIMARY KEY,
    case_id TEXT NOT NULL REFERENCES cases(id),
    run_id TEXT,
    mode TEXT NOT NULL,                -- 'live' | 'replay' | 'template'
    status TEXT NOT NULL,              -- 'draft' | 'approved'
    items TEXT NOT NULL,               -- JSON list of {request, reason, pages}
    letter TEXT NOT NULL,
    created_at TEXT NOT NULL,
    approved_by TEXT,
    approved_at TEXT
);

-- ---- leads produced by the monitoring (detection) job ----
CREATE TABLE leads (
    id TEXT PRIMARY KEY,
    lead_type TEXT NOT NULL,           -- drg_shift | short_stays | readmissions
    hospital_id TEXT NOT NULL REFERENCES hospitals(id),
    title TEXT NOT NULL,
    measure TEXT NOT NULL,
    value REAL NOT NULL,
    peer_value REAL NOT NULL,
    earlier_value REAL,
    unit TEXT NOT NULL,
    stays INTEGER NOT NULL,
    rule TEXT NOT NULL,
    params TEXT NOT NULL,              -- JSON: what the detail page needs to recompute
    status TEXT NOT NULL,              -- new | in_analysis | records_requested | closed_no_findings
    status_note TEXT,
    flagged_on TEXT NOT NULL,
    question_id TEXT,                  -- set when a full investigation exists (Riverside)
    detected_by TEXT NOT NULL DEFAULT '[]',  -- JSON: rule | peer_profiling | change_detection
    evidence TEXT NOT NULL DEFAULT '[]'      -- JSON: one sentence per method
);
