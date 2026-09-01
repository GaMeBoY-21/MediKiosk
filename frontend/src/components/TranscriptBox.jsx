// Owner: Ranjith
// The answer box. Typeable, always, on every question.
//
// It used to be a read-only display of what the mic heard, which meant an
// open-ended question rendered a mic and nothing else: a patient who cannot
// speak clearly, or who is standing in a noisy OPD where recognition simply
// fails, had no way to answer at all. The problem statement requires every
// question to be answerable by speaking OR tapping, and this is the tapping
// path for questions that have no tiles.
//
// Speech writes into the same box, so a mis-heard word can be corrected by
// hand rather than by saying the whole sentence again. Interim words stay in
// grey underneath — the colour change is what tells the patient the machine
// has committed to what it heard, and a textarea cannot show two colours at
// once.

export default function TranscriptBox({
  value,
  interim,
  onChange,
  placeholder,
  ariaLabel,
  autoFocus = false,
}) {
  return (
    <div className="transcript">
      <textarea
        className="transcript__input"
        value={value ?? ''}
        onChange={(e) => onChange?.(e.target.value)}
        placeholder={placeholder}
        aria-label={ariaLabel || placeholder}
        rows={2}
        autoFocus={autoFocus}
        // Kiosk keyboards: no autocorrect mangling a symptom, no auto-capital
        // fighting a lowercase clinical term.
        autoCorrect="off"
        autoCapitalize="sentences"
        spellCheck={false}
      />
      {interim ? (
        <p className="transcript__interim" aria-live="polite">
          {interim}
        </p>
      ) : null}
    </div>
  );
}
