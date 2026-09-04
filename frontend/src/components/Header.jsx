import { Download } from "lucide-react";

const NAV = [
  { href: "#pipeline", label: "Pipeline" },
  { href: "#scrape-status", label: "Scrape" },
  { href: "#ask-question", label: "Ask" },
  { href: "#research", label: "Research Qs" },
  { href: "#themes", label: "Themes" },
];

export default function Header({ onExport }) {
  return (
    <header className="border-b border-hairline bg-surface/95 backdrop-blur-md">
      <div className="mx-auto flex max-w-7xl items-center gap-5 px-6 py-3.5">
        <a href="#top" className="wordmark shrink-0 text-2xl md:text-[1.75rem]">
          NYKAA
        </a>
        <span className="hidden h-5 w-px bg-hairline sm:block" aria-hidden />
        <span className="hidden font-ui text-sm font-semibold tracking-tight text-muted sm:inline">
          Wishlist <span className="text-pink">discovery</span>
        </span>
        <nav className="ml-auto hidden items-center gap-5 lg:flex">
          {NAV.map((item) => (
            <a
              key={item.href}
              href={item.href}
              className="relative pb-1 text-sm font-medium text-ink transition hover:text-pink"
            >
              {item.label}
            </a>
          ))}
        </nav>
        <button
          type="button"
          onClick={onExport}
          className="inline-flex shrink-0 items-center gap-2 rounded-full bg-pink px-4 py-2 text-sm font-semibold text-white hover:bg-pink-hover lg:ml-2"
        >
          <Download className="h-4 w-4" strokeWidth={2} />
          Export
        </button>
      </div>
    </header>
  );
}
