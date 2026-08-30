export default function Hero() {
  return (
    <section className="relative min-h-[calc(100vh-7.5rem)] overflow-hidden bg-ink">
      <img
        src="https://images.unsplash.com/photo-1483985988355-763728e1935b?auto=format&fit=crop&w=2400&q=80"
        alt=""
        className="absolute inset-0 h-full w-full object-cover animate-hero-zoom"
      />
      <div className="absolute inset-0 bg-gradient-to-r from-white via-white/90 to-transparent" />
      <div className="relative mx-auto flex min-h-[calc(100vh-7.5rem)] max-w-6xl flex-col justify-center px-4 py-16 md:px-8">
        <p className="wordmark animate-rise text-6xl md:text-8xl">NYKAA</p>
        <h1 className="mt-4 max-w-xl animate-rise font-ui text-3xl font-semibold leading-tight text-ink delay-100 md:text-5xl" style={{ animationDelay: "80ms" }}>
          Why saved fashion waits past 30 days
        </h1>
        <p className="mt-4 max-w-md animate-rise text-base text-muted md:text-lg" style={{ animationDelay: "160ms" }}>
          Public Nykaa Fashion language, ranked by impact on wishlist-to-purchase — not by making the item cheaper.
        </p>
        <a
          href="#research"
          className="mt-8 inline-flex w-fit animate-rise rounded-full bg-pink px-6 py-3 text-sm font-semibold text-white hover:bg-pink-hover"
          style={{ animationDelay: "240ms" }}
        >
          Read the 10 questions
        </a>
      </div>
    </section>
  );
}
