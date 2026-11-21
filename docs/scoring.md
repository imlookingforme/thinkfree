# ThinkFree Scoring Specification & Pure Math Models

This document defines the mathematical foundations for ThinkFree's effort engine, cognitive reliance metrics, and mastery tracking. All implementations are pure functions with 100% deterministic unit test verification in `apps/api/tests/test_scoring_pure.py`.

---

## 1. Effort Score Formulation ($E$)

AI guidance is physically locked until the student has exerted genuine cognitive effort. The effort score $E \in [0, 1]$ is modeled using a saturated exponential decay function:

$$
E = 1 - \exp\left( -\left( a \cdot \frac{t}{T_{\text{exp}}} + b \cdot \frac{m}{M_{\text{exp}}} + c \cdot \frac{r}{R_{\text{exp}}} + d \cdot \frac{s}{S_{\text{exp}}} \right) \right)
$$

### Parameter Definitions
- **$t$**: Active seconds spent on the problem (in-focus editing, testing; inactivity gaps $>60\text{s}$ excluded).
- **$m$**: Meaningful character edits (net typed characters, excluding pasted blocks).
- **$r$**: Test executions and sandbox runs.
- **$s$**: Distinct logical steps identified in the scratchpad/answer.
- **Weights ($a + b + c + d = 1.0$)**:
  - $a = 0.35$ (Time weight)
  - $b = 0.25$ (Meaningful edits weight)
  - $c = 0.15$ (Code runs weight)
  - $d = 0.25$ (Steps weight)

### Expectation Scaling by Problem Difficulty ($\beta$)
For a problem with Item Response Theory (IRT) difficulty $\beta$:
- $T_{\text{exp}} = 300 \cdot \beta$ seconds (5 minutes baseline at $\beta = 1.0$)
- $M_{\text{exp}} = 180 \cdot \beta$ characters
- $R_{\text{exp}} = \max(2, 3 \cdot \beta)$ runs
- $S_{\text{exp}} = \max(3, 4 \cdot \beta)$ steps

### Unlock Condition
AI unlocks **only when both criteria are met**:
$$
E \ge E_{\text{min}} \quad (\text{default } 0.35) \quad \text{AND} \quad t \ge t_{\text{min}} \quad (\text{default } 180\text{ seconds})
$$

### Worked Example (Matches Test Case `test_calculate_effort_score_moderate_activity`)
- Given: $t = 150\text{s}$, $m = 90$, $r = 0$, $s = 2$, $\beta = 1.0$:
  $$\text{Exponent} = 0.35 \cdot \frac{150}{300} + 0.25 \cdot \frac{90}{180} + 0.15 \cdot \frac{0}{3} + 0.25 \cdot \frac{2}{4}$$
  $$\text{Exponent} = 0.175 + 0.125 + 0.0 + 0.125 = 0.425$$
  $$E = 1 - \exp(-0.425) \approx 1 - 0.65377 = 0.3462$$
- Result: $E = 0.3462 < 0.35$. Unlock is cleanly rejected by server-authoritative state checks.

---

## 2. Help Cost & AI Reliance Score

### Ladder Weights ($w$)
| Tutor Rung | Description | Help Cost ($w$) |
|---|---|---|
| **Guide** | Socratic questioning | 0.15 |
| **Hint** | Concept / approach pointer | 0.35 |
| **Help** | Conceptual explanation with distinct worked example | 0.55 |
| **Critical Hint** | Next single step hint | 0.80 |

### Per-Problem Reliance ($r_p$)
$$
r_p = \min\left(1.0, \frac{\sum w(k)}{H_{\text{cap}}}\right) + (0.10 \text{ if unlocked via stuck declaration})
$$
Where $H_{\text{cap}} = 1.5$. A self-solve without AI guidance yields $r_p = 0.0$.

### AI Dependency Ratio (ADR)
Across a sliding window of the last $N$ problems:
$$
\text{ADR} = \frac{1}{N} \sum_{p=1}^{N} r_p
$$

### Exponentially Weighted Moving Average Reliance ($R_t$)
$$
R_t = \lambda \cdot r_t + (1 - \lambda) \cdot R_{t-1}, \quad \lambda = 0.2
$$

---

## 3. Independent Thinking Score (ITS, 0-100)

$$
\text{ITS} = 100 \cdot (0.30 \cdot U + 0.30 \cdot V + 0.20 \cdot P + 0.20 \cdot Q)
$$
Where:
- **$U$**: Unaided success rate (problems solved with $\text{help\_cost} \le 0.35$).
- **$V$**: Mean validation score (rubric coverage score on explanations/isomorphic variants).
- **$P$**: Persistence ($E$ achieved before first tutor request).
- **$Q$**: Spaced retention accuracy on re-test reviews.
