// Owner: Nikki
// The uploaded image, beside what was read out of it.
//
// Extraction is a draft; the paper is the source. A doctor asked to accept
// findings they cannot check against the original is being asked to trust the
// model blindly, which no clinician would accept and this console should not
// require. The side-by-side is the whole point: image on the left, the
// extracted findings on the right, close enough to compare without scrolling.
//
// The image is fetched with the clinician's token — it is PHI behind an
// authenticated endpoint, so it cannot simply be an <img src> pointing at the
// API. It arrives as a blob, which is revoked on close.
//
// If it cannot be loaded, this says so in words. A broken-image icon on a
// clinical screen tells the doctor nothing about whether the document is
// missing, forbidden, or merely slow.

import { useCallback, useEffect, useRef, useState } from 'react';
import { fetchDocumentImage } from '../api/client.js';

const FOCUSABLE =
  'a[href], button:not([disabled]), input, select, textarea, [tabindex]:not([tabindex="-1"])';

export default function DocumentViewer({ doc, onClose }) {
  const [state, setState] = useState({ status: 'loading', url: null, error: '' });
  const [zoomed, setZoomed] = useState(false);
  const panel = useRef(null);
  const closeBtn = useRef(null);

  useEffect(() => {
    let revoked = null;
    let cancelled = false;
    setState({ status: 'loading', url: null, error: '' });
    fetchDocumentImage(doc.doc_id)
      .then((blob) => {
        if (cancelled) return;
        revoked = URL.createObjectURL(blob);
        setState({ status: 'ready', url: revoked, error: '' });
      })
      .catch((e) => {
        if (cancelled) return;
        setState({ status: 'error', url: null, error: e?.message || 'could not be loaded' });
      });
    return () => {
      cancelled = true;
      // The blob holds patient data in memory; let it go with the modal.
      if (revoked) URL.revokeObjectURL(revoked);
    };
  }, [doc.doc_id]);

  // Escape closes, and Tab is trapped: a modal the keyboard can wander out of
  // is one a screen-reader user cannot tell they are still inside.
  const onKeyDown = useCallback(
    (e) => {
      if (e.key === 'Escape') {
        e.stopPropagation();
        onClose();
        return;
      }
      if (e.key !== 'Tab') return;
      const items = panel.current?.querySelectorAll(FOCUSABLE);
      if (!items?.length) return;
      const first = items[0];
      const last = items[items.length - 1];
      if (e.shiftKey && document.activeElement === first) {
        e.preventDefault();
        last.focus();
      } else if (!e.shiftKey && document.activeElement === last) {
        e.preventDefault();
        first.focus();
      }
    },
    [onClose],
  );

  useEffect(() => {
    closeBtn.current?.focus();
  }, []);

  const findings = doc.findings || [];

  return (
    <div
      className="viewer"
      role="dialog"
      aria-modal="true"
      aria-label={doc.title || 'Uploaded document'}
      onKeyDown={onKeyDown}
      onMouseDown={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div className="viewer__panel" ref={panel}>
        <header className="viewer__head">
          <div>
            <h2 className="viewer__title">{doc.title || 'Uploaded document'}</h2>
            <p className="viewer__meta">
              {doc.date || doc.captured_at?.slice(0, 10) || '—'}
              {' · '}
              <span
                className={`viewer__by viewer__by--${
                  doc.uploaded_by === 'clinician' ? 'clinician' : 'patient'
                }`}
              >
                {doc.uploaded_by === 'clinician' ? 'Attached by clinician' : 'Uploaded by patient'}
              </span>
            </p>
          </div>
          <button type="button" className="viewer__close" onClick={onClose} ref={closeBtn}>
            Close
          </button>
        </header>

        <div className="viewer__body">
          <div className="viewer__image">
            {state.status === 'loading' ? <p className="viewer__note">Loading the image…</p> : null}
            {state.status === 'error' ? (
              // Said plainly. The doctor needs to know the original cannot be
              // checked, so they can decline to accept a reading on its own.
              <p className="viewer__note viewer__note--error">
                This image could not be loaded, so the extraction below cannot be checked against
                the original. {state.error}
              </p>
            ) : null}
            {state.status === 'ready' ? (
              <>
                <img
                  className={`viewer__img${zoomed ? ' viewer__img--zoom' : ''}`}
                  src={state.url}
                  alt={doc.title || 'Uploaded document'}
                  onClick={() => setZoomed((z) => !z)}
                />
                <div className="viewer__tools">
                  {/* Prescriptions are often small handwriting. */}
                  <button type="button" onClick={() => setZoomed((z) => !z)}>
                    {zoomed ? 'Fit to window' : 'Zoom in'}
                  </button>
                  <a href={state.url} target="_blank" rel="noreferrer">
                    Open full size
                  </a>
                </div>
              </>
            ) : null}
          </div>

          <div className="viewer__findings">
            <h3>What was read from it</h3>
            {findings.length ? (
              <ul>
                {findings.map((f, i) => (
                  <li
                    key={`${f.label}-${i}`}
                    className={f.out_of_range ? 'finding finding--flag' : 'finding'}
                  >
                    {/* A diagnosis carries the same text as label and value.
                        Printing both repeats the sentence. */}
                    {String(f.value) === String(f.label) ? null : (
                      <span className="finding__label">{f.label}</span>
                    )}
                    <span className="finding__value">
                      {f.value}
                      {f.unit ? ` ${f.unit}` : ''}
                      {/* Same red-and-icon treatment as the case view: an
                          out-of-range value must not read as a normal one
                          just because it moved into a modal. */}
                      {f.out_of_range ? <span className="finding__flag">▲</span> : null}
                    </span>
                    {/* `ref`, which is what DocumentFinding actually calls the
                        reference range. This read f.reference_range and so
                        silently showed no range on any finding — on the one
                        screen built for checking a value against its range. */}
                    {f.ref ? <span className="finding__range">({f.ref})</span> : null}
                  </li>
                ))}
              </ul>
            ) : (
              <p className="viewer__note">
                Nothing was extracted from this document. Read the image itself.
              </p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
