import { qLabel } from "../api.js";

export default function Themes({ themes, selectedId, onSelect }) {
  const selected = (themes || []).find((t) => t.sub_theme_id === selectedId) || themes?.[0];
  return (
    <section id="themes" className="border-t border-hairline bg-surface">
      <div className="mx-auto max-w-6xl px-4 py-16 md:px-8">
        <p className="text-[11px] font-semibold uppercase tracking-[0.2em] text-pink">Sub-theme explorer</p>
        <h2 className="mt-2 font-ui text-2xl font-semibold text-ink">What recurs after the save</h2>
        <p className="mt-2 max-w-xl text-muted">Ranked by impact on 30-day conversion. Names are hypotheses for interviews.</p>
        {!themes?.length ? (
          <p className="mt-8 text-sm text-muted">No named sub-themes in this catalog run.</p>
        ) : (
          <div className="mt-8 grid gap-8 md:grid-cols-[minmax(0,14rem)_1fr]">
            <ul className="space-y-1 text-sm">
              {themes.map((theme) => (
                <li key={theme.sub_theme_id}>
                  <button
                    type="button"
                    onClick={() => onSelect(theme.sub_theme_id)}
                    className={`w-full border-b py-2 text-left ${
                      selected?.sub_theme_id === theme.sub_theme_id
                        ? "border-pink font-medium text-pink"
                        : "border-hairline text-ink hover:text-pink"
                    }`}
                  >
                    {theme.name}
                  </button>
                </li>
              ))}
            </ul>
            {selected ? (
              <div>
                <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-pink">
                  {qLabel(selected.question_id)}
                </p>
                <h3 className="mt-1 text-xl font-medium text-ink">{selected.name}</h3>
                <p className="mt-2 text-sm text-muted">
                  Share {(selected.share_of_bucket * 100).toFixed(0)}% · {selected.source_diversity} sources ·{" "}
                  {selected.frequency} frequency · {selected.severity} severity
                </p>
                <p className="mt-4 text-ink">{selected.hypothesis}</p>
                {(selected.paraphrased_examples || []).map((ex) => (
                  <p key={ex} className="mt-3 text-sm text-muted">
                    {ex}
                  </p>
                ))}
                {(selected.interview_probes || []).length ? (
                  <p className="mt-4 text-sm text-ink">
                    Probe: {selected.interview_probes[0]}
                  </p>
                ) : null}
              </div>
            ) : null}
          </div>
        )}
      </div>
    </section>
  );
}
