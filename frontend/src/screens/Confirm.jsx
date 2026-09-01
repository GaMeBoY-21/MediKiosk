// Owner: Ranjith
// Screen 8. Read the collected history back as plain spoken sentences, with
// the same text on screen. Each item can be jumped back to and re-answered.
//
// This is the patient's only chance to catch a mis-heard answer, so the whole
// readback plays automatically and can be replayed from the bottom bar.

import { useEffect, useState } from 'react';
import ScreenShell from '../components/ScreenShell.jsx';
import BigButton from '../components/BigButton.jsx';
import { Pencil } from '../components/Icons.jsx';
import { useT } from '../i18n/useT.js';
import { useSession, SCREENS } from '../state/SessionContext.jsx';
import { generateSummary, submitAnswer } from '../api/client.js';
import BilingualText from '../components/BilingualText.jsx';

export default function Confirm() {
  const { tx, lang } = useT();
  const { sessionId, answers, setCurrentNode, setSummary, go } = useSession();
  const [saving, setSaving] = useState(false);

  const spoken = answers.map((a) => `${a.question} ${a.text}`).join('. ');
  const readback = tx('confirm.title');

  // Warm the summary while the patient is still listening, so pressing
  // "Yes, this is correct" feels instant.
  useEffect(() => {
    generateSummary(sessionId)
      .then(setSummary)
      .catch((e) => console.warn('[confirm] summary not ready:', e));
  }, [sessionId, setSummary]);

  const editAnswer = (answer) => {
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
          {answers.map((a) => (
            <div key={a.node_id} className="readback__item">
              <div className="readback__text">
                <div>{a.question}</div>
                <strong>{a.text}</strong>
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
          ))}
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
