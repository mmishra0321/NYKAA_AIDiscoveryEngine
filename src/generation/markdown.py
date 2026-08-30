"""Render catalog_summary.md — paraphrases only, no verbatim review dumps."""

from __future__ import annotations

from src.models.schemas import CatalogQuestion, CatalogReport, SubTheme


def _theme_md(theme: SubTheme) -> list[str]:
    lines = [
        f"#### {theme.impact_rank or '-'} {theme.name}",
        "",
        f"Share of bucket: **{theme.share_of_bucket:.0%}** · source diversity: **{theme.source_diversity}** "
        f"({', '.join(theme.sources) or '—'}) · frequency: {theme.frequency.value if hasattr(theme.frequency, 'value') else theme.frequency} "
        f"· severity: {theme.severity.value if hasattr(theme.severity, 'value') else theme.severity} "
        f"· impact: {theme.impact_score}",
        "",
    ]
    if theme.paraphrased_examples:
        lines.append("Paraphrase: " + theme.paraphrased_examples[0])
        lines.append("")
    if theme.hypothesis:
        lines.append(f"Hypothesis: {theme.hypothesis}")
        lines.append("")
    return lines


def _question_md(q: CatalogQuestion) -> list[str]:
    lines = [
        f"## {q.id} — {q.question}",
        "",
        f"Confidence: **{q.confidence}** · evidence chunks: **{q.evidence_count}** · sub-themes: **{q.themes_count}**",
        "",
        q.summary,
        "",
    ]
    if q.sub_themes:
        lines.append("### Sub-themes (ranked by impact on 30-day wishlist purchase)")
        lines.append("")
        for theme in q.sub_themes:
            lines.extend(_theme_md(theme))
    if q.implications:
        lines.append("### Implications (observed vs hypothesis)")
        lines.append("")
        for item in q.implications:
            lines.append(f"- {item}")
        lines.append("")
    if q.interview_probes:
        lines.append("### Interview probes")
        lines.append("")
        for item in q.interview_probes:
            lines.append(f"- {item}")
        lines.append("")
    if q.data_gaps:
        lines.append("### Data gaps")
        lines.append("")
        lines.append(q.data_gaps)
        lines.append("")
    return lines


def render_markdown(report: CatalogReport) -> str:
    corpus = report.corpus or {}
    lines = [
        "# Nykaa Fashion — Wishlist discovery catalog",
        "",
        f"KPI: **{report.kpi}** · generated {report.generated_at}",
        "",
        f"Corpus: **{corpus.get('relevant', 0)}** wishlist_signal · "
        f"**{corpus.get('noise', 0)}** noise · sources: {corpus.get('sources') or {}}",
        "",
        "User-facing examples are paraphrased. Monetary incentives are out of scope as the conversion mechanism.",
        "",
    ]
    for q in report.questions:
        lines.extend(_question_md(q))
        lines.append("---")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"
