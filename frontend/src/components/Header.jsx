import { Search, Download } from "lucide-react";

export default function Header({ ask, onAskChange, onAsk, onExport, asking }) {
  return (
    <header className="border-b border-hairline bg-surface">
      <div className="mx-auto flex max-w-6xl flex-wrap items-center gap-3 px-4 py-3 md:gap-4 md:px-8">
        <a href="#top" className="wordmark shrink-0 text-2xl md:text-3xl">
          NYKAA
        </a>
        <nav className="hidden items-center gap-6 text-sm font-medium text-ink md:flex">
          <a href="#pipeline" className="hover:text-pink">
            Pipeline
          </a>
          <a href="#research" className="hover:text-pink">
            Research Qs
          </a>
          <a href="#themes" className="hover:text-pink">
            Themes
          </a>
        </nav>
        <form
          className="ml-auto flex min-w-0 flex-1 max-w-md items-center gap-2 rounded-md bg-search px-3 py-2"
          onSubmit={onAsk}
        >
          <Search className="h-4 w-4 shrink-0 text-muted" strokeWidth={1.75} />
          <input
            type="search"
            value={ask}
            onChange={(e) => onAskChange(e.target.value)}
            placeholder="Ask why a wishlist stalls"
            className="w-full bg-transparent text-sm text-ink outline-none placeholder:text-muted"
            aria-label="Ask a research question"
          />
          <button
            type="submit"
            className="text-xs font-semibold uppercase tracking-wide text-pink disabled:opacity-50"
            disabled={asking}
          >
            {asking ? "…" : "Go"}
          </button>
        </form>
        <button
          type="button"
          onClick={onExport}
          className="inline-flex shrink-0 items-center gap-2 rounded-full bg-pink px-3 py-2 text-sm font-semibold text-white hover:bg-pink-hover sm:px-4"
        >
          <Download className="h-4 w-4" strokeWidth={2} />
          Export
        </button>
      </div>
    </header>
  );
}
