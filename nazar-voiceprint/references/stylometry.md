# Stylometry: what a writing fingerprint actually is

Confidence tags: [V] checked at the source, [S] secondary sourcing of a primary text, [UNVERIFIED] check before relying on it.

## 1. The unconscious layer: function words
- **Mosteller & Wallace (1963), "Inference in an Authorship Problem," *JASA* 58(302):275–309** [S]. Attributed the 12 disputed Federalist Papers to Madison using function-word frequencies (*the, of, and, but, upon*) in a Bayesian model. They tried sentence length first, and it didn't separate Hamilton from Madison at all.
- **Why function words:** they're so frequent and grammaticalised that writers don't consciously control their rate. A writer chooses content words and phrasing, but nobody tracks their own ratio of "upon" to "on". Topic words, register and flourishes are the opposite: chosen consciously, dependent on genre, and easy to imitate. An imitator, human or AI, copies the surface and misses the signature [S].
- **Burrows's Delta (2002), *Literary and Linguistic Computing* 17(3):267–287** [S]. Take the most frequent words, z-score each word's frequency per text, and compute the mean absolute difference between a test text and each candidate author. The lowest Delta wins. Z-scoring matters because raw frequencies fall off a cliff from common to rare words. Accuracy drops as the word list shrinks from about 150 words to about 40, so the signal needs breadth, not a few pet words.
- **What `engine/analyze.py` does with this:** it profiles one person's texts against a general-English baseline and against each other. It doesn't run authorship attribution, which would need several candidate authors' corpora. Only an English baseline ships with it. For other languages the layer is skipped and the output says why.

## 2. Feature classes used in the attribution literature
From the Stamatatos 2009 survey and the Koppel/Schler work [S; category boundaries approximate]:
- **Lexical:** word length, vocabulary richness (type-token ratio), and function-word lists of up to about 480 words.
- **Syntactic:** part-of-speech n-grams and habitual syntactic "errors".
- **Character and formatting:** character n-grams, punctuation habits, spelling idiosyncrasies, paragraph length.
- **Sentence length:** report the variance and the shape of the distribution, not just the mean. Mosteller and Wallace's own negative result shows the mean alone barely discriminates.

## 3. The discourse layer (where a word-counter is blind)
- **Biber (1988), *Variation across Speech and Writing*** [S]. 67 linguistic features across 23 genres, factor-analysed into six dimensions. The four attributed with confidence are:
  - **involved vs. informational** production (affective and interactional at one pole, dense exact content at the other);
  - **narrative vs. non-narrative** concerns;
  - **abstract vs. non-abstract** information;
  - **on-line informational elaboration**.
- The remaining two dimension labels need the book itself to pin down [UNVERIFIED].
- **Use this layer for the qualitative read:** how the person hedges (epistemic modality), how they open an argument, how they transition, how they close. This is where argument structure lives.

## 4. Is there one voice? (the honest answer: mixed)
- A 112-idiolect cross-genre study found **very low** individual stability when people switched genres. A separate study found that switching between written and spoken mode causes the single biggest shift, bigger than topic or time [S, Aston].
- In the other direction, a Spanish study of epistemic modality found that idiolectal hedging and indirectness markers **do** stay stable across genre and mode [S].
- A recent stability benchmark found about 80% of handcrafted features have positive cross-genre stability. It warns that stability has to be checked for each genre pair [preprint, arXiv 2611.07111].
- **Rule:** never assume one invariant voice. Test each feature across the person's own samples (`analyze.py a b`). Features at the level of function words and discourse markers transfer better than lexical or topic features.

## 5. Existing tools (proof this is implementable, not theoretical)
- **stylo** (R; Eder, Rybicki & Kestemont, *The R Journal* 2016): word and character n-grams, PCA and cluster analysis, bootstrap consensus trees, and rolling classification to flag mixed authorship within a single text.
- **JGAAP** (Juola, Duquesne; Java): a pipeline of canonicisers, culling, event sets and distance methods, including Burrows's Delta. Its documentation is stale (v5.1, 2013).

## Sources
Mosteller & Wallace 1963 (JASA) · Burrows 2002 (LLC 17:3) · Stamatatos 2009 survey · Koppel/Schler (JASIST; IJCAI idiosyncrasy paper) · Biber 1988 · Aston University cross-genre idiolect studies · arxiv.org/html/2611.07111 · arxiv.org/pdf/2310.00436 · journal.r-project.org/articles/RJ-2016-007 · JGAAP
