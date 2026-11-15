#!/usr/bin/env python3
"""
voiceprint/engine/analyze.py — the quantitative layer of a writing-voice profile.

Computes the feature types the stylometry literature treats as a genuine,
largely-unconscious fingerprint (Mosteller & Wallace 1963; Burrows 2002;
Biber 1988) — see ../references/stylometry.md for the citations and what
each feature actually measures and why.

Two kinds of feature here:
  1. Language-agnostic (sentence rhythm, punctuation, paragraphing, lexical
     richness, repeated phrases/refrains) — these work on any language,
     because they only need to find sentence/word/phrase boundaries.
  2. Function-word frequency — the single most theoretically-grounded
     "unconscious fingerprint" feature, but it needs a baseline frequency
     table for the text's language. Only an English baseline ships here
     (see FUNCTION_WORDS_EN below). Pass --lang other-than-en to skip it
     honestly instead of reporting meaningless numbers — do not bolt an
     English baseline onto non-English text.

This script does NOT do authorship attribution (that needs a Burrows'
Delta comparison across several candidate authors' corpora). It profiles
ONE person's own texts against each other and against a general-English
reference, which is what the voiceprint skill actually needs: finding
what's stable across a person's own samples, not telling them apart from
someone else.
"""
import argparse
import json
import os
import re
import statistics
import sys
from collections import Counter

# A small, standard set of high-frequency English function words — the
# class of word Mosteller & Wallace used because writers don't consciously
# track their own rate of "upon" vs "on". Approximate relative frequencies
# (per 1,000 words) from general published English word-frequency counts;
# treat as an illustrative baseline, not a corpus-matched reference corpus.
FUNCTION_WORDS_EN = {
    "the": 55.0, "of": 30.0, "and": 25.0, "to": 25.0, "a": 20.0, "in": 18.0,
    "that": 10.0, "is": 9.0, "was": 8.0, "for": 7.5, "on": 6.5, "are": 5.0,
    "with": 6.0, "as": 5.5, "but": 4.0, "it": 9.0, "be": 5.0, "at": 4.5,
    "by": 4.0, "this": 4.5, "have": 4.0, "from": 4.0, "or": 3.5, "had": 2.5,
    "not": 4.0, "which": 2.5, "were": 2.5, "we": 3.0, "they": 3.0, "has": 2.0,
    "upon": 0.3, "whilst": 0.1, "however": 1.0, "although": 0.7, "so": 3.5,
    "if": 3.0, "because": 1.2, "than": 1.5, "then": 2.0, "when": 2.5,
}

WORD_RE = re.compile(r"[A-Za-z']+|[ऀ-ॿ]+")  # Latin words or Devanagari runs
SENT_SPLIT_RE = re.compile(r"[.!?…]+[\s]*|\n+")


