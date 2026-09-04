import { ExternalLink, GitBranch, RefreshCw } from "lucide-react";
import SectionHeading from "./SectionHeading.jsx";

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
  return "text-muted";
}

export default function ScrapeStatus({ scrape, processing }) {
  const last = scrape?.last_scrape;
  const action = scrape?.last_github_action;
  const groups = last?.source_groups?.length
    ? last.source_groups
    : (last?.sources || []).map((row) => ({
        label: row.label || row.source,
        records_saved: row.records_saved,
      }));
  const scraped = last?.records_fetched ?? last?.records_saved ?? "—";
  const classified =
    processing?.classified ??
    processing?.relevance?.wishlist_signal ??
    "—";
  const interviewN = last?.interview_n || 0;

  return (
    <section id="scrape-status" aria-label="Last scrape and GitHub Action">
      <SectionHeading
        title="Last scrape & GitHub Action"
        subtitle={`${scrape?.schedule || "Every ~10 days"} · ${last?.sources_line || "Play Store · App Store · Forum/Blogs · Interviews"}`}
        action={
          scrape?.actions_url ? (
            <a
              href={scrape.actions_url}
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center gap-1.5 text-sm font-bold text-pink hover:underline"
            >
              Open Actions
              <ExternalLink className="size-3.5" strokeWidth={2.25} />
            </a>
          ) : null
        }
      />

      <div className="grid gap-3 md:grid-cols-2">
        <article className="research-card-shine relative overflow-hidden rounded-xl border border-hairline bg-surface p-5">
          <div className="mb-3 flex items-center gap-2 text-pink">
            <RefreshCw className="size-4" strokeWidth={2} />
            <p className="text-[11px] font-bold uppercase tracking-[0.14em]">Last scrape</p>
          </div>
          <p className="font-ui text-2xl font-extrabold tracking-tight text-ink">
            {formatWhen(last?.finished_at || last?.run_date)}
          </p>
          <p className="mt-2 text-[15px] font-semibold text-ink">
            {scraped} scraped → {classified} classified
            {interviewN ? ` · interviews n=${interviewN}` : ""}
          </p>
          <p className="mt-1 text-sm font-medium text-ink/70">
            {groups.length || 4} sources: {last?.sources_line || "Play Store · App Store · Forum/Blogs · Interviews"}
          </p>
          <ul className="mt-4 space-y-1.5 text-sm font-medium text-ink/80">
            {groups.map((row) => (
              <li
                key={row.label}
                className="flex justify-between gap-3 border-b border-hairline py-1.5 last:border-0"
              >
                <span className="font-bold text-ink">{row.label}</span>
                <span className="text-muted">{row.records_saved ?? 0} saved</span>
              </li>
            ))}
          </ul>
        </article>

        <article className="research-card-shine relative overflow-hidden rounded-xl border border-hairline bg-surface p-5">
          <div className="mb-3 flex items-center gap-2 text-pink">
            <GitBranch className="size-4" strokeWidth={2} />
            <p className="text-[11px] font-bold uppercase tracking-[0.14em]">GitHub Action</p>
          </div>
          {action ? (
            <>
              <p className={`font-ui text-2xl font-extrabold tracking-tight capitalize ${statusTone(action)}`}>
                {statusLabel(action)}
              </p>
              <p className="mt-2 text-[15px] font-medium text-ink/80">
                {formatWhen(action.run_started_at || action.created_at || action.updated_at)}
                {action.event ? ` · ${action.event}` : ""}
                {action.actor ? ` · ${action.actor}` : ""}
              </p>
              <p className="mt-1 text-sm font-medium text-muted">
                {action.display_title || scrape?.workflow_name}
              </p>
              {action.html_url ? (
                <a
                  href={action.html_url}
                  target="_blank"
                  rel="noreferrer"
                  className="mt-4 inline-flex items-center gap-1.5 text-sm font-bold text-pink hover:underline"
                >
                  View run #{action.id || ""}
                  <ExternalLink className="size-3.5" strokeWidth={2.25} />
                </a>
              ) : null}
            </>
          ) : (
            <p className="text-[15px] font-medium text-muted">
              No Actions run metadata yet. After the next scheduled scrape, status will appear here.
            </p>
          )}
        </article>
      </div>
    </section>
  );
}
