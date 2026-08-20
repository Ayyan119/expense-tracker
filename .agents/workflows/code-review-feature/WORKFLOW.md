# Code Review Feature Workflow

## Description
Executes a comprehensive, parallel dual-dimensional code quality and security review for a feature, file, or target directory using `code-quality-review-agent` and `code-security-review-agent` concurrently. Synthesizes a structured report, asks for user approval if code edits are needed, and updates the code upon confirmation.

## Trigger Command
`/code-review-feature [target-path-or-feature]`

---

## Execution Protocol

### Step 1: Target Scope Identification
- Extract target path, spec name, or file pattern from `$ARGUMENTS`.
- If no argument is provided, inspect modified repository files (`git status` / `git diff`) or default to core application components: `app.py`, `database/db.py`, `templates/`, `static/`.

---

### Step 2: Parallel Dual Audit Execution
Invoke **`code-quality-review-agent`** and **`code-security-review-agent`** **concurrently** in a single `invoke_subagent` call:

1. **`code-quality-review-agent`**: Evaluates:
   - **PEP 8 & Readability**: Naming conventions, formatting, docstrings, code clarity.
   - **Architecture & DRY**: Separation of concerns, function modularity, absence of duplicated logic.
   - **Performance & Resources**: Efficient SQL queries, N+1 loop prevention, proper resource context management.
   - **Testability & Error Handling**: Modular pure functions, fail-closed error boundaries, graceful HTTP handling.
   - **Spendly Guardrails**: Parameterized SQL (`?`), vanilla JS only, design system CSS variables (`var(--...)`).

2. **`code-security-review-agent`**: Evaluates:
   - **SQL Injection & Data Isolation**: 100% parameterized queries (`?`), strict tenancy checks (`WHERE user_id = ?`).
   - **Data Leakage & Secrets**: Audit for hardcoded API keys, JWT secrets, log sanitation, error stack trace masking.
   - **Authentication & IDOR**: Protected route authorization, session safety, resource ownership validation.
   - **XSS & Output Encoding**: Jinja2 autoescaping, DOM safety (`textContent` instead of `innerHTML`).
   - **Dependency & Stdlib Safety**: Audit for dangerous library calls (`eval`, `exec`) and safe subprocess usage.

---

### Step 3: Consolidated Structured Output Generation
Synthesize findings from both concurrent subagent reviews into the standardized Dual-Dimensional Review Report template below.

---

### Step 4: User Approval Gate
- If the review identifies any code quality refactoring or security vulnerability fixes:
  - Present the report and proposed code changes clearly to the user.
  - Ask for explicit user approval before applying any edits to repository files.
- If all checks pass with zero issues, report the clean status and conclude.

---

### Step 5: Code Update & Verification
- Once the user explicitly approves the proposed edits:
  - Apply the refactorings and security remediations to the target files.
  - Execute `.venv/bin/python -m pytest` to confirm 100% test suite pass rate without regressions.

---

## Structured Output Format

```markdown
# Dual-Dimensional Code Review Report — [Target Scope / Feature]

**Review Date**: [Current Date]  
**Audited Scope**: `[File or Feature Path]`  
**Overall Status**: ✅ PASS / ⚠️ ACTION REQUIRED / ❌ CRITICAL BLOCKERS

---

### 1. Executive Summary

| Dimension | Rating | Key Findings Summary |
|---|---|---|
| **Code Quality & Architecture** | High / Medium / Low | Summary of maintainability, PEP 8, and structure |
| **Code Security & Safety** | Secure / Moderate Risk / High Risk | Summary of security risks and OWASP compliance |

---

### 2. Code Quality Review Findings

| Severity | Location (File & Line) | Quality Dimension | Description & Code Smell | Recommended Refactored Code |
|---|---|---|---|---|
| Critical / High / Medium / Low | `app.py:42` | Architecture / PEP 8 / Performance | Explanation of quality issue | Refactored code snippet |

*(If no quality defects are found, explicitly note compliance.)*

---

### 3. Code Security Review Findings

| Severity | Location (File & Line) | Vulnerability Category | Description & Exploit Threat | Secure Code Remediation |
|---|---|---|---|---|
| Critical / High / Medium / Low | `app.py:84` | SQLi / Auth / IDOR / Data Leak / XSS | Explanation of security risk | Secure code replacement snippet |

*(If no security vulnerabilities are found, explicitly note compliance.)*

---

### 4. Consolidated Remediation Checklist

- [ ] Execute Code Quality Refactoring Items
- [ ] Apply Security Vulnerability Fixes
- [ ] Request User Approval Before Applying Changes
- [ ] Run `.venv/bin/python -m pytest` to Confirm 100% Pass Rate
```
