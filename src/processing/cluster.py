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
        f"Users describe {name.lower()} after liking or saving a Nykaa Fashion item "
        "— enough to stall a 30-day purchase."
    )


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
        paraphrased_examples=[paraphrase_stub(name)],
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
                paraphrased_examples=[paraphrase_stub(name)],
                hypothesis="Recurs across independent sources — treat as a high-confidence unmet need.",
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
