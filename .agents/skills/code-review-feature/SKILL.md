---
name: code-review-feature
description: Runs a parallel dual-dimensional code quality and security review for a target feature or file path using code-quality-review-agent and code-security-review-agent concurrently. Generates a consolidated report, prompts the user for approval if edits are required, and updates the code upon approval. Pass target path or feature as argument e.g. /code-review-feature app.py
allowed-tools: view_file, grep_search, find_by_name, run_command, invoke_subagent, ask_question, write_to_file, replace_file_content
---

# Code Review Feature (`/code-review-feature`)

Use this skill when performing a parallel dual-dimensional **Code Quality Review** and **Code Security Review** for a specified feature or file scope in Spendly.

---

## Command Usage

```bash
/code-review-feature [file-path-or-feature-name]
```

### Examples:
- `/code-review-feature app.py`
- `/code-review-feature database/db.py`
- `/code-review-feature dashboard`

---

## Execution Protocol

1. **Scope Resolution**: Extract `$ARGUMENTS`. If `$ARGUMENTS` is empty, target modified git files (`git status`) or core application files (`app.py`, `database/db.py`, `templates/`, `static/`).
2. **Parallel Subagent Execution**: Concurrently launch both subagents in a single `invoke_subagent` tool call:
   - **`code-quality-review-agent`**: Audits readability, maintainability, PEP 8 compliance, DRY architecture, and performance.
   - **`code-security-review-agent`**: Audits SQL injection prevention, user isolation (`WHERE user_id = ?`), secret leaks, XSS, and authentication guardrails.
3. **Structured Review Consolidation**: Synthesize findings from both concurrent audits into the standardized report format below.
4. **User Approval Gate**: If any fixes, refactorings, or code edits are required:
   - Present the report and actionable recommendations to the user.
   - Explicitly ask the user for approval before modifying any files.
5. **Code Remediation & Verification**:
   - Upon receiving user approval, apply the agreed code refactoring and security fixes.
   - Run verification using `.venv/bin/python -m pytest` to confirm 100% test pass rate.

---

## Structured Output Format

```markdown
# Dual-Dimensional Code Review Report — [Scope]

**Review Date**: [Current Date]  
**Target Scope**: `[Target File/Feature Path]`  
**Verdict**: ✅ PASS / ⚠️ ACTION REQUIRED / ❌ CRITICAL BLOCKERS

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
| Critical / High / Medium / Low | `file.py:line` | Architecture / PEP 8 / Performance | Explanation of quality issue | Refactored code replacement |

---

### 3. Code Security Review Findings

| Severity | Location (File & Line) | Vulnerability Category | Description & Exploit Threat | Secure Code Remediation |
|---|---|---|---|---|
| Critical / High / Medium / Low | `file.py:line` | SQLi / Auth / IDOR / Data Leak / XSS | Explanation of security risk | Secure code replacement |

---

### 4. Consolidated Action & Remediation Plan

- [ ] Apply Code Quality Refactorings
- [ ] Fix Security Vulnerabilities
- [ ] Get User Approval before editing code
- [ ] Verify test suite with `.venv/bin/python -m pytest`
```
