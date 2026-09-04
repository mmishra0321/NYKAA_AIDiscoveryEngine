import { ExternalLink, GitBranch, RefreshCw } from "lucide-react";

function formatWhen(value) {
  if (!value) return "—";
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return String(value);
  return d.toLocaleString(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  });
}

function statusLabel(action) {
  if (!action) return "No run found";
  const conclusion = (action.conclusion || "").toLowerCase();
  const status = (action.status || "").toLowerCase();
  if (status && status !== "completed") return status.replace(/_/g, " ");
  if (conclusion) return conclusion;
  return status || "unknown";
}

function statusTone(action) {
  const label = statusLabel(action).toLowerCase();
  if (label === "success") return "text-pink";
  if (label.includes("fail") || label === "cancelled") return "text-ink";
  if (label.includes("progress") || label === "queued" || label === "waiting") return "text-muted";
  return "text-muted";
}

export default function ScrapeStatus({ scrape }) {
  const last = scrape?.last_scrape;
  const action = scrape?.last_github_action;
  const sources = last?.sources || [];

  return (
    <section id="scrape-status" aria-label="Last scrape and GitHub Action">
      <div className="mb-4 flex flex-wrap items-end justify-between gap-3">
        <div>
          <h2 className="font-ui text-lg font-semibold tracking-tight text-ink">
            Last scrape &amp; GitHub Action
          </h2>
          <p className="mt-0.5 text-xs text-muted">
            {scrape?.schedule || "Scheduled ingest workflow"} · {scrape?.workflow_name || "Ingest pipeline"}
          </p>
        </div>
        {scrape?.actions_url ? (
          <a
            href={scrape.actions_url}
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center gap-1.5 text-sm font-semibold text-pink hover:underline"
          >
            Open Actions
            <ExternalLink className="size-3.5" strokeWidth={2.25} />
          </a>
        ) : null}
      </div>

      <div className="grid gap-3 md:grid-cols-2">
        <article className="rounded-xl border border-hairline bg-surface p-5">
          <div className="mb-3 flex items-center gap-2 text-pink">
            <RefreshCw className="size-4" strokeWidth={2} />
            <p className="text-[11px] font-semibold uppercase tracking-[0.14em]">Last scrape</p>
          </div>
          {last ? (
            <>
              <p className="font-ui text-2xl font-bold tracking-tight text-ink">
                {formatWhen(last.finished_at || last.run_date)}
              </p>
              <p className="mt-2 text-sm text-muted">
                Run date <span className="font-medium text-ink">{last.run_date || "—"}</span>
                {" · "}
                {last.records_fetched ?? "—"} fetched → {last.records_saved ?? "—"} saved
                {last.records_skipped != null ? ` · ${last.records_skipped} skipped` : ""}
              </p>
              {sources.length ? (
                <ul className="mt-4 space-y-1.5 text-xs text-muted">
                  {sources.map((row) => (
                    <li key={row.source} className="flex justify-between gap-3 border-b border-hairline py-1.5 last:border-0">
                      <span className="font-medium text-ink">{row.source}</span>
                      <span>
                        {row.records_saved ?? 0} saved
                        {row.errors ? ` · ${row.errors} err` : ""}
                      </span>
                    </li>
                  ))}
                </ul>
              ) : null}
            </>
          ) : (
            <p className="text-sm text-muted">No ingestion log found under data/raw/_logs yet.</p>
          )}
        </article>

        <article className="rounded-xl border border-hairline bg-surface p-5">
          <div className="mb-3 flex items-center gap-2 text-pink">
            <GitBranch className="size-4" strokeWidth={2} />
            <p className="text-[11px] font-semibold uppercase tracking-[0.14em]">GitHub Action</p>
          </div>
          {action ? (
            <>
              <p className={`font-ui text-2xl font-bold tracking-tight capitalize ${statusTone(action)}`}>
                {statusLabel(action)}
              </p>
              <p className="mt-2 text-sm text-muted">
                {formatWhen(action.run_started_at || action.created_at || action.updated_at)}
                {action.event ? ` · ${action.event}` : ""}
                {action.actor ? ` · ${action.actor}` : ""}
              </p>
              <p className="mt-1 text-xs text-muted">
                {action.display_title || scrape?.workflow_name}
                {scrape?.github_action_source ? ` · source: ${scrape.github_action_source}` : ""}
              </p>
              {action.html_url ? (
                <a
                  href={action.html_url}
                  target="_blank"
                  rel="noreferrer"
                  className="mt-4 inline-flex items-center gap-1.5 text-sm font-semibold text-pink hover:underline"
                >
                  View run #{action.id || ""}
                  <ExternalLink className="size-3.5" strokeWidth={2.25} />
                </a>
              ) : null}
            </>
          ) : (
            <p className="text-sm text-muted">
              No Actions run metadata yet. After the next scheduled scrape, status will appear here.
            </p>
          )}
        </article>
      </div>
    </section>
  );
}
