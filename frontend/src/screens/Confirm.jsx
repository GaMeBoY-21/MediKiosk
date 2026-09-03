// Owner: Ranjith
// Screen 8. Read the collected history back, with the same text on screen.
// Each item can be jumped back to and re-answered.
//
// This is the patient's only chance to catch a mis-heard answer, so it has to
// show EVERY answer they gave. It used to show two rows for a ten-question
// interview: the session store deduplicated answers by node_id, and every
// follow-up in the history stage carries node_id "hpi", so each new answer
// overwrote the last. The identity screens never recorded an answer at all.
// Both are fixed at the source; this screen now renders what it is given.

import { useEffect, useState } from 'react';
import ScreenShell from '../components/ScreenShell.jsx';
import BigButton from '../components/BigButton.jsx';
import { Pencil } from '../components/Icons.jsx';
import { useT } from '../i18n/useT.js';
import { useSession, SCREENS } from '../state/SessionContext.jsx';
import { generateSummary, submitAnswer } from '../api/client.js';
import BilingualText from '../components/BilingualText.jsx';
import { fieldLabel, valueLabel } from '../i18n/fieldNames.js';

/** What a field should read as on screen, in the patient's language. */
function shown(field, lang) {
  if (!field) return '';
  const own = valueLabel(field.name, field.value, lang);
  if (own) return own;
  if (field.display) return field.display;
  const v = field.value;
  if (Array.isArray(v)) return v.map((x) => String(x).replace(/_/g, ' ')).join(', ');
  if (typeof v === 'boolean') return v ? '✓' : '—';
  return String(v ?? '').replace(/_/g, ' ');
}

export default function Confirm() {
  const { tx, lang } = useT();
  const { sessionId, answers, extracted, setCurrentNode, setSummary, go } = useSession();
  const [saving, setSaving] = useState(false);

  const byName = new Map((extracted || []).map((f) => [f.name, f]));

  // Which fields each row accounts for, exposed for the layout/coverage
  // harness. Reading it off the DOM is not possible — a derived field that
  // reads the same as its source is deliberately not printed — and this
  // invariant is the one that keeps breaking, so it needs to be checkable.
  if (typeof window !== 'undefined') {
    window.__rowFields = answers.map((a) => ({
      key: a.key || `${a.node_id}:${a.question}`,
      fields: a.fields || [],
    }));
  }

  // Fields this answer filled that are not simply a restatement of it. A
  // reconciled field usually carries the SAME value as the answer it came from
  // (symptom_onset from symptom_duration), and repeating it would read as the
  // kiosk having recorded something twice. Anything genuinely different is
  // shown under the answer it was derived from — never as a row of its own,
  // which is a question the patient was never asked.
  const derivedFor = (a) =>
    (a.fields || [])
      .map((name) => byName.get(name))
      .filter((f) => f && shown(f, lang) && shown(f, lang) !== a.text);

  const spoken = answers.map((a) => `${a.question} ${a.text}`).join('. ');
  const readback = tx('confirm.title');

  // Warm the summary while the patient is still reading, so pressing
  // "Yes, this is correct" feels instant.
  useEffect(() => {
    generateSummary(sessionId)
      .then(setSummary)
      .catch((e) => console.warn('[confirm] summary not ready:', e));
  }, [sessionId, setSummary]);

  const editAnswer = (answer) => {
    // An identity answer belongs to its own screen, not to the interview loop.
    if (answer.screen) {
      go(answer.screen);
      return;
    }
    // TODO: re-entry rebuilds a minimal node, so the option tiles for that
    // question are lost and it falls back to voice. Needs a GET /interview/
    // {session}/node/{id} on the backend to restore options.
    setCurrentNode({ node_id: answer.node_id, question: answer.question, options: [] });
    go(SCREENS.INTERVIEW);
  };

  const accept = async () => {
    setSaving(true);
    // This screen IS the interview's `confirm` stage. Answering it here is what
    // stops the kiosk asking "is everything correct?" as a question and then
    // showing this screen asking the same thing. Fire and forget: the summary
    // is already warm and the patient should not wait on the network.
    submitAnswer(sessionId, { node_id: 'confirm', value: 'yes', text: '', lang })
      .catch((e) => console.warn('[confirm] confirmation not recorded:', e));
    go(SCREENS.DONE);
  };

  return (
    <ScreenShell
      prompt={{ label: readback.label, audio: `${readback.audio} ${spoken}` }}
      repeatAudio={`${readback.audio} ${spoken}`}
    >
      {answers.length ? (
        <div className="readback">
          {answers.map((a) => {
            // Keyed by question, not node_id: an interview stage asks many
            // questions and they all share one node id.
            const key = a.key || `${a.node_id}:${a.question}`;
            const extra = derivedFor(a);
            return (
              <div key={key} className="readback__item">
                <div className="readback__text">
                  <BilingualText className="readback__q" english={a.question_en}>
                    {a.question}
                  </BilingualText>
                  <BilingualText as="strong" className="readback__a" english={a.text_en}>
                    {a.text}
                  </BilingualText>
                  {extra.length ? (
                    <p className="readback__derived">
                      {extra
                        .map((f) => `${fieldLabel(f.name, lang)}: ${shown(f, lang)}`)
                        .join('   ')}
                    </p>
                  ) : null}
                </div>
                <button
                  type="button"
                  className="readback__edit"
                  onClick={() => editAnswer(a)}
                  aria-label={`${tx('common.edit').label}: ${a.question}`}
                >
                  <Pencil />
                </button>
              </div>
            );
          })}
        </div>
      ) : (
        <BilingualText as="p" className="shell__caption">{tx('confirm.nothing').label}</BilingualText>
      )}

      <BigButton variant="primary" center onClick={accept} disabled={saving}>
        {tx('confirm.correct').label}
      </BigButton>
    </ScreenShell>
  );
}
