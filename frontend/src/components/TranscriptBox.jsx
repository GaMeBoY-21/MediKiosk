// Owner: Ranjith
// Live transcript. Interim words in grey, settled words in black — the colour
// change is what tells the patient the machine has committed to what it heard.

export default function TranscriptBox({ final, interim, placeholder }) {
  const empty = !final && !interim;
  return (
    <div className="transcript" aria-live="polite">
      {empty ? (
        <span className="transcript__placeholder">{placeholder}</span>
      ) : (
        <>
          <span className="transcript__final">{final}</span>
          {interim ? <span className="transcript__interim">{final ? ' ' : ''}{interim}</span> : null}
        </>
      )}
    </div>
  );
}
