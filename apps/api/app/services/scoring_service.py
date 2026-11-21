from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Dict, List, Optional, Tuple


class ScoringService:
    """
    Pure mathematical calculations for ThinkFree's behavioral analytics,
    Independent Thinking Score (ITS), AI Dependency Ratio (ADR),
    Bayesian Knowledge Tracing (BKT), and SM-2 Spaced Repetition.
    """

    # --- 1. RELIANCE & ADR METRICS ---

    @staticmethod
    def calculate_problem_reliance(help_cost: float, unlocked_via_stuck: bool = False, h_cap: float = 1.5) -> float:
        """
        Calculates per-problem reliance r_p in [0, 1].
        r_p = min(1.0, help_cost / H_cap) + (0.10 if unlocked via stuck declaration).
        Unaided solves have help_cost = 0.0 -> r_p = 0.0.
        """
        base_reliance = min(1.0, max(0.0, help_cost / h_cap))
        if unlocked_via_stuck:
            base_reliance += 0.10
        return min(1.0, round(base_reliance, 4))

    @staticmethod
    def calculate_adr(reliance_scores: List[float]) -> float:
        """
        AI Dependency Ratio over window of N problems.
        ADR = (1/N) * sum(r_p).
        """
        if not reliance_scores:
            return 0.0
        return round(sum(reliance_scores) / len(reliance_scores), 4)

    @staticmethod
    def calculate_ewma_reliance(history: List[float], lambda_param: float = 0.2) -> List[float]:
        """
        Exponentially weighted moving average of reliance:
        R_t = lambda * r_t + (1 - lambda) * R_{t-1}.
        """
        if not history:
            return []
        ewma_vals = [history[0]]
        for r_t in history[1:]:
            r_prev = ewma_vals[-1]
            ewma_vals.append(round(lambda_param * r_t + (1.0 - lambda_param) * r_prev, 4))
        return ewma_vals

    # --- 2. INDEPENDENT THINKING SCORE (ITS) ---

    @staticmethod
    def calculate_its(
        unaided_success_rate: float,
        mean_validation_coverage: float,
        persistence_effort: float,
        spaced_retention: float,
        weights: Optional[Dict[str, float]] = None
    ) -> float:
        """
        ITS = 100 * (0.30*U + 0.30*V + 0.20*P + 0.20*Q)
        U: unaided success rate (help_cost <= 0.35)
        V: mean validation score (coverage)
        P: persistence (mean effort E before first help request)
        Q: retention on spaced re-tests
        """
        w = weights or {"U": 0.30, "V": 0.30, "P": 0.20, "Q": 0.20}
        its = 100.0 * (
            w["U"] * max(0.0, min(1.0, unaided_success_rate)) +
            w["V"] * max(0.0, min(1.0, mean_validation_coverage)) +
            w["P"] * max(0.0, min(1.0, persistence_effort)) +
            w["Q"] * max(0.0, min(1.0, spaced_retention))
        )
        return round(min(100.0, max(0.0, its)), 1)

    # --- 3. BAYESIAN KNOWLEDGE TRACING (BKT) ---

    @staticmethod
    def update_bkt(
        p_known: float,
        is_correct: bool,
        help_cost: float = 0.0,
        s: float = 0.1,    # slip probability
        g: float = 0.2,    # guess probability
        tau: float = 0.15  # transition probability
    ) -> float:
        """
        Standard BKT with help-cost attenuation:
        If aided, effective correctness weight is reduced.
        P(L|c) = P(L)(1-s) / [P(L)(1-s) + (1-P(L))g]
        P(L|~c) = P(L)s / [P(L)s + (1-P(L))(1-g)]
        P(L_{t+1}) = P(L|obs) + (1 - P(L|obs)) * tau
        """
        p_l = max(0.01, min(0.99, p_known))

        # Attenuate correct signal if high help was used
        if is_correct:
            # High help cost reduces the credit of being correct
            help_penalty = min(0.6, help_cost * 0.4)
            effective_guess = min(0.8, g + help_penalty)
            num = p_l * (1.0 - s)
            denom = num + (1.0 - p_l) * effective_guess
            p_obs = num / denom if denom > 0 else p_l
        else:
            num = p_l * s
            denom = num + (1.0 - p_l) * (1.0 - g)
            p_obs = num / denom if denom > 0 else p_l

        # Learning step transition
        p_next = p_obs + (1.0 - p_obs) * tau
        return round(min(0.99, max(0.01, p_next)), 4)

    # --- 4. SM-2 SPACED REPETITION ---

    @staticmethod
    def update_sm2(
        interval_days: float,
        ease_factor: float,
        quality_score: int  # 0 to 5
    ) -> Tuple[float, float, datetime]:
        """
        Standard SM-2 algorithm:
        EF' = EF + (0.1 - (5 - q) * (0.08 + (5 - q) * 0.02))
        I_n = 1 if q < 3 else (1 if I==0 else (6 if I==1 else I * EF))
        """
        q = max(0, min(5, quality_score))
        # Update Ease Factor (min 1.3)
        new_ef = ease_factor + (0.1 - (5 - q) * (0.08 + (5 - q) * 0.02))
        new_ef = max(1.3, round(new_ef, 4))

        if q < 3:
            # Failure resets review interval
            new_interval = 1.0
        else:
            if interval_days <= 1.0:
                new_interval = 1.0
            elif interval_days <= 2.0:
                new_interval = 6.0
            else:
                new_interval = round(interval_days * new_ef, 1)

        next_review = datetime.utcnow() + timedelta(days=new_interval)
        return new_interval, new_ef, next_review

    # --- 5. STREAK CALCULATION ---

    @staticmethod
    def calculate_streak(active_dates: List[date], freeze_tokens_used: int = 0) -> int:
        """
        Consecutive days with self-solves (allowing 1 freeze token per week gap).
        """
        if not active_dates:
            return 0
        sorted_dates = sorted(set(active_dates), reverse=True)
        streak = 0
        current_date = date.today()

        # If today is not in active dates, check if yesterday was active
        if sorted_dates[0] < current_date - timedelta(days=1):
            return 0

        prev_day = sorted_dates[0]
        streak = 1
        freezes_left = max(0, 1 - freeze_tokens_used)

        for d in sorted_dates[1:]:
            delta = (prev_day - d).days
            if delta == 1:
                streak += 1
                prev_day = d
            elif delta == 2 and freezes_left > 0:
                # Use freeze token for 1 missed day
                streak += 2
                freezes_left -= 1
                prev_day = d
            else:
                break

        return streak
