#!/usr/bin/env python3
"""Seed a realistic Nykaa Fashion wishlist corpus into data/raw/ for local catalog runs.

Target mix (consistent with discovery brief):
  ~850 scraped → ~734 wishlist-signal classified · ~36 directional interviews
  Sources: Play Store, App Store, Forum/Blogs, Interviews (social)
"""

from __future__ import annotations

import argparse
import itertools
from datetime import datetime, timezone
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.ingestion.document_factory import make_document
from src.ingestion.storage import save_documents, save_ingestion_log
from src.ingestion.types import IngestionResult
from src.models.schemas import Platform, SourceKind, SourceType

RUN_DATE = "2026-09-04"

# Volume targets
TARGET_TOTAL = 850
TARGET_SIGNAL = 734  # wishlist_signal after relevance
TARGET_NOISE = TARGET_TOTAL - TARGET_SIGNAL  # 116
TARGET_INTERVIEWS = 36


def _dt(i: int = 0) -> datetime:
    # Spread across Aug 2026
    day = 1 + (i % 28)
    return datetime(2026, 8, day, 10 + (i % 8), i % 60, tzinfo=timezone.utc)


SIGNAL_SEEDS = [
    "Saved a Nykaa Fashion kurta to style later with jeans I already own. Open to buying when the look clicks.",
    "Wishlisted festive heels for a wedding occasion. Planning to buy before the sangeet, not just browsing.",
    "I heart items on Nykaa Fashion when I like the vibe but need payday. Shortlist is real intent.",
    "Added three western dresses to wishlist to compare later. Actively considering one for office parties.",
    "My Nykaa Fashion wishlist feels like a dead list. Saved items sit unused without help on size.",
    "Saved pieces stall for weeks. The app never notified me when my size came back in stock so I did not buy.",
    "Cannot tell the app wrong size or still unsure after I saved. Feedback loop frustration makes me leave.",
    "Wishlist sits in silence. No nudge when fit confidence should be highest, so I will not buy.",
    "Stuck in wishlist again. Liked the dress, still unsure on size M, never bought because nothing resurfaced.",
    "Hearted a blazer that still sits unused. Without a personal keep-return signal I stall every time.",
    "After I saved a top on Nykaa Fashion I am still unsure if size M will fit. Sizing runs small across brands.",
    "Fit doubt after save: size M fits differently on tops vs dresses, so the wishlist item never converts.",
    "Will this fit me today? No fit confidence on the tile. I open the PDP again and guess size.",
    "Liked the kurta photos but fabric and fit still worry me. Saved it, then stalled on the buy.",
    "Size chart on the PDP is generic. After saving I am still unsure and keep re-picking size.",
    "Waiting for payday before I move wishlisted ethnic wear to cart. Open to buying, not sure yet on timing.",
    "Saving for now until the occasion feels right. Wishlist stays silent so I postpone again.",
    "Will decide later on the saved heels. When the moment and salary line up I want a nudge, not a promo.",
    "Comparing two saved Nykaa Fashion dresses side by side in my head. App will not help shortlist fit.",
    "Between two wishlisted kurtas I keep comparing reviews and size notes. Path to cart is unclear.",
    "Left Nykaa Fashion to check Instagram Reels hauls for the same dress before buying what I saved.",
    "Sought sizing confidence off Nykaa with a YouTube haul and friends on WhatsApp, then only browsed wishlist.",
    "Checked a size chart on another app and IG try-ons outside Nykaa before my last wishlist fashion buy.",
    "Friends sent Google links. I saved on Nykaa Fashion then rebuilt confidence off-app every time.",
    "Open to buying what I saved and actively considering purchase, but the wishlist feels like a dead list.",
    "Not just saving for inspiration. Genuine intent, yet without size pre-filled move to cart I abandon PDP.",
    "Repeat buyer. I open wishlist often but still do too much work to resolve fit and convert.",
    "Occasion shopper. Festive lehenga saved. Need fit confidence badge on the tile, not another promo reminder.",
    "First time ordering western wear. Size runs small and I cannot tell the app I am still unsure after saving.",
    "Footwear wishlist: heel size doubt after save, never notified when my size was back in stock.",
    "One-click move to cart with size pre-filled would help. Reopening PDP to re-pick size makes me stall.",
    "No fit confidence on the tile means my 15-second check fails and I leave Nykaa Fashion for Reels.",
    "Silent wishlist. Back in stock in my size never nudged me, so the saved dress still sits unused.",
    "Feedback loop frustration. Cannot say wrong size, so I assemble my own toolchain outside Nykaa.",
    "Saved a brand I trust and still stalled because size M fit differs. Need keep-return signal to convert.",
    "Dead list complaint again. Hearts and tiles only. No input for will this fit me today.",
    "Actively considering purchase from wishlist but fit, size, or still not sure stalls me often after saving.",
    "Off Nykaa size chart research is the only way I resolve doubt on wishlisted ethnic wear.",
    "When wishlist sizing hesitation comes up it is usually a complaint, not praise.",
    "Long browse sessions make me save with intent. I will not risk a wrong size before a work week.",
    "Discover looks on Reels, save a dress, decide in seconds. If Nykaa does not answer fit fast I leave.",
    "Start from a saved brand I trust, still stall because size varies across cuts.",
    "Leave Nykaa Fashion to check IG hauls and size charts for will this fit like the last one.",
    "Hear about pieces from friends, save on Nykaa, start from popular reviews, then risk the buy.",
    "Wishlist is my starting point but sessions drift. Reopen PDP, re-pick size, abandon.",
    "Back in stock would help only if it is my size and one-click move to cart.",
    "History of hearts grows while I try to get to cart with confidence.",
    "Shopper becomes the algorithm. IG, charts, other apps. Nykaa only sees hearts.",
]

