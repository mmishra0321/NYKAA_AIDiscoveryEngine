import { useEffect, useState } from "react";
import { X } from "lucide-react";

function collectQuotes(detail) {
  const seen = new Set();
  const out = [];
  for (const theme of detail?.sub_themes || []) {
    for (const example of theme.paraphrased_examples || []) {
      const quote = String(example || "").trim();
      if (!quote) continue;
      const key = quote.toLowerCase().slice(0, 120);
      if (seen.has(key)) continue;
      seen.add(key);
      out.push({
        quote,
        source: (theme.sources || []).join(", "),
        name: theme.name,
      });
    }
  }
  return out;
}

export default function AnswerDrawer({ open, onClose, detail, loading }) {
  const [showMore, setShowMore] = useState(false);
  const [showDetails, setShowDetails] = useState(false);

  useEffect(() => {
    if (!open) return undefined;
    setShowMore(false);
    setShowDetails(false);
    const onKey = (event) => {
      if (event.key === "Escape") onClose?.();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, onClose]);

  if (!open) return null;

  const quotes = collectQuotes(detail);
  const visible = showMore ? quotes : quotes.slice(0, 5);
  const implications = detail?.implications || [];

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-ink/40 backdrop-blur-sm" role="dialog" aria-modal="true">
      <button type="button" className="flex-1" aria-label="Close drawer" onClick={onClose} />
      <aside className="flex h-full w-full max-w-xl flex-col border-l border-hairline bg-surface shadow-2xl">
        <header className="flex items-start justify-between gap-3 border-b border-hairline px-5 py-4">
          <div>
            <p className="text-[11px] font-bold uppercase tracking-wide text-pink">Answer</p>
            <h2 className="mt-1 font-ui text-lg font-semibold leading-snug text-ink">{detail?.question}</h2>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-lg border border-hairline p-2 text-muted transition hover:text-ink"
            aria-label="Close"
          >
            <X className="size-4" />
          </button>
        </header>

        <div className="flex-1 overflow-y-auto px-5 py-4">
          {loading && (
            <div className="animate-pulse space-y-3">
              <div className="h-4 w-2/3 rounded bg-search" />
              <div className="h-16 rounded bg-search" />
              <div className="h-24 rounded bg-search" />
            </div>
          )}

          {!loading && detail && (
            <div className="space-y-8">
              <section>
                <h3 className="font-ui text-sm font-semibold text-ink">Answer</h3>
                <p className="mt-3 text-sm leading-relaxed text-ink">{detail.summary}</p>
                {(detail.sub_themes || []).length > 0 && (
                  <div className="mt-3 flex flex-wrap gap-1.5">
                    {detail.sub_themes.map((theme) => (
                      <span
                        key={theme.sub_theme_id}
                        className="rounded-full border border-pink/20 bg-pink/5 px-2.5 py-0.5 text-[10px] font-semibold tracking-wide text-pink"
                      >
                        {theme.name}
                      </span>
                    ))}
                  </div>
                )}
              </section>

              {visible.length > 0 && (
                <section>
                  <h3 className="font-ui text-sm font-semibold text-ink">What users said</h3>
                  <ul className="mt-3 space-y-4">
                    {visible.map((item) => (
                      <li key={item.quote} className="border-l-2 border-pink/40 pl-3">
                        <p className="text-sm leading-relaxed text-ink">“{item.quote}”</p>
                        <p className="mt-1.5 text-[11px] text-muted">
                          {[item.source, item.name].filter(Boolean).join(" · ")}
                        </p>
                      </li>
                    ))}
                  </ul>
                  {!showMore && quotes.length > 5 && (
                    <button
                      type="button"
                      onClick={() => setShowMore(true)}
                      className="mt-3 text-xs font-semibold text-pink hover:underline"
                    >
                      Show more reviews ({quotes.length - 5})
                    </button>
                  )}
                </section>
              )}

              {implications.length > 0 && (
                <section>
                  <h3 className="font-ui text-sm font-semibold text-ink">So what</h3>
                  <ul className="mt-3 space-y-2 text-sm text-muted">
                    {implications.slice(0, 3).map((item) => (
                      <li key={item} className="leading-relaxed">
                        · {item}
                      </li>
                    ))}
                  </ul>
                </section>
              )}

              {detail.data_gaps ? (
                <p className="text-sm text-muted">{detail.data_gaps}</p>
              ) : null}

              {detail.confidence && (
                <section>
                  <button
                    type="button"
                    onClick={() => setShowDetails((v) => !v)}
                    className="text-xs font-semibold text-muted hover:text-pink"
                  >
                    {showDetails ? "Hide details" : "More details"}
                  </button>
                  {showDetails && (
                    <div className="mt-3 space-y-2 rounded-xl border border-hairline bg-search p-3 text-xs text-muted">
                      <p>Confidence: {detail.confidence}</p>
                      <p>Evidence chunks: {detail.evidence_count || 0}</p>
                    </div>
                  )}
                </section>
              )}
            </div>
          )}
        </div>
      </aside>
    </div>
  );
}
