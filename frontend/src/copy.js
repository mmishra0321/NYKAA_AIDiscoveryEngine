/** Shared copy helpers for the discovery UI. */

export function cleanCopy(text) {
  let   out = String(text || "")
    .replace(/^Shopper:\s*/i, "")
    .replace(/^Directional interview\s*\d+\s*:\s*/i, "")
    .replace(
      /\s*Noted on a saved [a-z0-9-]+\.\s*(?:Happens every time I reopen the wishlist|This has been true for weeks now|Same story on ethnic and western pieces|Especially bad on festive wear|Worse after (?:I|they) heart something late at night|Friends said the same about Nykaa Fashion|(?:I|they) almost bought twice, then backed out|On Android it feels even slower to resolve|On iOS the wishlist looks prettier but still silent|(?:I|they) told myself I would buy after payday)\.?/gi,
      "",
    )
    .replace(
      /\s*Saved on Nykaa Fashion(?: wishlist)? with purchase intent[,.]?\s*(?:still unsure on fit\.?)?/gi,
      "",
    )
    .replace(/\u2014/g, ". ")
    .replace(/\u2013/g, "-")
    .replace(/\s*—\s*/g, ". ")
    .replace(/\s*–\s*/g, "-")
    .replace(/\s+\./g, ".")
    .replace(/\.\s*\./g, ".")
    .replace(/\s*\[\d+\]\s*$/g, "")
    .replace(/\s{2,}/g, " ")
    .trim();
  out = out.replace(/\.\s+([a-z])/g, (_, ch) => `. ${ch.toUpperCase()}`);
  return out;
}

/** Normalize near-duplicate review lines for drawer dedupe. */
export function quoteDedupeKey(text) {
  return cleanCopy(text)
    .toLowerCase()
    .replace(/\binterview\s*\d+\b/g, "")
    .replace(/\bshopper\s*\d+\b/g, "")
    .replace(/\bnoted on a saved [a-z0-9-]+\.?/g, "")
    .replace(/\bsaved on nykaa fashion wishlist with purchase intent[,.]?\s*still unsure on fit\.?/g, "")
    .replace(/\bsaved on nykaa fashion with purchase intent\.?/g, "")
    .replace(/\bhappens every time i reopen the wishlist\.?/g, "")
    .replace(/\bthis has been true for weeks now\.?/g, "")
    .replace(/\bsame story on ethnic and western pieces\.?/g, "")
    .replace(/\bespecially bad on festive wear\.?/g, "")
    .replace(/\bworse after (i|they) heart something late at night\.?/g, "")
    .replace(/\bfriends said the same about nykaa fashion\.?/g, "")
    .replace(/\bi almost bought twice, then backed out\.?/g, "")
    .replace(/\bon android it feels even slower to resolve\.?/g, "")
    .replace(/\bon ios the wishlist looks prettier but still silent\.?/g, "")
    .replace(/\bi told myself i would buy after payday\.?/g, "")
    .replace(/[^a-z0-9\s]/g, " ")
    .replace(/\s+/g, " ")
    .trim()
    .slice(0, 160);
}

export function firstComment(detail) {
  const seen = new Set();
  for (const theme of detail?.sub_themes || []) {
    for (const example of theme.paraphrased_examples || []) {
      const quote = cleanCopy(example);
      if (!quote) continue;
      const key = quoteDedupeKey(quote);
      if (!key || seen.has(key)) continue;
      seen.add(key);
      return quote;
    }
  }
  const summary = cleanCopy(detail?.summary || "");
  if (/^Observed from \d+ retrieved chunks/i.test(summary)) return "";
  return summary;
}

export const SOURCE_ORDER = ["Play Store", "App Store", "Forum/Blogs", "Interviews"];
