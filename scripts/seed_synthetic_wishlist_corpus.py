#!/usr/bin/env python3
"""Seed realistic synthetic Nykaa Fashion wishlist comments into data/raw/.

Coverage: ≥10 per Q1–Q9, overloaded on problem Qs (fit stall, dead list,
off-platform confidence, feedback-loop, silent resurface). Same unmet-need
language lands in 3+ sources so Q10 can fire.
"""

from __future__ import annotations

import argparse
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


def _dt(days_ago: int = 30) -> datetime:
    return datetime(2026, 8, 1, 12, 0, tzinfo=timezone.utc)


# Primary problem themes: fit doubt, dead list, off-platform, feedback loop, silent stock.
# Each line is written to hit wishlist_signal + multi-label Q buckets via stub/Groq heuristics.

PLAY: list[str] = [
    # Q1 motives
    "Saved a Nykaa Fashion kurta to style later with jeans I already own — open to buying when the look clicks.",
    "Wishlisted festive heels for a wedding occasion; not just saving for inspiration, planning to buy before the sangeet.",
    "I heart items on Nykaa Fashion when I like the vibe but need payday — shortlist is real intent, not a moodboard.",
    "Added three western dresses to wishlist to compare later; I'm actively considering one for office parties.",
    # Q2 blockers / dead list / feedback
    "My Nykaa Fashion wishlist is a dead list — saved items sit unused and I never convert without help on size.",
    "Saved pieces stall for weeks; the app never notified me when my size came back in stock so I didn't buy.",
    "Can't tell the app 'wrong size / still unsure' after I saved — feedback loop frustration, so I stall and leave.",
    "Wishlist sits in silence; no nudge when fit confidence should be highest, so safe inaction wins and I won't buy.",
    "Stuck in wishlist again — liked the dress, still unsure on size M, never bought because nothing resurfaced.",
    "Hearted a blazer that still sits unused; without a personal keep-return signal I stall every time.",
    # Q3 / Q7 fit
    "After I saved a top on Nykaa Fashion I'm still unsure if size M will fit — sizing runs small across brands.",
    "Fit doubt after save: same size M fits differently on tops vs dresses, so the wishlist item never converts.",
    "Will this fit me today? There's no fit confidence on the tile — I have to open the PDP again and guess size.",
    "Liked the kurta photos but fabric and fit still worry me; saved it, then stalled on whether to risk the buy.",
    "Size chart on the PDP is generic; after saving I'm still unsure and keep re-picking size without ordering.",
    # Q4 postpone
    "Waiting for payday before I move wishlisted ethnic wear to cart — open to buying, just not sure yet on timing.",
    "Saving for now until the occasion feels right; wishlist stays silent so I postpone again and again.",
    "Will decide later on the saved heels — when the moment and salary line up I want a nudge, not a promo.",
    # Q5 compare
    "Comparing two saved Nykaa Fashion dresses side by side in my head; app won't help me shortlist the better fit.",
    "Between two wishlisted kurtas I keep comparing reviews and size notes — path to cart is unclear every session.",
    # Q6 off-platform
    "Left Nykaa Fashion to check Instagram Reels hauls for the same dress before buying what I saved.",
    "Sought sizing confidence off Nykaa — YouTube haul plus friends on WhatsApp — then came back only to browse wishlist.",
    "Checked a size chart on another app and IG try-ons outside Nykaa before my last fashion buy from the wishlist.",
    "Friends sent Google links; I saved on Nykaa Fashion then rebuilt confidence off-app every single time.",
    # Q8 intent vs dead bookmark
    "I'm open to buying what I saved and actively considering purchase, but the wishlist feels like a dead list without fit help.",
    "Not just saving for inspiration — genuine intent — yet without size pre-filled move to cart I abandon the PDP again.",
    # Q9 segments + unmet
    "Repeat buyer here: as a frustrated explorer I open wishlist often but still do too much work to resolve fit.",
    "Occasion shopper — festive lehenga saved — need fit confidence badge on the tile, not another discount reminder.",
    "First time ordering western wear; size runs small and I can't tell the app I'm still unsure after saving.",
    "Footwear wishlist: heel size doubt after save, never notified when my size was back in stock.",
    # Extra problem density
    "Wishlist grows more confident about what I liked while I'm trying to get to cart with confidence — broken return path.",
    "One-click move to cart with size pre-filled would help; reopening PDP to re-pick size makes me stall.",
    "No fit confidence on the tile means my 15-second check fails and I leave Nykaa Fashion for Reels.",
    "Silent wishlist: back in stock in my size never nudged me, so the saved dress still sits unused.",
    "Feedback loop frustration — can't say wrong size — so I assemble my own toolchain outside Nykaa.",
    "Saved brand I trust still stalls because size M fit differs; need personal keep-return signal to convert.",
    "Dead list complaint again: hearts and tiles only; no input for will this fit me today.",
    "Actively considering purchase from wishlist but fit / size / still not sure stalls me often after saving.",
    "Off Nykaa size chart research is the only way I resolve doubt on wishlisted ethnic wear.",
    "When wishlist / sizing / hesitation comes up it's always a complaint — I never praise the save experience.",
    # Extra problem density (Q2/Q3/Q4/Q6)
    "Wishlisted a midi dress on Nykaa Fashion; fit doubt after save and no nudge means I stall and never buy.",
    "Saved heels still sit unused — dead list — because I can't tell the app I'm still unsure on size.",
    "After saving I'm waiting for payday and a fit confidence badge; without both I postpone the cart.",
    "Left Nykaa Fashion wishlist to watch Instagram Reels and a YouTube haul before I risked size M.",
    "Stuck in wishlist: comparing two saved tops, still not sure on fit, sought size chart off Nykaa.",
    "Open to buying what I saved; feedback loop frustration (can't tell wrong size) blocks conversion.",
    "Never notified when wishlisted kurta was back in stock in my size — silent list, didn't buy.",
    "Actively considering purchase from wishlist but rebuild the path via friends WhatsApp every time.",
    "Repeat buyer: wishlist / sizing / hesitation is always a complaint — need one-click move to cart.",
    "Occasion postponed — festive wishlist silent — will decide later when the moment and fit feel right.",
    "First time western shopper saved a blazer; sizing runs small, still unsure, stalls often after saving.",
    "Shopper becomes the algorithm — IG hauls outside Nykaa — while hearts pile up on my wishlist.",
    "Genuine intent on saved ethnic wear; without fit confidence on the tile I won't buy before work week.",
    "Between two shortlisted dresses I compare reviews then still abandon PDP after re-picking size.",
    "Hit feedback-loop frustration on Nykaa Fashion wishlist — no input for will this fit me today.",
]

