// Owner: Ranjith
// Screen 7. Photograph old prescriptions and reports.
//
// Uploads run in the background and their state is shown on the thumbnail.
// The patient is never blocked on a network call — OPD wifi is bad, and a
// spinner between them and the doctor is the worst possible failure here.

import { useCallback, useEffect, useRef, useState } from 'react';
import ScreenShell from '../components/ScreenShell.jsx';
import BigButton from '../components/BigButton.jsx';
import { Camera, Cross, Document } from '../components/Icons.jsx';
import { useT } from '../i18n/useT.js';
import { useSession, SCREENS } from '../state/SessionContext.jsx';
import { submitAnswer, uploadDocument } from '../api/client.js';

const JPEG_QUALITY = 0.85;

export default function Documents() {
  const { tx, lang } = useT();
  const { sessionId, documents, addDocument, updateDocument, removeDocument, go } = useSession();

  const [capturing, setCapturing] = useState(false);
  const [cameraError, setCameraError] = useState(false);

  const videoRef = useRef(null);
  const streamRef = useRef(null);

  const stopCamera = useCallback(() => {
    streamRef.current?.getTracks().forEach((track) => track.stop());
    streamRef.current = null;
  }, []);

  useEffect(() => stopCamera, [stopCamera]);

  // Answer the interview's `documents` stage from here, so it is asked once.
  // Fire and forget, like consent: the patient must never wait on the network
  // between themselves and the doctor.
  const answerNode = (value) => {
    submitAnswer(sessionId, { node_id: 'documents', value, text: '', lang })
      .catch((e) => console.warn('[documents] answer not recorded:', e));
  };

  const startCamera = async () => {
    answerNode('yes');
    setCapturing(true);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'environment' },
        audio: false,
      });
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        await videoRef.current.play();
      }
    } catch (e) {
      console.warn('[documents] camera unavailable:', e);
      setCameraError(true);
    }
  };

  const capture = () => {
    const video = videoRef.current;
    if (!video || !video.videoWidth) return;

    const canvas = document.createElement('canvas');
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    canvas.getContext('2d').drawImage(video, 0, 0);

    canvas.toBlob(
      (blob) => {
        if (!blob) return;
        const localId = `doc-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`;
        addDocument({ localId, url: URL.createObjectURL(blob), status: 'uploading' });

        uploadDocument(sessionId, blob, `${localId}.jpg`)
          .then((res) => updateDocument(localId, { status: 'done', documentId: res.document_id }))
          .catch((e) => {
            console.warn('[documents] upload failed:', e);
            // The photo stays in the list; staff can still see it on screen.
            updateDocument(localId, { status: 'failed' });
          });
      },
      'image/jpeg',
      JPEG_QUALITY,
    );
  };

  const finish = () => {
    stopCamera();
    go(SCREENS.CONFIRM);
  };

  const decline = () => {
    answerNode('no');
    finish();
  };

  /* ---------------------------------------------------------- ask first */

  if (!capturing) {
    return (
      <ScreenShell prompt={tx('documents.title')}>
        <div className="stack">
          <BigButton variant="primary" icon={Document} onClick={startCamera}>
            {tx('documents.yes').label}
          </BigButton>
          <BigButton variant="outline" onClick={decline}>
            {tx('documents.no').label}
          </BigButton>
        </div>
      </ScreenShell>
    );
  }

  /* ------------------------------------------------------ camera failed */

  if (cameraError) {
    return (
      <ScreenShell prompt={tx('documents.cameraBlocked')}>
        <BigButton variant="primary" center onClick={finish}>
          {tx('documents.done').label}
        </BigButton>
      </ScreenShell>
    );
  }

  /* ------------------------------------------------------------ capture */

  return (
    <ScreenShell prompt={tx('documents.cameraTitle')}>
      <div className="camera">
        <video ref={videoRef} playsInline muted />
        <div className="camera__guide" />
      </div>

      <button
        type="button"
        className="shutter"
        onClick={capture}
        aria-label={tx('documents.capture').label}
      >
        <Camera />
      </button>

      {documents.length ? (
        <div className="thumbs">
          {documents.map((doc) => (
            <div key={doc.localId} className="thumb">
              <img src={doc.url} alt="" />
              <button
                type="button"
                className="thumb__remove"
                onClick={() => removeDocument(doc.localId)}
                aria-label={tx('documents.remove').label}
              >
                <Cross />
              </button>
              <span className="thumb__status">
                {doc.status === 'uploading' ? '…' : doc.status === 'failed' ? '!' : '✓'}
              </span>
            </div>
          ))}
        </div>
      ) : null}

      <BigButton variant="primary" center onClick={finish} disabled={!documents.length}>
        {tx('documents.done').label}
      </BigButton>
    </ScreenShell>
  );
}
