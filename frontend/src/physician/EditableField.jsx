// Owner: Ranjith
// Click to edit, blur to commit, Escape to abandon. Every field on the console
// is one of these — the doctor corrects the machine, not the other way round.

import { useEffect, useRef, useState } from 'react';

export default function EditableField({ value, onCommit, placeholder = 'Not recorded', multiline = true }) {
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState(value ?? '');
  const ref = useRef(null);

  useEffect(() => setDraft(value ?? ''), [value]);

  useEffect(() => {
    if (editing && ref.current) {
      ref.current.focus();
      ref.current.select?.();
    }
  }, [editing]);

  const commit = () => {
    setEditing(false);
    if (draft !== value) onCommit(draft);
  };

  const onKeyDown = (e) => {
    if (e.key === 'Escape') {
      setDraft(value ?? '');
      setEditing(false);
    }
    if (e.key === 'Enter' && (!multiline || e.metaKey || e.ctrlKey)) {
      e.preventDefault();
      commit();
    }
  };

  if (editing) {
    const Tag = multiline ? 'textarea' : 'input';
    return (
      <Tag
        ref={ref}
        className="field__input"
        value={draft}
        rows={multiline ? Math.max(2, String(draft).split('\n').length) : undefined}
        onChange={(e) => setDraft(e.target.value)}
        onBlur={commit}
        onKeyDown={onKeyDown}
      />
    );
  }

  return (
    <button
      type="button"
      className={`field${value ? '' : ' field--empty'}`}
      onClick={() => setEditing(true)}
    >
      {value || placeholder}
    </button>
  );
}
