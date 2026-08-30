// Owner: Ranjith
// Seven dots, filled up to the current stage. No numbers, no percentages —
// a count is a reading task, a filled dot is not.

const TOTAL = 7;

export default function ProgressDots({ step }) {
  if (!step) return null;
  return (
    <div className="dots" role="img" aria-label={`Step ${step} of ${TOTAL}`}>
      {Array.from({ length: TOTAL }, (_, i) => (
        <span
          key={i}
          className={`dots__dot${i < step ? ' dots__dot--done' : ''}`}
        />
      ))}
    </div>
  );
}
