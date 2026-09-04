"""Cluster wishlist_signal docs per question, name sub-themes, compute Q10."""

from __future__ import annotations

import logging
import math
import re
from collections import defaultdict
from typing import Optional

from src.config_loader import load_processing, load_prompts, load_retrieval
from src.models.schemas import FrequencyLabel, ReviewDocument, SubTheme
from src.processing.groq_client import GroqClient
from src.processing.jsonutil import parse_json_object
from src.processing.quantify import score_and_rank, severity_num

logger = logging.getLogger(__name__)

SLUG_RE = re.compile(r"[^a-z0-9]+")

KEYWORD_SLUGS: list[tuple[str, str, str]] = [
    ("sizing_runs_small", "Sizing runs small", r"runs small|too small|size m fits|sizing chart"),
    ("fabric_quality_doubt", "Fabric quality doubt", r"fabric|polyester|material|thin"),
    ("color_mismatch", "Colour mismatch vs photos", r"colour|color|shade"),
    ("authenticity_doubt", "Authenticity doubt", r"authentic|fake|original"),
    ("fit_doubt_after_save", "Fit / size doubt after save", r"fit|still unsure|will this fit|wrong size"),
    ("dead_wishlist", "Wishlist feels like a dead list", r"dead list|won't act|wont act|sits unused|never open wishlist"),
    ("no_fit_feedback", "Can't tell the app wrong size / still unsure", r"can't tell the app|cant tell the app|feedback loop|still unsure|no way to say"),
    ("silent_back_in_stock", "No resurface when size / stock improves", r"back in stock|never notified|no nudge|my size came|silent wishlist"),
    ("fit_confidence_gap", "No fit confidence on the tile", r"fit confidence|on the tile|badge|fifteen.second|15.second"),
    ("one_click_cart_gap", "Wants size-prefilled move to cart", r"one.click|pre-filled|prefilled|move to cart|pdp again|re-pick size"),
    ("forgot_wishlist", "Wishlist forgotten", r"forgot|forget|don't remember|dont remember"),
    ("occasion_planning", "Occasion planning", r"wedding|occasion|festive|sangeet"),
    ("styling_later", "Saving to style later", r"style later|styling|outfit"),
    ("comparing_saved_items", "Comparing saved items", r"compar|between|vs |versus|side by side"),
    ("youtube_haul", "YouTube / haul research before convert", r"youtube|haul"),
    ("instagram_try_on", "Instagram / Reels try-ons", r"instagram|reels"),
    ("off_platform_size_chart", "Off-Nykaa size charts and other apps", r"size chart|other app|outside nykaa|off nykaa"),
    ("moodboard_bookmark", "Moodboard / bookmark only", r"inspiration|moodboard|just saving"),
    ("genuine_intent", "Genuine purchase intent", r"will buy|going to buy|open to buying|actively considering"),
    ("waiting_for_payday", "Waiting for payday / right moment", r"payday|salary|when the moment"),
    ("non_promo_nudge", "Non-promo wishlist reminder", r"remind|nudge"),
    ("side_by_side_gap", "No side-by-side compare", r"side by side|compare"),
]

HIGH_SEVERITY = {
    "sizing_runs_small",
    "fit_doubt_after_save",
    "fabric_quality_doubt",
    "authenticity_doubt",
    "dead_wishlist",
    "no_fit_feedback",
    "silent_back_in_stock",
    "fit_confidence_gap",
    "one_click_cart_gap",
    "off_platform_size_chart",
}


def _slugify(value: str) -> str:
    slug = SLUG_RE.sub("_", value.lower()).strip("_")
    return slug[:48] or "other"


def _char_ngrams(text: str, n: int = 3) -> set[str]:
    normalized = re.sub(r"\s+", " ", text.lower()).strip()
    if len(normalized) < n:
        return {normalized} if normalized else set()
    return {normalized[i : i + n] for i in range(len(normalized) - n + 1)}