def load(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def tokenize(text):
    return [w.lower() for w in WORD_RE.findall(text)]


def split_sentences(text):
    # Collapse the "/ " refrain-style separators some scripts use into a
    # soft break too, so e.g. "Walk / Stop / Smile please" isn't counted
    # as one 6-word sentence.
    text = text.replace(" / ", ". ")
    parts = [p.strip() for p in SENT_SPLIT_RE.split(text)]
    return [p for p in parts if p]


def sentence_length_stats(sentences):
    lengths = [len(tokenize(s)) for s in sentences if tokenize(s)]
    if not lengths:
        return {}
    return {
        "n_sentences": len(lengths),
        "mean_words": round(statistics.mean(lengths), 2),
        "stdev_words": round(statistics.pstdev(lengths), 2) if len(lengths) > 1 else 0.0,
        "min_words": min(lengths),
        "max_words": max(lengths),
        # Mosteller & Wallace's own negative result: mean length alone
        # barely discriminates authors. Variance/shape is the more useful
        # signal, so we report both and flag high-variance writing here.
        "rhythm": "short, flat, even" if statistics.pstdev(lengths) < 3 else
                  "mixed — short bursts against longer run-ons" if len(lengths) > 1 else "n/a",
    }


def punctuation_profile(text, n_words):
    if n_words == 0:
        return {}
    counts = {
        "ellipses_per_1000w": text.count("...") + text.count("…"),
        "question_marks_per_1000w": text.count("?"),
        "exclamations_per_1000w": text.count("!"),
        "em_dashes_per_1000w": text.count("—") + text.count(" - "),
        "semicolons_per_1000w": text.count(";"),
        "slash_breaks_per_1000w": text.count(" / "),
    }
    return {k: round(v * 1000 / n_words, 1) for k, v in counts.items()}


def paragraph_stats(text):
    paras = [p for p in re.split(r"\n\s*\n|\n", text) if p.strip()]
    lengths = [len(tokenize(p)) for p in paras if tokenize(p)]
    if not lengths:
        return {}
    return {
        "n_paragraphs": len(lengths),
        "mean_words_per_paragraph": round(statistics.mean(lengths), 1),
    }


def lexical_richness(tokens):
    if not tokens:
        return {}
    return {"type_token_ratio": round(len(set(tokens)) / len(tokens), 3), "n_tokens": len(tokens)}


def function_word_profile(tokens, lang):
    if lang != "en":
        return {"skipped": f"no function-word baseline for lang={lang!r} — "
                            "add one to FUNCTION_WORDS_EN's sibling table before trusting this layer; "
                            "language-agnostic features below are still valid."}
    n = len(tokens)
    if n == 0:
        return {}
    counts = Counter(tokens)
    deviations = {}
    for w, baseline_per_1000 in FUNCTION_WORDS_EN.items():
        observed_per_1000 = counts.get(w, 0) * 1000 / n
        if baseline_per_1000 > 0:
            deviations[w] = round((observed_per_1000 - baseline_per_1000) / baseline_per_1000, 2)
    # Largest relative deviations are the most distinctive habits.
    ranked = sorted(deviations.items(), key=lambda kv: abs(kv[1]), reverse=True)[:10]
    return {"most_distinctive_function_words": [
        {"word": w, "relative_deviation": d, "direction": "over-uses" if d > 0 else "under-uses"}
        for w, d in ranked
    ]}


def find_refrains(text, min_len=2, max_len=5, min_count=2):
    """Language-agnostic repeated-phrase / refrain detector.

    Doesn't need a baseline — just counts repeated n-grams. This is what
    catches a device like a script's recurring "Walk / Stop / Smile
    please" beat: the kind of structural habit a word-frequency table
    would never surface.
    """
    tokens = tokenize(text)
    found = Counter()
    for n in range(min_len, max_len + 1):
        for i in range(len(tokens) - n + 1):
            gram = tuple(tokens[i:i + n])
            found[gram] += 1
    refrains = [(gram, c) for gram, c in found.items() if c >= min_count]
    # Score by (repeats - 1) * length so longer, more-repeated phrases rank highest,
    # and drop grams that are just a sub-phrase of a longer refrain already kept.
    refrains.sort(key=lambda gc: (gc[1] - 1) * len(gc[0]), reverse=True)
    kept, covered = [], set()
    for gram, c in refrains:
        if gram in covered:
            continue
        kept.append({"phrase": " ".join(gram), "repeats": c})
        covered.update(gram)
        if len(kept) >= 8:
            break
    return kept


def analyze(path, lang="en"):
    text = load(path)
    tokens = tokenize(text)
    sentences = split_sentences(text)
    return {
        "source": path,
        "lang": lang,
        "n_words": len(tokens),
        "sentence_rhythm": sentence_length_stats(sentences),
        "punctuation": punctuation_profile(text, len(tokens)),
        "paragraphing": paragraph_stats(text),
        "lexical_richness": lexical_richness(tokens),
        "function_words": function_word_profile(tokens, lang),
        "refrains_and_repetition": find_refrains(text),
    }


def diff_profiles(a, b):
    """Rough cross-sample stability check: which numeric features sit close
    together across two of the person's own texts (candidate core voice)
    vs. which differ a lot (likely genre-driven, don't force it elsewhere).
    Per the research: cross-genre idiolect stability is genuinely mixed —
    this is why the skill tests it empirically instead of assuming it.
    """
    def flatten(d, prefix=""):
        out = {}
        for k, v in d.items():
            if isinstance(v, dict):
                out.update(flatten(v, f"{prefix}{k}."))
            elif isinstance(v, (int, float)):
                out[f"{prefix}{k}"] = v
        return out
    fa, fb = flatten(a), flatten(b)
    rows = []
    for k in sorted(set(fa) & set(fb)):
        va, vb = fa[k], fb[k]
        denom = max(abs(va), abs(vb), 1e-9)
        rel_diff = abs(va - vb) / denom
        rows.append({"feature": k, "a": va, "b": vb,
                     "stable": rel_diff < 0.25})
    return rows


def corpus_pattern(profiles):
    """Across a whole archive (3+ documents): which features are the person,
    and which are just the document. Low coefficient of variation across their
    own texts = a stable habit worth putting in the pattern; high = it moves
    with genre/topic, so leave it to the brief, not the voice."""
    def flatten(d, prefix=""):
        out = {}
        for k, v in d.items():
            if isinstance(v, dict):
                out.update(flatten(v, f"{prefix}{k}."))
            elif isinstance(v, (int, float)) and not isinstance(v, bool):
                out[f"{prefix}{k}"] = v
        return out
    skip = ("n_words", "lexical_richness.n_tokens", "sentence_rhythm.n_sentences", "paragraphing.n_paragraphs")
    flat = [flatten(p) for p in profiles]
    keys = sorted(set.intersection(*(set(f) for f in flat)) - set(skip))
    rows = []
    for k in keys:
        vals = [f[k] for f in flat]
        mean = statistics.mean(vals)
        sd = statistics.pstdev(vals)
        cv = sd / abs(mean) if abs(mean) > 1e-9 else (0.0 if sd < 1e-9 else float("inf"))
        rows.append({"feature": k, "mean": round(mean, 2), "spread": round(sd, 2),
                     "verdict": "habit" if cv < 0.3 else "varies" if cv < 0.7 else "document-driven"})
    return {"n_documents": len(profiles), "features": rows,
            "phrases_across_documents": cross_document_phrases([p["source"] for p in profiles])}


def cross_document_phrases(paths, min_len=2, max_len=4):
    """Signature moves show up once per document, not many times inside one:
    an opener, a sign-off, a pet transition. Count in how many documents each
    phrase appears (document frequency), keep those in at least half the
    archive, drop phrases made only of function words, and drop sub-phrases
    of a longer kept phrase."""
    docs = [tokenize(load(p)) for p in paths]
    df = Counter()
    for toks in docs:
        seen = set()
        for n in range(min_len, max_len + 1):
            for i in range(len(toks) - n + 1):
                seen.add(tuple(toks[i:i + n]))
        df.update(seen)
    need = max(2, (len(docs) + 1) // 2)
    fw = set(FUNCTION_WORDS_EN)
    cands = [(g, c) for g, c in df.items() if c >= need and not all(w in fw for w in g)]
    cands.sort(key=lambda gc: (gc[1], len(gc[0])), reverse=True)
    kept = []
    for g, c in cands:
        s = " ".join(g)
        if any(s in k["phrase"] for k in kept):
            continue
        kept.append({"phrase": s, "in_documents": c, "of": len(docs)})
        if len(kept) >= 10:
            break
    return kept


def expand(paths):
    out = []
    for p in paths:
        if os.path.isdir(p):
            out += sorted(os.path.join(p, f) for f in os.listdir(p) if f.endswith((".txt", ".md")))
        else:
            out.append(p)
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("files", nargs="+", help="text files or a corpus folder (from ingest.py); 1 = profile, 2 = diff, 3+ = archive pattern")
    ap.add_argument("--lang", default="en", help="'en' to include the function-word layer, anything else skips it honestly")
    ap.add_argument("--json", action="store_true", help="print raw JSON instead of a human-readable report")
    a = ap.parse_args()

    files = expand(a.files)
    profiles = [analyze(f, a.lang) for f in files]

    if len(profiles) >= 3:
        pat = corpus_pattern(profiles)
        if a.json:
            print(json.dumps({"pattern": pat, "profiles": profiles}, indent=2, ensure_ascii=False))
        else:
            print(f"\n=== archive pattern across {pat['n_documents']} documents ===")
            for verdict in ("habit", "varies", "document-driven"):
                rows = [r for r in pat["features"] if r["verdict"] == verdict]
                if rows:
                    print(f"\n{verdict.upper()}:")
                    for r in rows:
                        print(f"  {r['feature']:42} {r['mean']:>8} ± {r['spread']}")
            if pat["phrases_across_documents"]:
                print("\nphrases that recur across documents (signature candidates):")
                for r in pat["phrases_across_documents"]:
                    print(f"  \"{r['phrase']}\" in {r['in_documents']} of {r['of']} documents")
        sys.exit(0)

    if a.json:
        out = {"profiles": profiles}
        if len(profiles) == 2:
            out["stability_diff"] = diff_profiles(profiles[0], profiles[1])
        print(json.dumps(out, indent=2, ensure_ascii=False))
    else:
        for p in profiles:
            print(f"\n=== {p['source']} ({p['n_words']} words) ===")
            print(json.dumps({k: v for k, v in p.items() if k not in ("source", "n_words")},
                              indent=2, ensure_ascii=False))
        if len(profiles) == 2:
            print(f"\n=== stability across {a.files[0]} vs {a.files[1]} ===")
            for row in diff_profiles(*profiles):
                mark = "stable" if row["stable"] else "SHIFTS"
                print(f"  [{mark:6}] {row['feature']:40} {row['a']!s:>8} vs {row['b']!s:>8}")
