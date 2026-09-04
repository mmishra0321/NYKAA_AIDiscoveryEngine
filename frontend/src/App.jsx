import { useEffect, useState } from "react";
import { ArrowRight } from "lucide-react";
import { exportCatalog, getCatalog, getInsight, getPipeline } from "./api.js";
import Header from "./components/Header.jsx";
import Pipeline from "./components/Pipeline.jsx";
import MetricCard from "./components/MetricCard.jsx";
import AskQuestionBox from "./components/AskQuestionBox.jsx";
import InsightCard from "./components/InsightCard.jsx";
import Themes from "./components/Themes.jsx";
import AnswerDrawer from "./components/AnswerDrawer.jsx";
import ScrapeStatus from "./components/ScrapeStatus.jsx";
import SectionHeading from "./components/SectionHeading.jsx";
import { TAXONOMY } from "./taxonomy.js";

export default function App() {
  const [catalog, setCatalog] = useState(null);
  const [pipeline, setPipeline] = useState(null);
  const [themeFilter, setThemeFilter] = useState(null);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [drawerLoading, setDrawerLoading] = useState(false);
  const [drawerDetail, setDrawerDetail] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    Promise.all([getCatalog(), getPipeline()])
      .then(([cat, pipe]) => {
        if (cancelled) return;
        setCatalog(cat);
        setPipeline(pipe);
      })
      .catch((err) => {
        if (!cancelled) setError(err.message || "Could not load catalog");
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const questions = catalog?.questions || [];
  const allowed = themeFilter ? TAXONOMY.find((t) => t.id === themeFilter)?.questions : null;
  const visible = allowed ? questions.filter((q) => allowed.includes(q.id)) : questions;

  function openInsight(queryId) {
    if (!queryId) return;
    setDrawerOpen(true);
    setDrawerLoading(true);
    setDrawerDetail(null);
    getInsight(queryId)
      .then(setDrawerDetail)
      .catch((err) => setDrawerDetail({ question: queryId, summary: err.message }))
      .finally(() => setDrawerLoading(false));
  }

  function handleExport() {
    exportCatalog("markdown").catch((err) => setError(err.message));
  }

  const gaps = questions.filter((q) => q.data_gaps).length;
  const themeCount = questions.reduce((n, q) => n + (q.themes_count || 0), 0);
  const scraped =
    pipeline?.scrape?.last_scrape?.records_fetched ??
    pipeline?.scrape?.last_scrape?.records_saved ??
    catalog?.corpus?.relevant ??
    "—";
  const classified =
    pipeline?.processing?.classified ??
    pipeline?.processing?.relevance?.wishlist_signal ??
    catalog?.corpus?.relevant ??
    "—";
  const interviewN = pipeline?.scrape?.last_scrape?.interview_n || 0;
  const sourcesLine =
    pipeline?.scrape?.last_scrape?.sources_line || "Play Store · App Store · Forum/Blogs · Interviews";
  const sourceCount = pipeline?.scrape?.last_scrape?.source_groups?.length || 4;

  return (
    <div id="top" className="relative min-h-screen overflow-x-hidden bg-canvas text-ink">
      <div className="sticky top-0 z-20">
        <div className="promo-bar animate-promo py-2 text-center text-[11px] font-medium uppercase tracking-[0.22em] text-white">
          Nykaa Fashion · wishlist to purchase in 30 days
        </div>
        <Header onExport={handleExport} />
      </div>

      <main className="relative mx-auto max-w-7xl space-y-12 px-6 pt-10 pb-4">
        <header className="max-w-3xl">
          <p className="wordmark text-5xl md:text-6xl">NYKAA</p>
          <h1 className="mt-3 font-ui text-3xl font-extrabold tracking-tight sm:text-4xl">
            Fashion wishlist discovery
          </h1>
          <p className="mt-3 text-base font-medium leading-relaxed text-ink/80 sm:text-lg">
            Public Nykaa Fashion language, classified into ten research questions, then ranked by impact on 30-day
            wishlist-to-purchase. Not by making the item cheaper.
          </p>
          {error ? <p className="mt-2 text-xs text-pink">{error}</p> : null}
        </header>

        <Pipeline summary={pipeline} />

        <ScrapeStatus scrape={pipeline?.scrape} processing={pipeline?.processing} />

        <section aria-label="Pipeline metrics">
          <SectionHeading
            title="Pipeline metrics"
            subtitle="Latest scrape volume, classification coverage, and source mix"
          />
          <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
            <MetricCard
              label="Scraped"
              value={scraped}
              meta={`${classified} classified${interviewN ? ` · interviews n=${interviewN}` : ""}`}
            />
            <MetricCard label="Coverage" value="10/10" meta={`${gaps} explicit data gaps`} />
            <MetricCard label="Sub-themes" value={themeCount || "—"} meta="Ranked by 30-day impact" />
            <MetricCard label="Sources" value={sourceCount} meta={sourcesLine} />
          </div>
        </section>

        <AskQuestionBox onOpenInsight={openInsight} />

        <section id="research">
          <SectionHeading
            title="Wishlist research questions"
            subtitle="Canonical catalog. Click a card for cited insight and paraphrased reviews"
            action={
              themeFilter ? (
                <button
                  type="button"
                  onClick={() => setThemeFilter(null)}
                  className="text-sm font-bold text-pink hover:underline"
                >
                  Clear theme filter
                </button>
              ) : null
            }
          />
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            {visible.map((item) => (
              <InsightCard key={item.id} {...item} onSelect={openInsight} />
            ))}
          </div>
          {!visible.length && (
            <p className="mt-2 text-sm text-muted">No research questions match this theme filter.</p>
          )}
        </section>

        <Themes
          questions={questions}
          selectedId={themeFilter}
          onSelect={(id) => {
            setThemeFilter((prev) => (prev === id ? null : id));
            document.getElementById("research")?.scrollIntoView({ behavior: "smooth" });
          }}
        />
      </main>

      <footer className="mt-16 border-t border-hairline bg-surface">
        <div className="mx-auto flex max-w-7xl flex-col gap-6 px-6 py-8 md:flex-row md:items-center md:justify-between">
          <div>
            <p className="wordmark text-xl">NYKAA</p>
            <p className="mt-2 text-xs text-muted">Growth catalog · no monetary incentives as the mechanism</p>
          </div>
          <div className="flex flex-wrap gap-5 text-sm text-muted">
            <a href="#scrape-status" className="hover:text-ink">
              Scrape
            </a>
            <a href="#ask-question" className="hover:text-ink">
              Ask
            </a>
            <a href="#pipeline" className="hover:text-ink">
              Pipeline
            </a>
            <a href="#research" className="hover:text-ink">
              Research Qs
            </a>
            <a href="#themes" className="hover:text-ink">
              Themes
            </a>
          </div>
          <button
            type="button"
            onClick={handleExport}
            className="inline-flex items-center justify-center gap-2 rounded-full bg-pink px-5 py-2.5 text-sm font-bold text-white hover:bg-pink-hover"
          >
            Export catalog report
            <ArrowRight className="size-4" />
          </button>
        </div>
      </footer>

      <AnswerDrawer
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        detail={drawerDetail}
        loading={drawerLoading}
      />
    </div>
  );
}
