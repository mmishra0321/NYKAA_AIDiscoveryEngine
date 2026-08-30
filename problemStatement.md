# Problem Statement: AI-Powered Wishlist Discovery Engine

> **Canonical reference.** This document is the primary source of truth for product scope, business objective, the 10 research questions, data sources, constraints, and success criteria. Technical design lives in [architecture.md](./architecture.md). If the two diverge, amend this file first.

**Nykaa Fashion — Growth Team Capstone (Deliverable 1 of 3)**

---

## 1. Role & Context

You are acting as a Product Manager on the Growth Team at **Nykaa Fashion** (India's online fashion and lifestyle marketplace — Android app ID `com.fsn.nds`, iOS app ID `1439872423`).

Nykaa Fashion lets users browse fashion products (clothing, footwear, accessories, jewellery) and save items to a Wishlist. Over time, users accumulate dozens or hundreds of wishlisted items, but only a small fraction convert into purchases within a reasonable window.

---

## 2. Business Objective

**Increase the percentage of users who purchase at least one item from their wishlist within 30 days of adding it.**

Improving wishlist-to-purchase conversion increases purchase frequency and improves monetization from existing high-intent users, without needing to acquire new users.

---

## 3. Hard Constraint

No monetary incentives may be used as the solution (no coupons, discounts, cashback, or price-cuts as the mechanism). The fix must come from **removing friction, doubt, or forgetting** — not from making the item cheaper.

---

## 4. The Core Problem To Be Solved (by this engine)

We do not currently know **why** wishlist items fail to convert. This system's job is to discover that root cause at scale, from real Nykaa Fashion user language, **before any solution is designed**. This is qualitative-signal-mining, not a dashboard of star ratings.

---

## 5. Objective of the AI Discovery Engine

Build an AI-native workflow/agent system that ingests unstructured public text about **Nykaa Fashion specifically** (app reviews, forum posts, social discussion, video comments) and produces a structured, quantified breakdown of user behavior around wishlisting and purchase hesitation.

This must go **beyond summarization or sentiment tagging**. The system needs to:

1. Classify every relevant piece of text into one of the **10 research questions** below
2. Cluster the text within each question into **named sub-themes**
3. Quantify approximate **frequency / strength** of each sub-theme
4. Rank sub-themes by **potential impact** on the business metric

---

## 6. The 10 Research Questions — Output Classification Schema

Every piece of scraped, relevant text must be tagged against one (or more, if applicable) of these 10 buckets. This is the **primary output taxonomy** — the engine's core job is sorting raw text into these buckets, then finding patterns within each.

| # | Research Question | What counts as relevant text for this bucket |
|---|---|---|
| **Q1** | Why do users add fashion products to their wishlist? | Mentions of why something was saved — price watching, styling later, comparing, gifting, aspirational saving, occasion planning |
| **Q2** | What prevents wishlisted products from eventually being purchased? | Any stated or implied blocker after saving — doubt, distraction, friction, change of mind |
| **Q3** | What uncertainties remain after users have identified a product they like? | Fit, quality, color-accuracy, material, authenticity doubts expressed after liking the item |
| **Q4** | What causes users to postpone a purchase? | Deferral language — "waiting for," "not sure yet," "will decide later," "saving for now" |
| **Q5** | How do users compare multiple shortlisted products? | Mentions of comparing 2+ saved/considered items against each other before deciding |
| **Q6** | What information do users seek outside Nykaa Fashion before purchasing? | References to checking Instagram, YouTube reviews, friends, other retailers, size-comparison elsewhere |
| **Q7** | What role do fit, size, styling, price, reviews, occasion, and social validation play? | Any explicit mention of these six factors influencing a decision, positively or negatively |
| **Q8** | When is the wishlist genuine purchase intent vs. pure bookmarking? | Language distinguishing "I will buy this" vs. "just saving it," "for inspiration," "not really planning to buy" |
| **Q9** | How do these behaviors differ across user segments? | Any text with inferable segment context — first-time vs. repeat buyer, category (ethnic/western/footwear/beauty-crossover), price sensitivity |
| **Q10** | What unmet needs emerge consistently across many independent sources? | Recurring asks/complaints/suggestions that appear across **3+ independent sources** — the strongest signal bucket |

---

## 7. Functional Requirements (what the engine must actually do)

1. **Ingest** text from multiple heterogeneous public sources, Nykaa Fashion only (see Section 8).
2. **Normalize** all text into a common schema: `{source, source_type, date, product_category (if inferable), raw_text, url}`.
3. **Filter for relevance** — most reviews will be about delivery/logistics/refund complaints unrelated to wishlist behavior; discard or separately bucket these before deeper analysis.
4. **Classify** each relevant item into one or more of the 10 research question buckets in Section 6 using an **LLM-based classifier** (not keyword matching).
5. **Cluster** within each bucket into named sub-themes (e.g. within Q3: "sizing runs small," "fabric quality doubt," "color mismatch vs. photos").
6. **Quantify** each sub-theme: share of relevant mentions within its bucket, source diversity (how many independent sources), and a qualitative severity/frequency score.
7. **Segment** where possible — tag by inferred user type or product category if the source text allows it (feeds Q9 directly).
8. **Surface supporting evidence** — every sub-theme must be traceable to representative (**paraphrased, not verbatim-scraped-at-scale**) examples, so findings are defensible in interviews and the deck.
9. **Output** a structured report (JSON + human-readable summary), organized question-by-question (Q1–Q10), each with ranked sub-themes — to directly feed:
   - Part 2 (metric decomposition)
   - Part 3 (interview guide — hypotheses to validate)
   - Part 4 (final problem definition)
10. **Be deployed as a testable, shareable link** — a live workflow/interface (not a one-off script run once locally), since it is one of the three graded deliverables.

---

## 8. Data Sources to Scrape / Analyze — Nykaa Fashion Only

> **Note to implementer:** verify each URL's current availability, robots.txt / ToS compliance, and rate limits before building scrapers. Prefer official APIs (Reddit API, YouTube Data API, Google Play review API/RSS) over raw HTML scraping wherever one exists. Community links below are commonly-active fashion/beauty communities relevant to the Indian market — confirm current activity level before committing scraping effort.

### A. App Store & Play Store Reviews (primary, highest-signal source)

| App | URL / ID |
|---|---|
| Nykaa Fashion — Google Play | https://play.google.com/store/apps/details?id=com.fsn.nds&hl=en_IN |
| Nykaa Fashion — Apple App Store | https://apps.apple.com/in/app/nykaa-fashion-shopping-app/id1439872423 |
| Nykaa Beauty (cross-reference only for shared account/wishlist UX complaints — same company, same wishlist infra) | https://play.google.com/store/apps/details?id=com.fsn.nykaa&hl=en_IN |

### B. Independent Review / Complaint Platforms

| Platform | URL |
|---|---|
| Trustpilot — Nykaa | https://www.trustpilot.com/review/nykaa.com |
| Trustpilot — Nykaa Fashion | https://www.trustpilot.com/review/nykaafashion.com |
| MouthShut — Nykaa Fashion | https://www.mouthshut.com/product-reviews/nykaa-fashion-reviews-926168279 |
| MouthShut — Nykaa | https://www.mouthshut.com/product-reviews/nykaa-reviews-925702993 |
| Consumer complaint aggregator (search "Nykaa Fashion") | https://www.consumercomplaints.in/ |

### C. Reddit (community discussion — informal, high-context language)

| Subreddit | URL |
|---|---|
| r/IndianFashionAddicts | https://www.reddit.com/r/IndianFashionAddicts/ |
| r/IndianMakeupAddicts | https://www.reddit.com/r/IndianMakeupAddicts/ |
| r/IndianSkincareAddicts | https://www.reddit.com/r/IndianSkincareAddicts/ |
| r/india (search within sub) | https://www.reddit.com/r/india/ |
| r/femalefashionadvice | https://www.reddit.com/r/femalefashionadvice/ |

**Suggested search queries via Reddit API:** `"Nykaa Fashion" wishlist`, `"Nykaa Fashion" size`, `"Nykaa Fashion" review`, `"Nykaa Fashion" haven't bought`

### D. YouTube (video reviews, hauls, unboxings — comments section is the signal)

Search terms to pull video IDs, then extract comments via YouTube Data API:

- `"Nykaa Fashion haul review"`
- `"Nykaa Fashion app review India"`
- `"Nykaa Fashion sizing review"`
- `"Nykaa Fashion honest review"`

YouTube Data API v3 docs: https://developers.google.com/youtube/v3

### E. Twitter / X

- Search: https://twitter.com/search?q=%22Nykaa%20Fashion%22%20wishlist
- Search: https://twitter.com/search?q=%22Nykaa%20Fashion%22%20size
- Nykaa Fashion support handle public replies: https://twitter.com/NykaaFashion

### F. Q&A / Forums

- Quora (search `"Nykaa Fashion review"`, `"is Nykaa Fashion sizing accurate"`): https://www.quora.com/search?q=Nykaa%20Fashion%20review

### G. General Web

Search queries for implementer's scraper/agent:

- `"Nykaa Fashion" review site:blogspot.com`
- `"Nykaa Fashion" sizing guide honest review`
- `"Nykaa Fashion" wishlist experience`

---

## 9. Constraints & Non-Goals

| Rule | Detail |
|---|---|
| **Nykaa Fashion only** | Do not include Myntra, AJIO, or other competitor data in this engine's scope |
| **No login / paywall** | Do not scrape data requiring login/authentication or paywalled content |
| **ToS / robots.txt** | Respect each platform's terms of service and robots.txt; prefer official APIs where available |
| **Discovery, not conclusion** | The engine is a discovery tool, not the final answer — its output is a ranked hypothesis list to be validated in Part 3 (user interviews), not a conclusion to build against directly |
| **No PII** | No PII should be stored/displayed from scraped sources; aggregate and anonymize before reporting |

---

## 10. Success Criteria for This Deliverable

The engine is considered complete when it can:

1. Be accessed via a **live link** and re-run/queried by someone other than the builder
2. Sort all relevant scraped text into the **10 research question buckets** (Section 6), each with ranked, named sub-themes and supporting evidence
3. Produce **at least one quantified, evidence-backed answer per research question** (Q1–Q10)
4. Produce output clean enough to drop into a metric-decomposition exercise (Part 2) and an interview discussion guide (Part 3) with **minimal manual rework**

---

## 11. Downstream Use

This document is intended to be handed to an AI coding assistant (Cursor) to produce a detailed technical architecture plan (ingestion pipeline, storage schema, the Q1–Q10 classification prompt/logic, sub-theme clustering strategy, relevance filtering approach, output format, and deployment plan for the live link) — implementation choices are intentionally left open here for that next step.

See **[architecture.md](./architecture.md)** for that plan.
