// Owner: Ranjith
// Route /physician. Desktop, 1280px+, English only, information-dense.
//
// Everything the patient screens optimise for is inverted here: 16px type,
// two columns, tables, no audio, no icons-as-controls. This user is a literate
// doctor with about 90 seconds per patient.

import { useCallback, useEffect, useState } from 'react';
import EditableField from './EditableField.jsx';
import {
  confirmCase,
  fetchCase,
  fetchPatientList,
  rejectCase,
  updateCase,
} from '../api/client.js';
import './physician.css';

// Red flags must be legible without colour: on a projector, in greyscale, and
// to a colour-blind reader. Icon + word + colour, three independent signals.
function WarningIcon() {
  return (
    <svg viewBox="0 0 24 24" className="warn-icon" aria-hidden="true" focusable="false">
      <path
        d="M12 3 L22 20 H2 Z"
        fill="none"
        stroke="currentColor"
        strokeWidth="2.2"
        strokeLinejoin="round"
      />
      <path d="M12 9 v5" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" />
      <circle cx="12" cy="17.2" r="1.2" fill="currentColor" />
    </svg>
  );
}

// Which flat console keys the backend's low_confidence_fields map onto. The
// backend names extracted fields (symptom_site); the console renders clinical
// sections (hpi). Anything unmapped still hedges its own section if the name
// matches a section key directly.
const FIELD_TO_SECTION = {
  chief_complaint: 'chief_complaint',
  symptom_duration: 'hpi',
  symptom_site: 'hpi',
  symptom_onset: 'hpi',
  symptom_character: 'hpi',
  symptom_severity: 'hpi',
  symptom_radiation: 'hpi',
  symptom_timing: 'hpi',
  symptom_exacerbating_factors: 'hpi',
  symptom_relieving_factors: 'hpi',
  associated_symptoms: 'hpi',
  ros_screen: 'ros',
  past_medical_conditions: 'past_history',
  past_surgeries: 'past_history',
  current_medications: 'drugs_allergies',
  known_allergies: 'drugs_allergies',
  family_history: 'family',
  smoking_status: 'personal',
  alcohol_use: 'personal',
  diet: 'personal',
  sleep_pattern: 'personal',
  occupation: 'personal',
};

// Standard clinical reading order. Not alphabetical, not API order.
const SECTIONS = [
  { key: 'chief_complaint', title: 'Chief complaint' },
  { key: 'hpi', title: 'History of present illness' },
  { key: 'past_history', title: 'Past history' },
  { key: 'drugs_allergies', title: 'Drug & allergy' },
  { key: 'family', title: 'Family history' },
  { key: 'personal', title: 'Personal history' },
  { key: 'ros', title: 'Review of systems' },
];

