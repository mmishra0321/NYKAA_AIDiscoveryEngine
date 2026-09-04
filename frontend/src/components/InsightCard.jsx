import { ChevronRight } from "lucide-react";
import { QUESTION_BADGES } from "../taxonomy.js";
import { cleanCopy, firstComment } from "../copy.js";

const TONES = {
  pink: "bg-pink/10 text-pink",
  peach: "bg-peach/40 text-ink",
  ink: "bg-search text-ink",
};

export default function InsightCard({
  id,
  question,
  summary,
  evidence_count,
  themes_count,
  data_gaps,
  sub_themes,
  onSelect,
}) {
  const meta = QUESTION_BADGES[id] || { badge: id, tone: "pink" };
  const preview = firstComment({ summary, sub_themes }) || cleanCopy(summary);
  const clipped = preview.length > 180 ? `${preview.slice(0, 180)}…` : preview;
  return (
    <button
      type="button"
      onClick={() => onSelect?.(id)}
      className="group research-card-shine relative flex w-full flex-col overflow-hidden rounded-xl border border-hairline bg-surface p-5 text-left transition hover:border-pink/40"
    >
      <div className="mb-3 flex items-center justify-between gap-2">
        <span className={`rounded-md px-2 py-0.5 text-[10px] font-bold tracking-wider uppercase ${TONES[meta.tone] || TONES.pink}`}>
          {meta.badge}
        </span>
        <ChevronRight className="size-4 text-muted transition group-hover:text-pink" />
      </div>
      <h3 className="font-ui text-base font-bold leading-snug text-ink sm:text-[17px]">{question}</h3>
      <p className="mt-3 flex-1 text-[15px] font-medium leading-relaxed text-ink/85">{clipped}</p>
      <p className="mt-4 text-[12px] font-semibold text-muted">
        {evidence_count || 0} related reviews
        {themes_count ? ` · ${themes_count} sub-themes` : data_gaps ? " · data gap" : ""} · click for full answer
      </p>
    </button>
  );
}
