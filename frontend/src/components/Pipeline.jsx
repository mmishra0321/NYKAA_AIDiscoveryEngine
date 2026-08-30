function blurb(step) {
  const d = step.detail;
  if (typeof d === "string" && d) return d;
  if (!d || typeof d !== "object") return "Completed in this run";
  if (step.id === "relevance" && d.wishlist_signal != null) {
    return `${d.wishlist_signal} wishlist signal · ${d.logistics_noise || 0} logistics · ${d.other || 0} other`;
  }
  if (step.id === "classify" && d.classified != null) {
    return `${d.classified} classified · ${d.mode || "stub"}`;
  }
  if (step.id === "index" && (d.chunks != null || d.collection)) {
    const bits = [];
    if (d.chunks != null) bits.push(`${d.chunks} chunks`);
    if (d.collection) bits.push(d.collection);
    return bits.join(" · ") || "Index summary not on this host";
  }
  if (step.id === "retrieve") {
    const gaps = Array.isArray(d.gaps) ? d.gaps.length : d.gaps;
    if (d.with_hits != null || gaps != null) {
      return `${d.with_hits ?? "—"} with hits · ${gaps ?? "—"} gaps`;
    }
  }
  if (step.id === "catalog") {
    if (d.coverage === true) return "10/10 sections (gaps explicit where thin)";
    if (d.coverage === false) return "Incomplete coverage";
    if (d.mode) return `Mode ${d.mode}`;
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
    <section id="pipeline" className="border-t border-hairline bg-surface">
      <div className="mx-auto max-w-6xl px-4 py-16 md:px-8">
        <p className="text-[11px] font-semibold uppercase tracking-[0.2em] text-pink">How this ran</p>
        <h2 className="mt-2 font-ui text-2xl font-semibold text-ink">From public text to ranked hypotheses</h2>
        <p className="mt-2 max-w-xl text-muted">
          One pass: gather Fashion-only reviews, drop delivery rage, classify into ten questions, then quantify.
        </p>
        <ol className="mt-10 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {steps.map((step, i) => (
            <li key={step.id || i} className="border-t border-hairline pt-4">
              <span className="text-xs font-semibold text-pink">{String(i + 1).padStart(2, "0")}</span>
              <h3 className="mt-1 text-lg font-medium text-ink">{step.label}</h3>
              <p className="mt-1 text-sm text-muted">{blurb(step)}</p>
            </li>
          ))}
        </ol>
      </div>
    </section>
  );
}
