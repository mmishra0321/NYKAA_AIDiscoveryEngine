import ThemeCard from "./ThemeCard.jsx";
import { TAXONOMY } from "../taxonomy.js";

function reviewsLabel(item, questions) {
  const n = (questions || [])
    .filter((q) => item.questions.includes(q.id))
    .reduce((sum, q) => sum + (q.evidence_count || 0), 0);
  return `${n} REVIEWS`;
}

export default function Themes({ questions, selectedId, onSelect }) {
  return (
    <section id="themes">
      <div className="mb-4">
        <h2 className="font-ui text-lg font-semibold tracking-tight text-ink">Discovery theme taxonomy</h2>
        <p className="mt-0.5 text-xs text-muted">
          Click a theme to highlight related research questions — same interaction as the last discovery agent
        </p>
      </div>
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
        {TAXONOMY.map((theme) => (
          <ThemeCard
            key={theme.id}
            title={theme.title}
            description={theme.description}
            icon={theme.icon}
            reviewsLabel={reviewsLabel(theme, questions)}
            selected={selectedId === theme.id}
            onSelect={() => onSelect(theme.id)}
          />
        ))}
      </div>
    </section>
  );
}
