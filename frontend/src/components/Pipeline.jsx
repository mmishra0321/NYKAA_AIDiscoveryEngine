import {
  Brain,
  CheckCircle2,
  CloudDownload,
  Database,
  Filter,
  Search,
  Tags,
} from "lucide-react";

import SectionHeading from "./SectionHeading.jsx";

const ICONS = {
  ingest: CloudDownload,
  relevance: Filter,
  classify: Tags,
  index: Database,
  retrieve: Search,
  catalog: Brain,
};

function blurb(step) {
  const d = step.detail;
  if (typeof d === "string" && d) return d;
  if (!d || typeof d !== "object") return "Completed in this run";
  if (step.id === "ingest" && (d.records_saved != null || d.run_date)) {
    const when = d.run_date || "latest";
    return `${d.records_saved ?? "—"} saved · ${when}`;
  }
  if (step.id === "relevance" && d.wishlist_signal != null) {
    return `${d.wishlist_signal} wishlist signal · ${d.logistics_noise || 0} logistics`;
  }
  if (step.id === "classify" && d.classified != null) {
    return `${d.classified} classified into Q1–Q9`;
  }
  if (step.id === "index" && d.chunks != null) {
    return `${d.chunks} chunks indexed`;
  }
  if (step.id === "retrieve") {
    return `${d.with_hits ?? "—"} with hits · ${Array.isArray(d.gaps) ? d.gaps.length : d.gaps ?? "—"} gaps`;
  }
  if (step.id === "catalog") {
    return d.coverage === true ? "10/10 sections (gaps explicit)" : d.mode ? `Mode ${d.mode}` : "Catalog cached";
  }
  return "Completed in this run";
}

const FALLBACK = [
  { id: "ingest", label: "Ingest", detail: "Play Store + App Store" },
  { id: "relevance", label: "Relevance", detail: "Wishlist vs logistics noise" },
  { id: "classify", label: "Classify", detail: "Groq Q1–Q9" },
  { id: "index", label: "Index", detail: "MiniLM + Chroma" },
  { id: "retrieve", label: "Retrieve", detail: "Packs per question" },
  { id: "catalog", label: "Catalog", detail: "JSON + Markdown" },
];

export default function Pipeline({ summary }) {
  const steps = summary?.steps?.length ? summary.steps : FALLBACK;
  return (
    <section id="pipeline">
      <SectionHeading
        title="Discovery pipeline"
        subtitle="Ingest → relevance → classify → index → retrieve → catalog"
        action={
          summary?.run_date ? (
            <a href="#research" className="text-sm font-bold text-pink hover:underline">
              Run {summary.run_date} · view research Qs
            </a>
          ) : null
        }
      />
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6">
        {steps.map((step) => {
          const Icon = ICONS[step.id] || Tags;
          return (
            <article
              key={step.id}
              className="research-card-shine relative overflow-hidden rounded-xl border border-hairline bg-surface p-4"
            >
              <div className="mb-3 flex items-start justify-between">
                <div className="flex size-10 items-center justify-center rounded-xl bg-search text-pink">
                  <Icon className="size-5" strokeWidth={1.75} />
                </div>
                <CheckCircle2 className="size-4 text-pink" strokeWidth={2.25} />
              </div>
              <h3 className="font-ui text-sm font-bold text-ink">{step.label || step.title}</h3>
              <p className="mt-1 text-xs font-medium leading-relaxed text-ink/70">{blurb(step)}</p>
            </article>
          );
        })}
      </div>
    </section>
  );
}
