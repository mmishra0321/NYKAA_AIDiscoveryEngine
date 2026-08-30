import { useEffect, useState } from "react";
import { askQuestion, exportCatalog, getCatalog, getPipeline, getThemes } from "./api.js";
import Header from "./components/Header.jsx";
import Hero from "./components/Hero.jsx";
import Pipeline from "./components/Pipeline.jsx";
import Questions from "./components/Questions.jsx";
import Themes from "./components/Themes.jsx";

export default function App() {
  const [catalog, setCatalog] = useState(null);
  const [pipeline, setPipeline] = useState(null);
  const [themes, setThemes] = useState([]);
  const [openId, setOpenId] = useState(null);
  const [themeId, setThemeId] = useState(null);
  const [ask, setAsk] = useState("");
  const [askResult, setAskResult] = useState(null);
  const [asking, setAsking] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    Promise.all([getCatalog(), getPipeline(), getThemes()])
      .then(([cat, pipe, th]) => {
        if (cancelled) return;
        setCatalog(cat);
        setPipeline(pipe);
        setThemes(th.themes || []);
        setThemeId(th.themes?.[0]?.sub_theme_id || null);
      })
      .catch((err) => {
        if (!cancelled) setError(err.message || "Could not load catalog");
      });
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (askResult) {
      document.getElementById("ask-result")?.scrollIntoView({ behavior: "smooth" });
    }
  }, [askResult]);

  function handleAsk(event) {
    event.preventDefault();
    const q = ask.trim();
    if (q.length < 3) return;
    setAsking(true);
    askQuestion(q)
      .then((res) => {
        setAskResult(res);
        if (res.query_id) setOpenId(res.query_id);
      })
      .catch((err) => setError(err.message))
      .finally(() => setAsking(false));
  }

  function handleExport() {
    exportCatalog("markdown").catch((err) => setError(err.message));
  }

  return (
    <div id="top" className="min-h-screen bg-canvas">
      <div className="sticky top-0 z-20">
        <div className="promo-bar animate-promo py-2 text-center text-[11px] font-medium uppercase tracking-[0.22em] text-white">
          Nykaa Fashion · wishlist to purchase in 30 days
        </div>
        <Header
          ask={ask}
          onAskChange={setAsk}
          onAsk={handleAsk}
          onExport={handleExport}
          asking={asking}
        />
      </div>
      <Hero />
      {askResult ? (
        <div id="ask-result" className="border-b border-hairline bg-surface">
          <div className="mx-auto max-w-6xl px-4 py-6 md:px-8">
            <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-pink">Ask</p>
            <p className="mt-2 text-ink">{askResult.answer}</p>
          </div>
        </div>
      ) : null}
      {error ? (
        <p className="mx-auto max-w-6xl px-4 py-4 text-sm text-pink md:px-8">{error}</p>
      ) : null}
      <Pipeline summary={pipeline} />
      <Questions
        questions={catalog?.questions || []}
        openId={openId}
        onToggle={(id) => setOpenId((cur) => (cur === id ? null : id))}
      />
      <Themes themes={themes} selectedId={themeId} onSelect={setThemeId} />
      <footer className="border-t border-hairline bg-surface">
        <div className="mx-auto flex max-w-6xl flex-col items-start justify-between gap-4 px-4 py-10 md:flex-row md:items-center md:px-8">
          <p className="wordmark text-xl">NYKAA</p>
          <p className="text-sm text-muted">Growth catalog · no monetary incentives as the mechanism</p>
          <button
            type="button"
            onClick={handleExport}
            className="rounded-full bg-pink px-5 py-2 text-sm font-semibold text-white hover:bg-pink-hover"
          >
            Export Q1–Q10
          </button>
        </div>
      </footer>
    </div>
  );
}
