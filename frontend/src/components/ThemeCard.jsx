import { Ban, Bookmark, Clock, GitCompare, Globe, Heart, HelpCircle, SlidersHorizontal, Sparkles, Users } from "lucide-react";

const ICONS = {
  heart: Heart,
  ban: Ban,
  help: HelpCircle,
  clock: Clock,
  compare: GitCompare,
  globe: Globe,
  sliders: SlidersHorizontal,
  bookmark: Bookmark,
  users: Users,
  spark: Sparkles,
};

export default function ThemeCard({ title, reviewsLabel, description, icon, selected, onSelect }) {
  const Icon = ICONS[icon] || Heart;
  return (
    <button
      type="button"
      onClick={onSelect}
      className={`w-full rounded-xl border bg-surface p-4 text-left transition ${
        selected ? "border-pink ring-1 ring-pink/30" : "border-hairline hover:border-pink/30"
      }`}
    >
      <div className="mb-4 flex size-12 items-center justify-center rounded-xl bg-pink/10 text-pink">
        <Icon className="size-6" strokeWidth={1.75} />
      </div>
      <h3 className="font-ui text-base font-semibold text-ink">{title}</h3>
      <p className="mt-1 text-[11px] font-bold tracking-wide text-pink">{reviewsLabel}</p>
      <p className="mt-2 text-xs leading-relaxed text-muted">{description}</p>
    </button>
  );
}