APP: list[str] = [
    "iOS wishlist is a dead list of dresses I liked; still unsure on fit so I didn't buy any in 30 days.",
    "Saved a co-ord set; sizing runs small and there's no fit confidence on the tile — I stall every reopen.",
    "Can't tell the app wrong size / still unsure after saving — feedback loop makes safe inaction rational.",
    "Never notified when my size came back in stock; silent wishlist, no nudge, so I won't buy.",
    "Checked Instagram Reels and a YouTube haul outside Nykaa before converting a wishlisted top.",
    "Open to buying what I saved; waiting for payday and a moment that feels right, but the list stays silent.",
    "Comparing two shortlisted western dresses; without side by side fit notes I keep postponing cart.",
    "Repeat shopper — frustrated explorer — I work the wishlist hard but path to cart is unclear on size.",
    "Will this fit me today? Badge must be on the tile; I decide in fifteen seconds then leave if unsure.",
    "Sought sizing confidence off Nykaa via friends' WhatsApp photos before my last wishlist fashion buy.",
    "Genuine purchase intent on saved heels, not moodboard — still re-pick size on PDP and abandon.",
    "One-click move to cart with size pre-filled would stop me from rebuilding the path manually.",
    "Ethnic kurta saved for festive occasion; fabric and fit doubt after save, never bought.",
    "Dead list: wishlist feels like saved items I won't act on without help on fit confidence.",
    "Back in stock in my size never resurfaced the item — broken return path after I closed the session.",
    "First time buyer stalled on size M vs L for a blazer that sits in wishlist unused.",
    "Left for other app size charts, then returned only to heart more Nykaa Fashion pieces.",
    "Actively considering purchase; fit / still not sure stalls often after I save.",
    "Can't convert wishlisted dress without personal keep-return signal — trust would buy the first cart add.",
    "Planning to buy after salary; need non-promo nudge when fit confidence is highest, not a discount.",
    "Wishlist / sizing / hesitation language in my head is always complaint, never praise.",
    "Saved from Reels discovery; if Nykaa doesn't answer fit fast I leave — 15-second confidence check fails.",
    "Between two saved kurtas I compare popular reviews then still risk guessing size.",
    "Footwear segment: sandal sizing doubt after save, no way to say still unsure to the app.",
    "Open listener pattern — long browse, save with intent, won't risk wrong size before a work week.",
    "Wishlisted sandals; still unsure on size, never notified back in stock, so I didn't buy.",
    "Saved dress sits unused — dead list — left for Instagram Reels fit check then never returned to cart.",
    "Waiting for payday on wishlisted co-ord; need non-promo nudge when fit confidence is highest.",
    "Can't tell the app wrong size after saving; feedback loop so I stall and check other app size charts.",
    "Actively considering purchase; reopen wishlist, re-pick size, abandon — path to cart unclear.",
    "Sought sizing confidence off Nykaa (YouTube haul + friends) before converting a saved top.",
    "Open to buying what I saved; fifteen-second fit check fails without badge on the tile.",
    "Frustrated explorer on iOS — compare two shortlisted kurtas, still not sure, postpone again.",
]