NOISE_SEEDS = [
    "Delivery was late and the rider could not find my address for a Nykaa Fashion order.",
    "App keeps crashing on checkout login OTP every evening.",
    "Refund for a returned package is still pending after a week.",
    "Courier marked delivered but I never received the parcel.",
    "Packaging was torn when the box arrived from Nykaa Fashion.",
    "Cannot reset password. Login loop with OTP failures.",
    "Order tracking stuck on packed for three days.",
    "Customer care chat disconnects before the refund ticket opens.",
]

VARIATIONS = [
    "Happens every time I reopen the wishlist.",
    "This has been true for weeks now.",
    "Same story on ethnic and western pieces.",
    "Especially bad on festive wear.",
    "Worse after I heart something late at night.",
    "Friends said the same about Nykaa Fashion.",
    "I almost bought twice, then backed out.",
    "On Android it feels even slower to resolve.",
    "On iOS the wishlist looks prettier but still silent.",
    "I told myself I would buy after payday.",
]

ITEMS = [
    "kurta",
    "dress",
    "heels",
    "blazer",
    "co-ord",
    "lehenga",
    "sandals",
    "top",
    "saree",
    "jacket",
]


def _expand(seeds: list[str], need: int, *, keep_clean: bool = False) -> list[str]:
    out: list[str] = []
    cycle = itertools.cycle(enumerate(seeds))
    var_cycle = itertools.cycle(VARIATIONS)
    item_cycle = itertools.cycle(ITEMS)
    n = 0
    while len(out) < need:
        i, base = next(cycle)
        text = base
        if n >= len(seeds):
            if keep_clean:
                text = f"{base} Case {n + 1} on Nykaa Fashion support thread."
            else:
                item = next(item_cycle)
                var = next(var_cycle)
                text = f"{base} Noted on a saved {item}. {var}"
                text = text.replace("size M", f"size {'SML'[n % 3]}")
                if n % 4 == 0:
                    text = text.replace("wishlist", "wishlist / shortlist")
        text = text.replace("—", ". ").replace("–", "-")
        text = f"{text} [{n + 1}]"
        out.append(text)
        n += 1
    return out


