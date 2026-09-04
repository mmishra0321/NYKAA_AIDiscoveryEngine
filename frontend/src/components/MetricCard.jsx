export default function MetricCard({ label, value, meta }) {
  return (
    <article className="research-card-shine relative overflow-hidden rounded-xl border border-hairline bg-surface p-5">
      <p className="text-[11px] font-bold uppercase tracking-[0.14em] text-muted">{label}</p>
      <p className="mt-2 font-ui text-3xl font-extrabold tracking-tight text-ink">{value}</p>
      <p className="mt-2 text-sm font-medium leading-relaxed text-ink/70">{meta}</p>
    </article>
  );
}