def _cosine_sets(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / math.sqrt(len(a) * len(b))


def _cosine_vec(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def try_minilm_vectors(texts: list[str]) -> list[list[float]] | None:
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError:
        return None
    try:
        model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
        vectors = model.encode(texts, show_progress_bar=False)
        return [list(map(float, row)) for row in vectors]
    except Exception as exc:  # noqa: BLE001
        logger.warning("MiniLM unavailable, using n-gram clustering: %s", exc)
        return None


def keyword_groups(
    texts: list[str],
    *,
    min_cluster_size: int,
) -> tuple[list[list[int]], list[int]]:
    """Group indices by first matching KEYWORD_SLUGS pattern (stub-friendly)."""
    buckets: dict[str, list[int]] = defaultdict(list)
    unmatched: list[int] = []
    for i, text in enumerate(texts):
        lower = text.lower()
        matched = None
        for slug, _name, pattern in KEYWORD_SLUGS:
            if re.search(pattern, lower):
                matched = slug
                break
        if matched is None:
            unmatched.append(i)
        else:
            buckets[matched].append(i)
    kept = [idxs for idxs in buckets.values() if len(idxs) >= min_cluster_size]
    leftover = list(unmatched)
    for idxs in buckets.values():
        if len(idxs) < min_cluster_size:
            leftover.extend(idxs)
    return kept, leftover


def agglomerative_groups(
    texts: list[str],
    *,
    distance_threshold: float = 0.35,
    min_cluster_size: int = 3,
    vectors: list[list[float]] | None = None,
) -> tuple[list[list[int]], list[int]]:
    """Greedy cosine clustering. Returns (kept clusters, leftover indices)."""
    n = len(texts)
    if n == 0:
        return [], []
    sim_cut = 1.0 - distance_threshold
    grams = None if vectors is not None else [_char_ngrams(t) for t in texts]

    def sim(i: int, j: int) -> float:
        if vectors is not None:
            return _cosine_vec(vectors[i], vectors[j])
        return _cosine_sets(grams[i], grams[j])  # type: ignore[index]

    clusters: list[list[int]] = []
    for i in range(n):
        best_c = -1
        best_s = -1.0
        for c_idx, members in enumerate(clusters):
            mean_s = sum(sim(i, j) for j in members) / len(members)
            if mean_s > best_s:
                best_s = mean_s
                best_c = c_idx
        if best_c >= 0 and best_s >= sim_cut:
            clusters[best_c].append(i)
        else:
            clusters.append([i])

    kept = [c for c in clusters if len(c) >= min_cluster_size]
    leftover = [i for c in clusters if len(c) < min_cluster_size for i in c]
    return kept, leftover


def infer_slug(texts: list[str]) -> tuple[str, str, str]:
    blob = " ".join(texts).lower()
    for slug, name, pattern in KEYWORD_SLUGS:
        if re.search(pattern, blob):
            sev = "high" if slug in HIGH_SEVERITY else "medium"
            return slug, name, sev
    return "other", "Other wishlist language", "low"


def paraphrase_stub(name: str) -> str:
    return (
        f"Users describe {name.lower()} after liking or saving a Nykaa Fashion item. "
        "Enough to stall a 30-day purchase."
    )


ALTERNATE_COMMENTS: dict[str, list[str]] = {
    "fit_doubt_after_save": [
        "Liked the dress on Nykaa Fashion, then stalled because size M still felt like a guess.",
        "They keep reopening the PDP after saving just to stare at the size chart again.",
        "Saved with real intent, but fit confidence never showed up on the wishlist tile.",
    ],
    "dead_wishlist": [
        "Their wishlist looks full, yet nothing moves unless someone helps with size confidence.",
        "Hearts pile up while the list stays quiet for weeks.",
        "They call it a dead list: saved pieces they will not act on without a nudge.",
    ],
    "silent_back_in_stock": [
        "Their size came back and the app said nothing, so the saved kurta stayed untouched.",
        "No resurface when stock returned in their size. They stopped checking.",
        "Waiting for a back-in-stock ping on a saved heel that never arrived.",
    ],
    "no_fit_feedback": [
        "After saving, there is nowhere to say still unsure on size, so they leave.",
        "They wanted to tell the app wrong size, but the wishlist only keeps the heart.",
        "Feedback dies after the save. The doubt stays private and the cart stays empty.",
    ],
    "instagram_try_on": [
        "They checked Reels try-ons for the same dress before touching checkout.",
        "Instagram made the fit feel real; Nykaa Fashion only showed the save.",
        "A creator haul decided the buy more than the wishlist tile did.",
    ],
    "off_platform_size_chart": [
        "They left for another app size chart, then came back only to browse again.",
        "WhatsApp photos from a friend beat the in-app size guide for confidence.",
        "Google and a random size chart finished the decision the wishlist could not.",
    ],
    "youtube_haul": [
        "A YouTube haul answered fabric and fit questions the saved PDP never did.",
        "They watched two hauls before risking the wishlisted co-ord.",
        "Off-app video proof came first; Nykaa Fashion was just where it was saved.",
    ],
    "comparing_saved_items": [
        "Two saved kurtas, no side-by-side, so they keep postponing the pick.",
        "They bounce between shortlisted dresses without a clear fit winner.",
        "Comparison lives in their head because the app will not help.",
    ],
    "waiting_for_payday": [
        "Open to buying after salary, but the silent wishlist never times the return.",
        "They are waiting for payday and a moment that feels right.",
        "Money is ready next week; the list still will not nudge them back.",
    ],
    "genuine_intent": [
        "This was a definite buy list, not a moodboard, until size doubt crept in.",
        "They planned to purchase, then abandoned because size stayed unclear.",
        "Intent was real on save day. Confidence was not.",
    ],
    "one_click_cart_gap": [
        "They hate re-picking size on the PDP every time they reopen a saved item.",
        "One-click move to cart with size pre-filled would have closed the session.",
        "The path from wishlist to cart feels rebuilt from scratch each visit.",
    ],
    "fit_confidence_gap": [
        "Fifteen seconds on the tile. No badge. They bounce to Reels.",
        "Fit confidence missing on the hearted card kills the impulse buy.",
        "If the tile answered will this fit me, they would not leave the app.",
    ],
    "sizing_runs_small": [
        "Brand size M runs small on tops, so the saved dress stays parked.",
        "They learned the hard way that ethnic and western cuts size differently.",
        "Runs-small warnings show up after the save, never before the stall.",
    ],
    "generic": [
        "Saved on Nykaa Fashion with intent, then stalled on a confidence gap.",
        "The wishlist remembers the like. It forgets the doubt.",
        "They want to convert, but the app only shows hearts and tiles.",
        "Public comments keep circling fit, silence after save, and off-app checks.",
        "Without a personal keep-return signal, safe inaction wins.",
        "Occasion was clear. Size confidence was not, so the cart waited.",
        "They open the wishlist often and still leave without resolving fit.",
        "A quiet list taught them that saving is easy and converting is work.",
        "Need fit confidence badge on the tile, not another promo reminder.",
    ],
}


def _alts_for(name: str, slug: str | None = None) -> list[str]:
    key = (slug or _slugify(name)).lower()
    hits: list[str] = []
    for alt_key, alts in ALTERNATE_COMMENTS.items():
        if alt_key == "generic":
            continue
        if alt_key in key or alt_key.replace("_", " ") in name.lower():
            hits.extend(alts)
    hits.extend(ALTERNATE_COMMENTS.get("generic", []))
    return hits


def _paraphrase_dedupe_key(text: str) -> str:
    """Normalize near-duplicates (interview N prefixes, trailing [n], shared boilerplate)."""
    t = text.lower()
    t = re.sub(r"directional interview\s*\d+\s*:\s*", "", t)
    t = re.sub(r"shopper\s*\d+\s*:\s*", "", t)
    t = re.sub(r"\s*\[\d+\]\s*$", "", t)
    t = re.sub(
        r"saved on nykaa fashion(?: wishlist)? with purchase intent[,.]?\s*"
        r"(?:still unsure on fit\.?)?",
        "",
        t,
    )
    t = re.sub(r"[^a-z0-9\s]", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t[:140]


def paraphrase_from_members(
    members: list,
    name: str,
    *,
    used: set[str] | None = None,
    slug: str | None = None,
) -> list[str]:
    """Lightly rewrite member snippets; prefer distinct quotes across the run."""
    used_refs = used if used is not None else set()

    def _rewrite(raw: str) -> str:
        raw = " ".join(str(raw or "").split())
        raw = raw.replace("—", ". ").replace("–", "-")
        raw = re.sub(r"^Directional interview\s*\d+\s*:\s*", "", raw, flags=re.IGNORECASE)
        raw = re.sub(r"\s*\[\d+\]\s*$", "", raw)
        raw = re.sub(
            r"\s*Noted on a saved [a-z0-9-]+\.\s*"
            r"(?:Happens every time I reopen the wishlist|"
            r"This has been true for weeks now|"
            r"Same story on ethnic and western pieces|"
            r"Especially bad on festive wear|"
            r"Worse after I heart something late at night|"
            r"Friends said the same about Nykaa Fashion|"
            r"I almost bought twice, then backed out|"
            r"On Android it feels even slower to resolve|"
            r"On iOS the wishlist looks prettier but still silent|"
            r"I told myself I would buy after payday)\.?",
            "",
            raw,
            flags=re.IGNORECASE,
        )
        raw = re.sub(
            r"\s*Saved on Nykaa Fashion(?: wishlist)? with purchase intent[,.]?\s*"
            r"(?:still unsure on fit\.?)?",
            "",
            raw,
            flags=re.IGNORECASE,
        )
        if not raw:
            return ""
        text = re.sub(r"\bReviews say\b", "People note", raw, flags=re.IGNORECASE)
        text = re.sub(r"\bI'M\b", "they're", text)
        text = re.sub(r"\bI'm\b", "they're", text)
        text = re.sub(r"\bI\b", "they", text)
        text = re.sub(r"\b[Mm]y\b", "their", text)
        text = re.sub(r"\bI've\b", "they've", text)
        if text and text[0].islower():
            text = text[0].upper() + text[1:]
        if len(text) > 220:
            text = text[:217].rsplit(" ", 1)[0] + "…"
        return text

    def _collect(*, respect_global: bool) -> list[str]:
        out: list[str] = []
        seen: set[str] = set()
        for member in members:
            text = _rewrite(getattr(member, "raw_text", "") or "")
            if not text:
                continue
            key = _paraphrase_dedupe_key(text)
            if not key or key in seen:
                continue
            if respect_global and key in used_refs:
                continue
            seen.add(key)
            out.append(text)
            if len(out) >= 3:
                break
        return out

    out = _collect(respect_global=True)
    if not out:
        # Prefer a real member quote over identical stub templates across themes
        out = _collect(respect_global=False)[:1]
    for text in out:
        used_refs.add(_paraphrase_dedupe_key(text))
    if out:
        return out
    for alt in _alts_for(name, slug):
        key = _paraphrase_dedupe_key(alt)
        if not key or key in used_refs:
            continue
        used_refs.add(key)
        return [alt]
    stub = paraphrase_stub(name)
    used_refs.add(_paraphrase_dedupe_key(stub))
    return [stub]


def _groq_name(client: GroqClient, texts: list[str]) -> tuple[str, str, str]:
    prompts = load_prompts()
    sample = "\n".join(f"- {t[:240]}" for t in texts[:12])
    raw = client.chat(
        [
            {"role": "system", "content": str(prompts.get("cluster_name_system") or "")},
            {"role": "user", "content": sample},
        ],
        temperature=0.1,
    )
    payload = parse_json_object(raw)
    slug = _slugify(str(payload.get("slug") or payload.get("name") or "other"))
    name = str(payload.get("name") or slug.replace("_", " ")).strip()[:80]
    sev = str(payload.get("severity") or "medium").lower()
    if sev not in {"high", "medium", "low"}:
        sev = "medium"
    return slug, name, sev


def _name_cluster(
    texts: list[str],
    *,
    stub: bool,
    client: Optional[GroqClient],
) -> tuple[str, str, str]:
    if stub or client is None or not client.available:
        return infer_slug(texts)
    try:
        return _groq_name(client, texts)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Cluster name Groq failed: %s", exc)
        return infer_slug(texts)


def _unique_theme_id(question_id: str, slug: str, used: set[str]) -> str:
    base = f"{question_id}_{slug}"
    if base not in used:
        used.add(base)
        return base
    idx = 2
    while f"{base}_{idx}" in used:
        idx += 1
    theme_id = f"{base}_{idx}"
    used.add(theme_id)
    return theme_id


def _build_theme(
    *,
    theme_id: str,
    question_id: str,
    name: str,
    members: list[ReviewDocument],
    bucket_size: int,
    severity: str,
    used_examples: set[str] | None = None,
    slug: str | None = None,
) -> SubTheme:
    sources = sorted({m.source.value for m in members})
    sev = severity if severity in {"high", "medium", "low"} else "medium"
    return SubTheme(
        sub_theme_id=theme_id,
        question_id=question_id,
        name=name,
        share_of_bucket=round(len(members) / max(bucket_size, 1), 3),
        source_diversity=len(sources),
        sources=sources,
        frequency=FrequencyLabel.MEDIUM,
        severity=FrequencyLabel(sev),
        impact_score=0.0,
        segment_skew=sorted(
            {m.segment_hint.value for m in members if m.segment_hint.value != "unknown"}
        ),
        paraphrased_examples=paraphrase_from_members(
            members, name, used=used_examples, slug=slug
        ),
        hypothesis=f"{name} may delay 30-day wishlist conversion.",
        interview_probes=[f"When you saved something recently, did {name.lower()} come up?"],
        chunk_ids=[m.id for m in members],
    )


def _attach(updated: dict[str, ReviewDocument], doc_id: str, theme_id: str, question_id: str | None = None) -> None:
    doc = updated[doc_id]
    ids = list(doc.sub_theme_ids)
    if theme_id not in ids:
        ids.append(theme_id)
    qs = list(doc.research_questions)
    if question_id and question_id not in qs:
        qs.append(question_id)
    updated[doc_id] = doc.model_copy(update={"sub_theme_ids": ids, "research_questions": qs})


def cluster_and_score(
    documents: list[ReviewDocument],
    *,
    stub: bool,
    client: Optional[GroqClient] = None,
) -> tuple[list[ReviewDocument], list[SubTheme], str]:
    proc = load_processing()
    clustering = proc.get("clustering") or {}
    dist = float(clustering.get("distance_threshold", 0.35))
    min_size = int(clustering.get("min_cluster_size", 3))
    leftover_slug = str(clustering.get("leftover_slug", "other"))
    min_q10 = int(load_retrieval().get("q10_min_independent_sources") or 3)

    n_sources = len({d.source.value for d in documents}) or 1
    backend = "ngram"
    vectors_all: list[list[float]] | None = None
    if not stub:
        vectors_all = try_minilm_vectors([d.raw_text for d in documents]) if documents else None
        if vectors_all is not None:
            backend = "minilm"

    doc_index = {d.id: i for i, d in enumerate(documents)}
    by_q: dict[str, list[ReviewDocument]] = defaultdict(list)
    for doc in documents:
        for qid in doc.research_questions:
            if qid.startswith("q10"):
                continue
            by_q[qid].append(doc)

    updated: dict[str, ReviewDocument] = {d.id: d for d in documents}
    themes: list[SubTheme] = []
    slug_sources: dict[str, set[str]] = defaultdict(set)
    slug_members: dict[str, list[ReviewDocument]] = defaultdict(list)
    slug_meta: dict[str, tuple[str, str]] = {}
    used_examples: set[str] = set()

    for qid, bucket in by_q.items():
        texts = [d.raw_text for d in bucket]
        bucket_vectors = None
        if vectors_all is not None:
            bucket_vectors = [vectors_all[doc_index[d.id]] for d in bucket]
        if stub or bucket_vectors is None:
            kept, leftover_idxs = keyword_groups(texts, min_cluster_size=min_size)
            # Merge tiny leftover via n-gram so we do not drop signal
            if leftover_idxs and len(leftover_idxs) >= min_size:
                sub_texts = [texts[i] for i in leftover_idxs]
                sub_kept, sub_left = agglomerative_groups(
                    sub_texts,
                    distance_threshold=dist,
                    min_cluster_size=min_size,
                    vectors=None,
                )
                kept.extend([[leftover_idxs[j] for j in group] for group in sub_kept])
                leftover_idxs = [leftover_idxs[j] for j in sub_left]
        else:
            kept, leftover_idxs = agglomerative_groups(
                texts,
                distance_threshold=dist,
                min_cluster_size=min_size,
                vectors=bucket_vectors,
            )
        used_ids: set[str] = set()
        bucket_themes: list[SubTheme] = []

        def add_group(idxs: list[int], *, leftover: bool) -> None:
            members = [bucket[i] for i in idxs]
            member_texts = [m.raw_text for m in members]
            canonical, name, sev = _name_cluster(member_texts, stub=stub or leftover, client=client)
            if leftover:
                slug, display = leftover_slug, "Other"
            else:
                slug, display = canonical, name
            theme_id = _unique_theme_id(qid, slug, used_ids)
            st = _build_theme(
                theme_id=theme_id,
                question_id=qid,
                name=display,
                members=members,
                bucket_size=len(bucket),
                severity=sev if not leftover else "low",
                used_examples=used_examples,
                slug=slug,
            )
            bucket_themes.append(st)
            if leftover:
                for m in members:
                    c_slug, c_name, c_sev = infer_slug([m.raw_text])
                    if c_slug in {leftover_slug, "other"}:
                        continue
                    slug_sources[c_slug].add(m.source.value)
                    slug_members[c_slug].append(m)
                    slug_meta.setdefault(c_slug, (c_name, c_sev))
            elif canonical not in {leftover_slug, "other"}:
                slug_sources[canonical].update(m.source.value for m in members)
                slug_members[canonical].extend(members)
                slug_meta[canonical] = (name, sev)
            for m in members:
                _attach(updated, m.id, theme_id)

        for idxs in kept:
            add_group(idxs, leftover=False)
        if leftover_idxs:
            add_group(leftover_idxs, leftover=True)

        score_and_rank(bucket_themes, n_sources=n_sources)
        themes.extend(bucket_themes)

    q10: list[SubTheme] = []
    for slug, sources in slug_sources.items():
        if slug in {leftover_slug, "other"}:
            continue
        if len(sources) < min_q10:
            continue
        members: list[ReviewDocument] = []
        seen: set[str] = set()
        for m in slug_members[slug]:
            if m.id in seen:
                continue
            seen.add(m.id)
            members.append(updated[m.id])
        name, sev = slug_meta.get(slug, infer_slug([m.raw_text for m in members])[1:])
        share = len(members) / max(len(documents), 1)
        q10.append(
            SubTheme(
                sub_theme_id=f"q10_unmet_needs_{slug}",
                question_id="q10_unmet_needs",
                name=name,
                share_of_bucket=round(share, 3),
                source_diversity=len(sources),
                sources=sorted(sources),
                frequency=FrequencyLabel.HIGH,
                severity=FrequencyLabel(sev if sev in {"high", "medium", "low"} else "high"),
                impact_score=round(
                    0.35 * share + 0.4 * (len(sources) / n_sources) + 0.25 * severity_num(sev),
                    3,
                ),
                paraphrased_examples=paraphrase_from_members(
                    members, name, used=used_examples, slug=slug
                ),
                hypothesis="Recurs across independent sources. Treat as a high-confidence unmet need.",
                interview_probes=["Have you seen this same gap on more than one channel?"],
                chunk_ids=[m.id for m in members],
            )
        )
    q10.sort(key=lambda t: t.impact_score, reverse=True)
    for rank, theme in enumerate(q10, start=1):
        theme.impact_rank = rank
        for mid in theme.chunk_ids:
            _attach(updated, mid, theme.sub_theme_id, "q10_unmet_needs")
    themes.extend(q10)

    return list(updated.values()), themes, backend
