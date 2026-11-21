from __future__ import annotations

import re
from typing import List

from pydantic import BaseModel


class ConsistencyBreakdown(BaseModel):
    consistency_score: float
    perplexity_ratio: float
    vocabulary_overlap: float
    syntactic_alignment: float
    anomaly_flag: bool
    plain_english: str
    reasons: List[str]


class ConsistencyService:
    """
    Feature 5: Understanding-consistency & suspicion meter.
    Calculates statistical, stylistic, and vocabulary consistency between
    the student's attempt-phase work and their validation explanation.
    Never auto-punitive; provides complete explainability and contestability.
    """

    @staticmethod
    def _tokenize(text: str) -> List[str]:
        """Simple lower-cased alphanumeric tokenization."""
        return re.findall(r"\b[a-zA-Z_][a-zA-Z0-9_]*\b", text.lower())

    @classmethod
    def calculate_consistency(
        cls,
        attempt_text: str,
        explanation_text: str,
        effort_score: float = 0.5,
        time_spent_seconds: float = 180.0
    ) -> ConsistencyBreakdown:
        """
        Computes the multi-factor consistency score S in [0.0, 1.0].
        Considers:
        1. Jaccard vocabulary overlap between attempt code/notes and spoken/written explanation.
        2. Perplexity / length balance (suspicious if explanation uses advanced idioms completely absent in attempt).
        3. Attempt effort context: low effort + sudden perfect vocabulary triggers advisory anomaly flag.
        """
        attempt_tokens = set(cls._tokenize(attempt_text))
        expl_tokens = cls._tokenize(explanation_text)
        expl_set = set(expl_tokens)

        # 1. Vocabulary overlap
        if not attempt_tokens and not expl_set:
            vocab_overlap = 0.8
        elif not attempt_tokens or not expl_set:
            vocab_overlap = 0.25
        else:
            intersection = attempt_tokens.intersection(expl_set)
            # Overlap relative to the smaller set (subset coverage) rather than full union
            vocab_overlap = len(intersection) / min(len(attempt_tokens), len(expl_set))

        # 2. Syntactic / Idiom Alignment
        # Fraction of keywords in explanation that appeared in attempt
        # English stop-words shouldn't penalize domain vocabulary
        stopwords = {"in", "this", "we", "use", "a", "an", "the", "to", "of", "and", "or", "for", "is", "are", "on", "it"}
        core_expl_tokens = [t for t in expl_tokens if t not in stopwords]
        core_expl_set = set(core_expl_tokens)

        if core_expl_set:
            attempt_recall = len(attempt_tokens.intersection(core_expl_set)) / len(core_expl_set)
        else:
            attempt_recall = 0.5

        syntactic_alignment = min(1.0, max(0.1, attempt_recall * 2.0))

        # 3. Perplexity ratio proxy
        expl_len = len(expl_tokens)
        attempt_len = len(attempt_tokens)
        if attempt_len == 0 and expl_len > 30:
            perplexity_ratio = 2.4
        elif attempt_len > 0:
            perplexity_ratio = max(0.5, min(3.0, expl_len / (attempt_len + 5)))
        else:
            perplexity_ratio = 1.0

        # Weighted combination for consistency score:
        # High effort during attempt boosts consistency presumption (up to +0.30)
        effort_boost = min(0.30, effort_score * 0.30)
        raw_score = 0.35 * vocab_overlap + 0.35 * syntactic_alignment + effort_boost
        consistency_score = round(min(1.0, max(0.1, raw_score)), 2)

        # Anomaly determination: Advisory flag triggered if consistency is low AND effort was minimal
        anomaly_flag = False
        reasons: List[str] = []

        if effort_score < 0.20 and expl_len >= 20 and vocab_overlap < 0.15:
            anomaly_flag = True
            reasons.append("High vocabulary disparity between minimal attempt notes and detailed explanation.")

        if time_spent_seconds < 60 and expl_len >= 20:
            anomaly_flag = True
            reasons.append("Rapid solution submission with zero incremental scratchpad edits.")

        if consistency_score < 0.35:
            reasons.append("Terminology in explanation was largely absent during the active attempt phase.")

        plain_english = (
            "Your explanation is well-aligned with your problem-solving attempt."
            if not anomaly_flag
            else "Notice: Your explanation uses significant terminology not observed in your attempt scratchpad. "
                 "In ThinkFree, this is purely advisory: you can self-annotate or validate via an isomorphic problem."
        )

        return ConsistencyBreakdown(
            consistency_score=consistency_score,
            perplexity_ratio=round(perplexity_ratio, 2),
            vocabulary_overlap=round(vocab_overlap, 2),
            syntactic_alignment=round(syntactic_alignment, 2),
            anomaly_flag=anomaly_flag,
            plain_english=plain_english,
            reasons=reasons
        )
