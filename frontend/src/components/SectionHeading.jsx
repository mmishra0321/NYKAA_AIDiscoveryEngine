export default function SectionHeading({ title, subtitle, action }) {
  return (
    <div className="mb-5 flex flex-wrap items-end justify-between gap-3">
      <div>
        <h2 className="font-ui text-2xl font-extrabold tracking-tight text-ink sm:text-3xl">{title}</h2>
        {subtitle ? (
          <p className="mt-2 text-base font-medium leading-relaxed text-ink/75 sm:text-lg">{subtitle}</p>
        ) : null}
      </div>
      {action || null}
    </div>
  );
}
