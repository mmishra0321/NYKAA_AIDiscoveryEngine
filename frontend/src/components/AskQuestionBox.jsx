import { useState } from "react";
import { MessageCircleQuestion, Send } from "lucide-react";
import { askQuestion } from "../api.js";

export default function AskQuestionBox({ onOpenInsight }) {
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  async function handleSubmit(event) {
    event.preventDefault();
    const trimmed = question.trim();
    if (trimmed.length < 3) return;
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      setResult(await askQuestion(trimmed));
    } catch (err) {
      setError(err.message || "Could not reach the API.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <section id="ask-question" aria-label="Ask a discovery question">
      <div className="mb-4">
        <h2 className="font-ui text-lg font-semibold tracking-tight text-ink">Ask a Question</h2>
        <p className="mt-0.5 text-xs text-muted">
          Matches your question to the ten wishlist research questions, then grounds the answer on the catalog
        </p>
      </div>

      <div className="rounded-xl border border-hairline bg-surface p-5 sm:p-6">
        <form onSubmit={handleSubmit} className="flex flex-col gap-3 sm:flex-row sm:items-start">
          <label className="sr-only" htmlFor="discovery-question">
            Your question
          </label>
          <div className="relative flex-1">
            <MessageCircleQuestion
              className="pointer-events-none absolute top-3.5 left-3.5 size-4 text-muted"
              aria-hidden
            />
            <input
              id="discovery-question"
              type="text"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="e.g. Why do saved kurtas never convert within 30 days?"
              className="w-full rounded-xl border border-hairline bg-search py-3 pr-4 pl-10 text-sm text-ink outline-none transition placeholder:text-muted/70 focus:border-pink/40 focus:ring-2 focus:ring-pink/15"
              disabled={loading}
            />
          </div>
          <button
            type="submit"
            disabled={loading || question.trim().length < 3}
            className="ask-halo inline-flex items-center justify-center gap-2 rounded-xl bg-pink px-5 py-3 text-sm font-semibold text-white transition hover:bg-pink-hover disabled:cursor-not-allowed disabled:opacity-50"
          >
            <Send className="size-4" aria-hidden />
            {loading ? "Matching…" : "Ask"}
          </button>
        </form>

        {error && (
          <p className="mt-4 rounded-xl border border-pink/30 bg-pink/5 px-4 py-3 text-sm text-pink">{error}</p>
        )}

        {result && (
          <div className="mt-5 rounded-xl border border-pink/20 bg-pink/5 px-4 py-4">
            <p className="text-[11px] font-semibold uppercase tracking-wide text-pink">Matched research question</p>
            <p className="mt-1 text-sm font-medium text-ink">{result.question}</p>
            <p className="mt-3 text-sm leading-relaxed text-ink">{result.answer}</p>
            {result.query_id && onOpenInsight && (
              <button
                type="button"
                onClick={() => onOpenInsight(result.query_id)}
                className="mt-3 text-xs font-semibold text-pink hover:underline"
              >
                View full insight & evidence →
              </button>
            )}
          </div>
        )}
      </div>
    </section>
  );
}