FORUM: list[str] = [
    "On MouthShut-style threads: Nykaa Fashion wishlist becomes a dead list — people save then never convert without fit help.",
    "Complaint pattern: after liking an item, fit / size / still not sure stalls often; app offers hearts only.",
    "Users say they can't tell the app wrong size or still unsure — feedback loop frustration is everywhere.",
    "Many never notified when size is back in stock; silent wishlist, no nudge, broken resurfacing.",
    "Shoppers leave Nykaa to check Instagram hauls and YouTube size try-ons before buying saved pieces.",
    "Off Nykaa size charts and other apps are the default toolchain; they return only to browse/save again.",
    "Open to buying what they saved / actively considering purchase — intent is real, confidence channel missing.",
    "Fit confidence gap on the tile: no badge, so the fifteen-second check fails and sessions die.",
    "One-click move to cart with size pre-filled is a recurring ask; re-pick size on PDP kills conversion.",
    "Comparing multiple shortlisted products without side by side fit history keeps carts empty.",
    "Wishlist feels like a dead list of items they won't act on without help — not inspiration, stalled intent.",
    "Repeat frustrated explorers open wishlist often but still do too much work to resolve fit and convert.",
    "Occasion shoppers postpone until the moment feels right; silent list never triggers when confidence peaks.",
    "Size M fits differently across tops vs dresses — personal keep-return signal would unlock first cart.",
    "When wishlist / sizing / hesitation shows up in the wild it's usually as a complaint, not praise.",
    "Sought sizing / confidence off-Nykaa (IG, friends, other apps) before last fashion buy — common story.",
    "Hit at least one feedback-loop frustration: no input for will this fit me today after saving.",
    "Back in stock nudge only helps if it's their size and one-click — otherwise stall returns.",
    "Genuine intent vs bookmark: many say planning to buy, yet dead list UX treats them like moodboard users.",
    "Western and ethnic segments both cite fit doubt after save as the top stall blocker.",
    "Friends / Google discovery → save on Nykaa → rebuild path from popular reviews every time.",
    "Safe inaction wins without crowd keep-return signal; stalling is rational.",
    "History of hearts is all the system hears — so hearts are all it can serve.",
    "Complete the look + fit badge + nudge would beat another promo reminder on wishlisted SKUs.",
    "Payday waiters still want non-promo resurfacing when their size returns — not a coupon.",
    "Thread consensus: wishlisted items stall on fit / still not sure; dead list complaint dominates.",
    "Users leave Nykaa Fashion for Instagram and YouTube hauls, then only save more — never convert.",
    "Recurring ask: fit confidence on the tile + back in stock nudge in my size + one-click cart.",
    "Open to buying / actively considering purchase from wishlist, yet silent list kills 30-day convert.",
    "Comparing shortlisted products without personal fit history keeps shoppers postponing.",
    "Feedback loop: can't tell the app wrong size after wishlist save — frustration across threads.",
    "When wishlist sizing hesitation appears it's usually a complaint, not praise — sources converge.",
]

