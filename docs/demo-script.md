# ThinkFree Complete Product Demonstration Script

This script walks through the entire ThinkFree product for course evaluators, professors, and partners.

---

## 1. Concept Introduction (Screen 1: Dashboard)
1. **Open:** `http://localhost:5173/`
2. **Observe:**
   - **Independent Thinking Score (ITS):** Shows 82/100. Click the **ⓘ** icon to inspect the exact formula:
     $$\text{ITS} = 100 \times (0.30 U + 0.30 V + 0.20 P + 0.20 Q)$$
   - **AI Dependency Ratio (ADR):** Shows 0.19. Click the **ⓘ** icon to inspect the rolling window reliance metric.
   - **Today's Spaced Review Queue (SM-2):** Prompts the student to review due concepts (*Dynamic Programming*, *Calculus 101*).
   - **Concept Knowledge Tracing Heat-Grid:** P(Known) bars identifying weak concepts ($< 0.40$) and alerting on unmet prerequisites.
   - **Free Thinker Radar:** 5-axis visualization of cognitive independence.

---

## 2. Locked-AI Attempt Phase (Screen 2: Problem Attempt)
1. **Navigate to:** `http://localhost:5173/attempt/demo`
2. **Observe:**
   - The AI / Help button is **strictly locked** with a lock icon.
   - Active effort meter tracks typing, code edits, and test runs.
   - Fast Lane badge is active (if student has $\text{ITS} \ge 80$, lock timer is reduced to 60s).
3. **Trigger Stuck Declaration:**
   - Click **"I'm Stuck"**.
   - Note the word-count enforcement ($\ge 35$ words required) preventing careless bypass.
   - Enter your stuck explanation and unlock Socratic guidance.

---

## 3. Socratic Tutor Ladder with LeakGuard (Screen 3: Guided Mode)
1. **Navigate to:** `http://localhost:5173/guided/demo`
2. **Observe:**
   - **4 Socratic Rungs:** Guide ($w=0.15$), Hint ($w=0.35$), Help ($w=0.55$), Critical Hint ($w=0.80$).
   - Ask for code or full answers — observe **LeakGuard** intercepting giveaways with the green *"LeakGuard Verified: No Direct Code/Numeric Giveaway"* badge.
   - Monaco code editor with live sandbox test runs.

---

## 4. Understanding Validation & Teach-Back (Screen 4: Validation)
1. **Navigate to:** `http://localhost:5173/validate/demo`
2. **Observe:**
   - AI is **locked again** while the student proves understanding.
   - Live Web Speech API captions for voice explanation.
   - Rubric grading with mandatory quoted evidence spans.
   - **Teach-Back ("Confused Junior"):** Simulated junior peer asks counter-intuitive questions (*"Why can't we just sort the array first?"*).
   - **Understanding-Consistency Meter:** Click **(Contest / Details)** to inspect vocabulary overlap and submit 1-click contestation notes per ThinkFree's Fairness Charter.

---

## 5. Institutional & Cryptographic Credentials
1. **Professor Portal:**
   - Visit `http://localhost:5173/professor`
   - Review class reliance distributions, exam-readiness brackets, and assignment creation with AI policy toggles.
2. **Tamper-Evident Badge Verification:**
   - Visit `http://localhost:5173/verify/badge_demo_77`
   - Observe real-time Ed25519 digital signature verification certifying unassisted performance.
3. **Linear Collaboration & DPDP Privacy Centre:**
   - Visit `http://localhost:5173/collab`
   - Inspect team tasks with AI policies, voluntary external AI self-reporting, and 1-click DPDP personal telemetry export.
