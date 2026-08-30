import { ChevronRight } from "lucide-react";
import { QUESTION_BADGES } from "../taxonomy.js";

const TONES = {
  pink: "bg-pink/10 text-pink",
  peach: "bg-peach/40 text-ink",
  ink: "bg-search text-ink",
};

export default function InsightCard({ id, question, summary, evidence_count, themes_count, data_gaps, onSelect }) {
  const meta = QUESTION_BADGES[id] || { badge: id, tone: "pink" };
  const preview = (summary || "").slice(0, 160);
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
      <h3 className="font-ui text-[15px] font-semibold leading-snug text-ink">{question}</h3>
      <p className="mt-2 flex-1 text-sm leading-relaxed text-muted">
        {preview}
        {summary && summary.length > 160 ? "…" : ""}
      </p>
      <p className="mt-4 text-[11px] text-muted">
        {evidence_count || 0} related reviews
        {themes_count ? ` · ${themes_count} sub-themes` : data_gaps ? " · data gap" : ""} · click for full answer
      </p>
    </button>
  );
}
