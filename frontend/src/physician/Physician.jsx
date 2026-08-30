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

export default function Physician() {
  const [queue, setQueue] = useState([]);
  const [activeId, setActiveId] = useState(null);
  const [record, setRecord] = useState(null);
  const [status, setStatus] = useState('draft'); // draft | accepted | rejected
  const [busy, setBusy] = useState(false);
  const [note, setNote] = useState('');

  useEffect(() => {
    fetchPatientList()
      .then((list) => {
        setQueue(list);
        if (list.length) setActiveId(list[0].session_id);
      })
      .catch((e) => console.error('[physician] queue failed:', e));
  }, []);

  useEffect(() => {
    if (!activeId) return;
    setStatus('draft');
    setNote('');
    fetchCase(activeId)
      .then(setRecord)
      .catch((e) => console.error('[physician] case failed:', e));
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
              {p.red_flag ? <div className="queue__flag">RED FLAG · {p.red_flag}</div> : null}
            </button>
          ))}
        </aside>

        {record ? (
          <main className="case">
            <header className="case__header">
              <span className="case__name">{record.patient.name}</span>
              <span className="case__meta">
                {record.patient.age}/{record.patient.sex} · ABHA {record.patient.abha ?? '—'} ·
                session {record.session_id}
              </span>
            </header>

            <div className="case__cols">
              {SECTIONS.map((s) => (
                <section className="section" key={s.key}>
                  <h2 className="section__title">{s.title}</h2>
                  <EditableField
                    value={summary[s.key]}
                    onCommit={(v) => editField(s.key, v)}
                    multiline={s.key !== 'chief_complaint'}
                  />
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