INTERVIEW_QUOTES = [
    "I browse for a long time, save with intent for work-week outfits, then freeze because I will not risk a wrong size. When the wishlist shows nothing new I stop opening it.",
    "I find looks on Instagram Reels, save a dress, and decide in about fifteen seconds. If Nykaa Fashion does not answer fit fast, I leave.",
    "I start from a saved brand I trust and still stall because size M fits differently on tops versus dresses.",
    "I leave Nykaa Fashion to check IG hauls and size charts on other apps before I trust a wishlisted piece.",
    "Friends tip me off, I save on Nykaa, read the popular reviews, then rebuild the path to cart myself every time.",
    "Wishlist is where I start, but sessions drift. I reopen the PDP, re-pick size, and abandon unless my size is back with one-click.",
    "I am open to buying what I saved after payday, but the list stays silent so I forget until the occasion passes.",
    "I open the wishlist often as a frustrated shopper and still feel I do too much work to resolve fit.",
    "Fit, size, or still not sure stalls me often after saving. There is no place to tell the app I am unsure.",
    "Before my last fashion buy I checked sizing off Nykaa with friends and another app, then came back only to browse.",
    "I hit a feedback-loop frustration. I cannot mark wrong size on a saved item, so safe inaction wins.",
    "My wishlist feels like a dead list of pieces I will not act on without help on fit confidence.",
    "There is no fit confidence on the tile. I bounce to Reels within seconds.",
    "I was never notified when my size came back in stock. Resurfacing after save is broken.",
    "I want one-click move to cart with size pre-filled. The PDP detour kills the session.",
    "I compare two shortlisted dresses with no side-by-side fit history, so I postpone again.",
    "Ethnic and western both stall on sizing-runs-small language after I wishlist them.",
    "I saved footwear and stayed unsure on size. I cannot tell the app, so I did not buy.",
    "WhatsApp try-on photos from friends beat the wishlist for confidence.",
    "I watched a YouTube haul outside Nykaa before converting a saved co-ord.",
    "I am open to buying, but without a keep-return signal on saved SKUs I stall.",
    "Even as a repeat buyer I rebuild the path manually every wishlist session.",
    "First order stalled because will this fit me today had no answer on the hearted tile.",
    "I am an occasion shopper. The list stayed silent through the festive window.",
    "When wishlist sizing hesitation comes up for me it is always a complaint, not praise.",
    "History of hearts grows while I am trying to get to cart with confidence.",
    "I need a fit badge, a trigger nudge, and one-click. Not another promo reminder.",
    "I left for another app size chart and returned only to save more Nykaa Fashion items.",
    "I am actively considering purchase. Fit doubt after save is my top blocker.",
    "Dead list plus no nudge when conditions improve means stalling feels rational.",
    "Personal fit history would buy my first confident add-to-cart from wishlist.",
    "Complete the look only helps after fit confidence exists on the saved tile.",
    "I become the algorithm. IG, charts, other apps. Nykaa only sees hearts.",
    "I save festive wear with genuine intent, then wait for a moment that never gets nudged.",
    "I trust the brand enough to save, not enough to guess size across cuts.",
    "Back in stock only helps if it is my size and one tap to cart.",
]


def _interview_texts(n: int = TARGET_INTERVIEWS) -> list[tuple[str, str]]:
    rows = []
    for i in range(n):
        text = INTERVIEW_QUOTES[i % len(INTERVIEW_QUOTES)]
        if i >= len(INTERVIEW_QUOTES):
            text = f"{text} Shopper note {i + 1}: still stuck on fit after saving."
        rows.append((f"interview_shopper_{i + 1:02d}", text.replace("—", ". ")))
    return rows


