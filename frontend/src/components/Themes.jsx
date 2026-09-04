import ThemeCard from "./ThemeCard.jsx";
import { TAXONOMY } from "../taxonomy.js";
import SectionHeading from "./SectionHeading.jsx";

function reviewsLabel(item, questions) {
  const n = (questions || [])
    .filter((q) => item.questions.includes(q.id))
    .reduce((sum, q) => sum + (q.evidence_count || 0), 0);
  return `${n} REVIEWS`;
}

export default function Themes({ questions, selectedId, onSelect }) {
  return (
    <section id="themes">
      <SectionHeading
        title="Discovery theme taxonomy"
        subtitle="Click a theme to highlight related research questions"
      />
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
