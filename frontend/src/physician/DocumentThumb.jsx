// Owner: Nikki
// A small preview of the uploaded page, inside the View control.
//
// The endpoint needs the clinician's token, so this cannot be a plain <img
// src>; the bytes come back as a blob and the object URL is revoked when the
// row unmounts. Failure is silent HERE and only here: a thumbnail that cannot
// load falls back to a label rather than a broken-image icon, and the viewer
// behind it explains what went wrong in words when the doctor opens it.

import { useEffect, useState } from 'react';
import { fetchDocumentImage } from '../api/client.js';

export default function DocumentThumb({ docId }) {
  const [url, setUrl] = useState(null);

  useEffect(() => {
    let made = null;
    let cancelled = false;
    fetchDocumentImage(docId)
      .then((blob) => {
        if (cancelled) return;
        made = URL.createObjectURL(blob);
        setUrl(made);
      })
      .catch(() => {
        /* The viewer reports it properly; a thumbnail says nothing useful. */
      });
    return () => {
      cancelled = true;
      if (made) URL.revokeObjectURL(made);
    };
  }, [docId]);

  if (!url) return <span className="thumb thumb--empty" aria-hidden="true" />;
  return <img className="thumb" src={url} alt="" />;
}