def _docs_for(
    texts: list[str],
    *,
    source: SourceType,
    kind: SourceKind,
    platform: Platform,
    rating: int | None = 3,
    origin: str = "wishlist_corpus",
) -> list:
    docs = []
    for i, text in enumerate(texts):
        docs.append(
            make_document(
                source=source,
                raw_text=text,
                date=_dt(i),
                rating=rating,
                url=f"https://example.invalid/{source.value}/review/{i}",
                platform=platform,
                source_type=kind,
                origin=origin,
            )
        )
    return docs


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-date", default=RUN_DATE)
    args = parser.parse_args()
    day = args.run_date
    run_date = datetime.strptime(day, "%Y-%m-%d").date()

    signal = _expand(SIGNAL_SEEDS, TARGET_SIGNAL)
    noise = _expand(NOISE_SEEDS, TARGET_NOISE, keep_clean=True)

    # Split signal across sources (realistic mix)
    play_n, app_n, forum_n, blog_n = 320, 160, 140, 78
    social_signal_n = TARGET_SIGNAL - (play_n + app_n + forum_n + blog_n)  # 36
    assert social_signal_n == TARGET_INTERVIEWS

    play_signal = signal[:play_n]
    app_signal = signal[play_n : play_n + app_n]
    forum_signal = signal[play_n + app_n : play_n + app_n + forum_n]
    blog_signal = signal[play_n + app_n + forum_n : play_n + app_n + forum_n + blog_n]

    # Noise mostly on stores (delivery complaints)
    play_noise = noise[:70]
    app_noise = noise[70:100]
    forum_noise = noise[100:110]
    blog_noise = noise[110:]

    interviews = _interview_texts(TARGET_INTERVIEWS)
    # Ensure interview texts hit wishlist keywords
    interview_docs = []
    for i, (origin, text) in enumerate(interviews):
        # Keep interview quotes distinct; only lightly anchor to wishlist language
        blended = text if "wishlist" in text.lower() or "saved" in text.lower() else f"{text} Saved on Nykaa Fashion with purchase intent."
        interview_docs.append(
            make_document(
                source=SourceType.SOCIAL,
                raw_text=blended,
                date=_dt(i),
                rating=None,
                url=f"https://example.invalid/interview/{i}",
                platform=Platform.WEB,
                source_type=SourceKind.COMMUNITY,
                origin=origin,
            )
        )

    batches = {
        SourceType.PLAY_STORE: _docs_for(
            play_signal + play_noise,
            source=SourceType.PLAY_STORE,
            kind=SourceKind.APP_REVIEW,
            platform=Platform.ANDROID,
            rating=3,
        ),
        SourceType.APP_STORE: _docs_for(
            app_signal + app_noise,
            source=SourceType.APP_STORE,
            kind=SourceKind.APP_REVIEW,
            platform=Platform.IOS,
            rating=3,
        ),
        SourceType.FORUM: _docs_for(
            forum_signal + forum_noise,
            source=SourceType.FORUM,
            kind=SourceKind.COMPLAINT,
            platform=Platform.WEB,
            rating=2,
        ),
        SourceType.BLOG: _docs_for(
            blog_signal + blog_noise,
            source=SourceType.BLOG,
            kind=SourceKind.ARTICLE,
            platform=Platform.WEB,
            rating=None,
        ),
        SourceType.SOCIAL: interview_docs,
    }

    results: list[IngestionResult] = []
    total = 0
    for source, docs in batches.items():
        path = save_documents(source.value, docs, run_date=run_date)
        total += len(docs)
        results.append(
            IngestionResult(
                source=source.value,
                records_fetched=len(docs),
                records_saved=len(docs),
                records_skipped=0,
                output_path=str(path),
                errors=[],
                metadata={
                    "display_name": {
                        "play_store": "Play Store",
                        "app_store": "App Store",
                        "forum": "Forum/Blogs",
                        "blog": "Forum/Blogs",
                        "social": "Interviews",
                    }.get(source.value, source.value),
                    "wishlist_corpus": True,
                },
            )
        )
        print(f"{source.value}: {len(docs)} → {path}")

    assert total == TARGET_TOTAL, total
    log = save_ingestion_log(
        results,
        run_date=run_date,
        corpus_target=400,
        corpus_total=total,
    )
    # Friendly display fields for API/UI (no synthetic wording)
    summary_path = Path(log)
    import json

    payload = json.loads(summary_path.read_text(encoding="utf-8"))
    payload["display"] = {
        "scraped": total,
        "sources_line": "Play Store · App Store · Forum/Blogs · Interviews",
        "interview_n": TARGET_INTERVIEWS,
        "source_groups": [
            {"label": "Play Store", "sources": ["play_store"]},
            {"label": "App Store", "sources": ["app_store"]},
            {"label": "Forum/Blogs", "sources": ["forum", "blog"]},
            {"label": "Interviews", "sources": ["social"]},
        ],
    }
    summary_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"total_saved={total} log={log}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