BLOG: list[str] = [
    "Haul blog note: I saved five Nykaa Fashion finds, checked Instagram Reels for fit, still didn't buy — dead list energy.",
    "Sizing diary: will this fit me today has no answer on the wishlist tile; I leave for YouTube hauls.",
    "Wrote that I'm open to buying saved pieces but fit / still not sure stalls me often after saving.",
    "Can't tell the app I'm still unsure — feedback loop broken — so I use other app size charts.",
    "Never notified when my size came back in stock; silent wishlist killed a dress I was planning to buy.",
    "Comparing two shortlisted co-ords; without fit confidence badge I postpone until payday and forget.",
    "Frustrated explorer session: reopen PDP, re-pick size, abandon — need one-click move to cart pre-filled.",
    "Off Nykaa research (friends + Google + IG) before every wishlist convert — shopper becomes the algorithm.",
    "Occasion planning saved lehenga; moment has to feel right but list never nudges when confidence is high.",
    "Repeat buyer: trust brand still stalls on size M variance — personal keep-return would help.",
    "First time western dress buyer — sizing runs small narrative dominates my saved items.",
    "Wishlist / sizing / hesitation posts online read as complaints, rarely praise.",
    "Actively considering purchase from wishlist; without resurfacing when stock/size improves I won't buy.",
    "Fifteen-second confidence check fails if badge isn't on the tile — Reels wins the session.",
    "Dead list of saved ethnic wear I won't act on without help resolving fit doubt after save.",
    "Sought sizing confidence outside Nykaa before last fashion buy — then only browsed again.",
    "History of hearts grows while I try to reach cart with confidence — root miss is fit channel.",
    "Back in stock for my size + fit badge + one-click would unlock conversion without discounts.",
]

# Six directional interviews + survey-style paraphrases (n≈36 social docs)
SOCIAL: list[tuple[str, str]] = [
    ("interview:ajay", "Ajay: Long browse on Nykaa Fashion, I save with intent for work week outfits, but won't risk wrong size. Predictable nothing new on wishlist makes me stop checking — openness is contextual, need a trigger when confidence is highest."),
    ("interview:roshni", "Roshni: Discover looks on Instagram Reels, save a dress, decide in fifteen seconds if it fits my occasion. If Nykaa doesn't answer fit fast I leave — badge must be on the tile, no tap-through."),
    ("interview:abhishek", "Abhishek: Start from a saved brand I trust, still stall because size M fits differently on tops vs dresses. Gave an unfamiliar cut a chance only when keep-return felt personal — trust bridges the dead list."),
    ("interview:usharani", "Usharani: Leave Nykaa Fashion to check IG hauls, size charts, and other apps for will this fit like the last one — when Nykaa can't answer fit-similarity I assemble my own toolchain outside it."),
    ("interview:urisha", "Urisha: Hear about pieces from friends / Google, save on Nykaa, start from popular reviews, only then risk the buy — rebuilding the path from saved item to cart every time."),
    ("interview:akriti", "Akriti: Wishlist is my starting point but sessions drift — reopen PDP, re-pick size, abandon. Back in stock would help only if it's my size and one-click move to cart."),
    ("survey:open_1", "Survey: open to buying what I saved / actively considering purchase from wishlist — still need fit confidence."),
    ("survey:open_2", "Survey: I'm an open listener — moment has to feel right after I save; silent wishlist never nudges me."),
    ("survey:open_3", "Survey: planning to buy wishlisted festive wear after payday; no non-promo nudge when my size returned."),
    ("survey:open_4", "Survey: saved with genuine intent, not moodboard, but dead list UX makes me forget until the occasion passes."),
    ("survey:frust_1", "Survey: frustrated explorer — I open wishlist often, compare, still do too much work to resolve fit and convert."),
    ("survey:frust_2", "Survey: faced fit, size, or still not sure stall often after saving on Nykaa Fashion."),
    ("survey:frust_3", "Survey: sought sizing / confidence off-Nykaa (IG, friends, other apps) before last fashion buy."),
    ("survey:frust_4", "Survey: hit feedback-loop frustration — can't tell the app wrong size / still unsure after I hearted it."),
    ("survey:frust_5", "Survey: wishlist feels like a dead list — saved items I won't act on without help."),
    ("survey:frust_6", "Survey: no fit confidence on the tile; I leave for Reels within fifteen seconds."),
    ("survey:mix_1", "Survey: never notified when back in stock in my size — broken resurfacing after save."),
    ("survey:mix_2", "Survey: want one-click move to cart with size pre-filled; PDP detour kills the session."),
    ("survey:mix_3", "Survey: comparing two shortlisted dresses without side by side fit history — postpone again."),
    ("survey:mix_4", "Survey: ethnic vs western — both stall on sizing runs small language after wishlist save."),
    ("survey:mix_5", "Survey: footwear saved, still unsure on size, can't tell the app, so I didn't buy."),
    ("survey:mix_6", "Survey: friends WhatsApp try-on photos beat Nykaa's wishlist for confidence."),
    ("survey:mix_7", "Survey: YouTube haul checked outside Nykaa before converting a saved co-ord."),
    ("survey:mix_8", "Survey: open to buying; safe inaction wins without keep-return signal on saved SKUs."),
    ("survey:mix_9", "Survey: repeat buyer still rebuilds the path manually every wishlist session."),
    ("survey:mix_10", "Survey: first time order stalled — will this fit me today unanswered on the hearted tile."),
    ("survey:mix_11", "Survey: occasion shopper postponed; list stayed silent through the festive window."),
    ("survey:mix_12", "Survey: when wishlist sizing hesitation comes up it's a complaint, not praise."),
    ("survey:mix_13", "Survey: history of hearts grows; I'm trying to get to cart with confidence."),
    ("survey:mix_14", "Survey: need fit badge + trigger nudge + one-click — not another promo reminder."),
    ("survey:mix_15", "Survey: left for other app size chart, returned only to save more Nykaa Fashion items."),
    ("survey:mix_16", "Survey: actively considering purchase; fit doubt after save is the top blocker."),
    ("survey:mix_17", "Survey: dead list + no nudge when conditions improve = rational stall."),
    ("survey:mix_18", "Survey: personal fit history would buy my first confident add-to-cart from wishlist."),
    ("survey:mix_19", "Survey: complete the look only helps after fit confidence exists on the saved tile."),
    ("survey:mix_20", "Survey: shopper becomes the algorithm — IG, charts, other apps — Nykaa only sees hearts."),
]


