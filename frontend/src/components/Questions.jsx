import { ChevronDown } from "lucide-react";
import { qLabel } from "../api.js";

function ThemeBlock({ theme }) {
  return (
    <div className="border-t border-hairline py-4">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <h4 className="font-medium text-ink">{theme.name}</h4>
        <p className="text-xs text-muted">
          share {(theme.share_of_bucket * 100).toFixed(0)}% · diversity {theme.source_diversity} · impact{" "}
          {theme.impact_score}
        </p>
      </div>
      {theme.paraphrased_examples?.[0] ? (
        <p className="mt-2 text-sm text-muted">{theme.paraphrased_examples[0]}</p>
      ) : null}
      {theme.hypothesis ? <p className="mt-1 text-sm text-ink/80">{theme.hypothesis}</p> : null}
    </div>
  );
}

export default function Questions({ questions, openId, onToggle }) {
  return (
    <section id="research" className="bg-canvas">
      <div className="mx-auto max-w-6xl px-4 py-16 md:px-8">
        <p className="text-[11px] font-semibold uppercase tracking-[0.2em] text-pink">Research questions</p>
        <h2 className="mt-2 font-ui text-2xl font-semibold text-ink">Ten lenses on the 30-day wishlist</h2>
        <p className="mt-2 max-w-xl text-muted">Open a question for ranked sub-themes and paraphrased evidence.</p>
        <ul className="mt-10 divide-y divide-hairline border-y border-hairline bg-surface">
          {(questions || []).map((q) => {
            const open = openId === q.id;
            return (
              <li key={q.id}>
                <button
                  type="button"
                  onClick={() => onToggle(q.id)}
                  className="flex w-full items-start gap-4 px-4 py-5 text-left md:px-6"
                >
                  <span className="mt-0.5 text-[11px] font-semibold uppercase tracking-[0.18em] text-pink">
                    {qLabel(q.id)}
                  </span>
                  <span className="flex-1">
                    <span className="block font-medium text-ink">{q.question}</span>
                    <span className="mt-1 block text-sm text-muted">
                      {q.themes_count ? `${q.themes_count} sub-themes` : "Data gap"}
                      {q.confidence ? ` · ${q.confidence} confidence` : ""}
                    </span>
                  </span>
                  <ChevronDown
                    className={`mt-1 h-5 w-5 shrink-0 text-muted transition-transform duration-300 ${open ? "rotate-180" : ""}`}
                  />
                </button>
                <div
                  className={`grid transition-[grid-template-rows] duration-300 ease-out ${open ? "grid-rows-[1fr]" : "grid-rows-[0fr]"}`}
                >
                  <div className="overflow-hidden">
                    <div className="px-4 pb-6 md:px-6 md:pl-[4.5rem]">
                      <p className="text-sm leading-relaxed text-ink">{q.summary}</p>
                      {q.data_gaps ? <p className="mt-3 text-sm text-muted">{q.data_gaps}</p> : null}
                      {(q.sub_themes || []).map((theme) => (
                        <ThemeBlock key={theme.sub_theme_id} theme={theme} />
                      ))}
                      {(q.implications || []).length ? (
                        <ul className="mt-4 list-disc space-y-1 pl-5 text-sm text-ink">
                          {q.implications.map((line) => (
                            <li key={line}>{line}</li>
                          ))}
                        </ul>
                      ) : null}
                    </div>
                  </div>
                </div>
              </li>
            );
          })}
        </ul>
      </div>
    </section>
  );
}
