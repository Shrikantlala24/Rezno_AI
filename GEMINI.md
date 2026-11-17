# Agent Operating Guidelines & Rules (GEMINI.md)

> **Audience**: Primary AI Agent (Antigravity/Gemini) and any delegated subagents operating in this repository.  
> **Purpose**: Strict execution guardrails, git safety rules, and token-efficiency standards.

---

## 1. Absolute Git Safety Policy (Non-Negotiable)

* **NO Autonomous Commits or Pushes**:
  * NEVER run `git commit` or `git push` on your own.
  * Always present file diffs, verification metrics, and test outputs to the user first.
  * Execute a commit or push **ONLY** when the user explicitly gives written approval (e.g., *"commit this"* or *"push now"*).
* **NO Commits Directly to `main`**:
  * NEVER commit directly to the `main` branch under any circumstances.
  * All experiments, features, bug fixes, and refactoring MUST occur on isolated feature branches (e.g., `feature/core-engine-architecture`).
  * Changes reach `main` strictly through Pull Requests (PRs) reviewed with the user.

---

## 2. Token Efficiency & Planning Policy

* **NO Unsolicited Plan Documents**:
  * DO NOT automatically draft long planning artifacts (`plan.md`, design specs) or waste tokens on speculative planning documents.
  * Proceed directly to targeted code exploration, testing, and implementation.
  * Draft formal implementation/execution plan documents **ONLY when the user explicitly requests one** (e.g., invoking `/plan` or explicitly asking for a written spec).

---

## 3. Scope & Architecture Focus

* **Brain & Spine Ownership**:
  * Focus exclusively on the core computational engine:
    * Query expansion (`plan_query.py`)
    * Retrieval resilience (`search.py`)
    * Vector re-ranking & similarity math (`rank.py`)
    * Grounded claim verification & synthesis (`synthesize.py`)
    * Bipartite concept graph topology (`graph.py`)
    * Intent routing & conversation context (`route.py`)
    * Backend APIs & evaluation suites (`evaluate.py`)
  * Do NOT modify or spend cycles on frontend layout, styling, or CSS components unless explicitly instructed.

---

## 4. Verification Workflow

Before requesting approval or reporting work complete:
1. Verify syntax and dependencies (`uv run python ...` or unit tests).
2. Ensure no unintended file modifications or secret leaks exist.
3. Keep changes clean, modular, and well-commented.