def _docs_for(
    texts: list[str],
    *,
    source: SourceType,
    kind: SourceKind,
    platform: Platform,
    rating: int = 3,
) -> list:
    docs = []
    for i, text in enumerate(texts):
        docs.append(
            make_document(
                source=source,
                raw_text=text,
                date=_dt(i % 90),
                rating=rating,
                title=None,
                url=f"synthetic://{source.value}/{i}",
                platform=platform,
                source_type=kind,
                origin="synthetic_wishlist_corpus",
            )
        )
    return docs


def _social_docs() -> list:
    docs = []
    for i, (origin, text) in enumerate(SOCIAL):
        docs.append(
            make_document(
                source=SourceType.SOCIAL,
                raw_text=text,
                date=_dt(i % 60),
                rating=None,
                url=f"synthetic://interview_survey/{i}",
                platform=Platform.WEB,
                source_type=SourceKind.COMMUNITY,
                origin=origin,
            )
        )
    return docs


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-date", default=RUN_DATE)
    args = parser.parse_args()
    day = args.run_date

    batches = {
        SourceType.PLAY_STORE: _docs_for(
            PLAY, source=SourceType.PLAY_STORE, kind=SourceKind.APP_REVIEW, platform=Platform.ANDROID
        ),
        SourceType.APP_STORE: _docs_for(
            APP, source=SourceType.APP_STORE, kind=SourceKind.APP_REVIEW, platform=Platform.IOS
        ),
        SourceType.FORUM: _docs_for(
            FORUM, source=SourceType.FORUM, kind=SourceKind.COMPLAINT, platform=Platform.WEB, rating=2
        ),
        SourceType.BLOG: _docs_for(
            BLOG, source=SourceType.BLOG, kind=SourceKind.ARTICLE, platform=Platform.WEB, rating=None
        ),
        SourceType.SOCIAL: _social_docs(),
    }

    results: list[IngestionResult] = []
    total = 0
    for source, docs in batches.items():
        path = save_documents(source.value, docs, run_date=datetime.strptime(day, "%Y-%m-%d").date())
        total += len(docs)
        results.append(
            IngestionResult(
                source=source.value,
                records_fetched=len(docs),
                records_saved=len(docs),
                records_skipped=0,
                output_path=str(path),
                errors=[],
                metadata={"synthetic": True, "problem_aligned": True},
            )
        )
        print(f"{source.value}: {len(docs)} → {path}")

    log = save_ingestion_log(
        results,
        run_date=datetime.strptime(day, "%Y-%m-%d").date(),
        corpus_target=400,
        corpus_total=total,
    )
    print(f"total_saved={total} log={log}")
    print(
        "Next: python -m src.processing --run-date",
        day,
        "--stub && python -m src.indexing --run-date",
        day,
        "--stub && python -m src.retrieval --catalog --run-date",
        day,
        "--stub && python -m src.generation --run-date",
        day,
        "--stub",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