export default function Physician({ auth, onSignOut }) {
  const [queue, setQueue] = useState([]);
  const [activeId, setActiveId] = useState(null);
  const [record, setRecord] = useState(null);
  const [status, setStatus] = useState('draft'); // draft | accepted | rejected
  const [busy, setBusy] = useState(false);
  const [note, setNote] = useState('');

  // Poll the queue. A doctor leaves this open; a patient who finishes intake
  // while they are reading a case must appear without a manual refresh, and a
  // red flag raised mid-read must climb to the top on its own.
  useEffect(() => {
    let cancelled = false;
    const load = () =>
      fetchPatientList()
        .then((list) => {
          if (cancelled) return;
          setQueue(list);
          // Only auto-select on first load; never yank the doctor off the case
          // they are reading because the queue re-ordered underneath them.
          setActiveId((cur) => cur ?? (list.length ? list[0].session_id : null));
        })
        .catch((e) => {
          // A 401 has already cleared the session; ProtectedRoute will swap in
          // the login screen. Nothing useful to show here.
          if (e?.name !== 'Unauthorized') console.error('[physician] queue failed:', e);
        });
    load();
    const id = setInterval(load, 10000);
    return () => {
      cancelled = true;
      clearInterval(id);
    };
  }, []);

  useEffect(() => {
    if (!activeId) return;
    setStatus('draft');
    setNote('');
    fetchCase(activeId)
      .then(setRecord)
      .catch((e) => {
        if (e?.name !== 'Unauthorized') console.error('[physician] case failed:', e);
      });
  }, [activeId]);

  const editField = useCallback(
    (key, value) => {
      setRecord((r) => ({ ...r, summary: { ...r.summary, [key]: value } }));
      // Local edit only until Accept. Persisted as a draft amendment.
      updateCase(activeId, { [key]: value }).catch((e) =>
        console.warn('[physician] draft not saved:', e),
      );
      setNote('Draft amended locally');
    },
    [activeId],
  );

  const accept = async () => {
    setBusy(true);
    try {
      await confirmCase(activeId);
      setStatus('accepted');
      setNote('Accepted — record written and released');
    } catch (e) {
      console.error('[physician] accept failed:', e);
      setNote('Accept failed — not written');
    } finally {
      setBusy(false);
    }
  };

  const reject = async () => {
    setBusy(true);
    try {
      await rejectCase(activeId, 'Rejected at console');
      setStatus('rejected');
      setNote('Rejected — nothing written');
    } catch (e) {
      console.error('[physician] reject failed:', e);
    } finally {
      setBusy(false);
    }
  };

  const summary = record?.summary ?? {};

  // Sections containing at least one low-confidence field, hedged the same way
  // the kiosk hedges them so the two screens never disagree about certainty.
  const lowConfidence = new Set(
    (record?.low_confidence_fields ?? [])
      .map((f) => FIELD_TO_SECTION[f] ?? f)
      .filter(Boolean),
  );
  const mocked = new Set(record?.mocked_fields ?? []);

  return (
    <div className="physician">
      <div
        className={`physician__banner ${
          status === 'accepted' ? 'physician__banner--accepted' : 'physician__banner--draft'
        }`}
      >
        {status === 'accepted'
          ? 'Verified — released to the record'
          : status === 'rejected'
            ? 'Rejected — nothing written'
            : 'Unverified draft — nothing is written until you press Accept'}
      </div>

      <div className="physician__whoami">
        <span>
          Signed in as <strong>{auth?.name ?? auth?.username ?? 'clinician'}</strong>
          {auth?.role ? ` · ${auth.role}` : ''}
        </span>
        <button type="button" className="physician__signout" onClick={() => onSignOut?.(false)}>
          Sign out
        </button>
      </div>

      <div className="physician__layout">
        <aside className="queue">
          <div className="queue__head">Waiting ({queue.length})</div>
          {queue.map((p) => (
            <button
              key={p.session_id}
              type="button"
              className={`queue__row${p.session_id === activeId ? ' queue__row--active' : ''}${
                p.red_flag ? ' queue__row--flag' : ''
              }`}
              onClick={() => setActiveId(p.session_id)}
            >
              <div className="queue__name">
                {p.token} · {p.name}
              </div>
              <div className="queue__meta">
                {p.age}/{p.sex} · {p.complaint}
              </div>
              {p.red_flag ? (
                <div className="queue__flag">
                  {/* Icon AND colour AND text. Colour alone is a WCAG failure
                      and washes out on a projector. */}
                  <WarningIcon />
                  <span>RED FLAG · {p.red_flag}</span>
                </div>
              ) : null}
            </button>
          ))}
          {queue.length === 0 ? (
            <p className="queue__empty">
              No completed intakes yet. Rows appear here as patients finish at the kiosk.
            </p>
          ) : null}
        </aside>

        {record ? (
          <main className="case">
            <header className="case__header">
              <span className="case__name">{record.patient.name}</span>
              <span className="case__meta">
                {record.patient.age}/{record.patient.sex} · ABHA {record.patient.abha ?? '—'} ·
                session {record.session_id}
              </span>
              {/* Say so on screen. Demographics are not collected for real yet,
                  and demo values must never be presented as patient data. */}
              {mocked.size ? (
                <span className="case__mocked" title={`Demo values: ${[...mocked].join(', ')}`}>
                  DEMO DATA · {[...mocked].join(', ')}
                </span>
              ) : null}
            </header>

            {/* Red flags, read live from the clinical record by the API — not
                from the stored summary snapshot. This block is why that
                matters: it is the view a doctor trusts, so it must never show
                fewer flags than the queue row they clicked. */}
            {(record.red_flags ?? []).length ? (
              <section className="flags" aria-label="Safety flags">
                {record.red_flags.map((f) => (
                  <div key={f.rule_id} className={`flags__row flags__row--${f.severity}`}>
                    <WarningIcon />
                    <span className="flags__severity">{f.severity}</span>
                    <span className="flags__label">{f.label}</span>
                  </div>
                ))}
              </section>
            ) : null}

            <div className="case__cols">
              {SECTIONS.map((s) => (
                <section className="section" key={s.key}>
                  <h2 className="section__title">
                    {s.title}
                    {lowConfidence.has(s.key) ? (
                      <span className="section__unsure" title="Extracted with low confidence">
                        ? low confidence
                      </span>
                    ) : null}
                  </h2>
                  <div className={lowConfidence.has(s.key) ? 'section__body--unsure' : undefined}>
                    <EditableField
                      value={summary[s.key]}
                      onCommit={(v) => editField(s.key, v)}
                      multiline={s.key !== 'chief_complaint'}
                    />
                  </div>
                </section>
              ))}

              <section className="section section--wide">
                <h2 className="section__title">Document timeline</h2>
                <table className="timeline">
                  <thead>
                    <tr>
                      <th>Date</th>
                      <th>Document</th>
                      <th>Findings</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(record.documents ?? []).map((doc) => (
                      <tr key={doc.id}>
                        <td className="timeline__date">{doc.date}</td>
                        <td>{doc.title}</td>
                        <td>
                          {(doc.findings ?? []).map((f) => (
                            <span
                              key={f.label}
                              className={`lab${f.out_of_range ? ' lab--out' : ''}`}
                            >
                              {f.label} {f.value}
                              {f.unit ? ` ${f.unit}` : ''}{' '}
                              <span className="lab__ref">({f.ref})</span>
                            </span>
                          ))}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </section>

              <section className="section section--wide fhir">
                <details>
                  <summary>View FHIR bundle</summary>
                  <pre>{JSON.stringify(record.fhir ?? {}, null, 2)}</pre>
                </details>
              </section>
            </div>

            <div className="actions">
              <button
                type="button"
                className="action action--accept"
                onClick={accept}
                disabled={busy || status === 'accepted'}
              >
                Accept
              </button>
              <button
                type="button"
                className="action"
                onClick={() => setNote('Edit any field inline, then press Accept')}
                disabled={busy}
              >
                Amend
              </button>
              <button
                type="button"
                className="action action--reject"
                onClick={reject}
                disabled={busy || status === 'rejected'}
              >
                Reject
              </button>
              <span className="actions__status">{note}</span>
            </div>
          </main>
        ) : (
          <div className="physician__empty">Select a patient.</div>
        )}
      </div>
    </div>
  );
}
