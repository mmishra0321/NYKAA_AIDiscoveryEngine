export default function MetricCard({ label, value, meta }) {
  return (
    <article className="rounded-xl border border-hairline bg-surface p-5">
      <p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-muted">{label}</p>
      <p className="mt-2 font-ui text-3xl font-bold tracking-tight text-ink">{value}</p>
      <p className="mt-2 text-xs font-medium leading-relaxed text-muted">{meta}</p>
    </article>
  );
}
