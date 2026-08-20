# Test Feature Workflow

## Description
Executes a two-phase spec-driven testing pipeline for a specific Spendly feature. It uses `pytest-spec-writer` to generate black-box test cases based strictly on feature specifications, followed by `spendly-test-runner` to execute and analyze the tests, producing a consolidated testing report.

## Trigger Command
`/test-feature [spec-name]`

### Examples
- `/test-feature 05-backend-connection`
- `/test-feature 02-registration`
- `/test-feature 03-login-and-logout`

---

## Execution Protocol

### Step 1: Parameter & Spec File Resolution
1. Extract `$ARGUMENTS` passed to the trigger command.
2. **Validation**:
   - If `$ARGUMENTS` is empty, halt immediately with:
     `Please provide a spec name. Usage: /test-feature <spec-name> e.g. /test-feature 05-backend-connection`
   - Locate the specification file at `specs/$ARGUMENTS.md` or `.claude/specs/$ARGUMENTS.md`.
   - If the spec file does not exist, halt immediately with:
     `Spec file not found at specs/$ARGUMENTS.md. Please check the spec name and try again.`

---

### Step 2: Spec-Driven Test Generation (`pytest-spec-writer`)
Invoke the **`pytest-spec-writer`** subagent with the following context and parameters:
- **Spec Source**: `specs/$ARGUMENTS.md` (or `.claude/specs/$ARGUMENTS.md`)
- **Structure Reference**: `app.py` and `database/` directory
- **Target Output File**: `tests/test_$ARGUMENTS.py`
- **Core Instruction**: Generate black-box `pytest` test cases evaluating expected spec behaviors. Tests must cover happy paths, validation errors, auth guards, edge cases, and DB side effects without inspecting implementation details.
- **Handoff Check**: Wait for `pytest-spec-writer` to complete. Verify that `tests/test_$ARGUMENTS.py` was created. If `pytest-spec-writer` fails or fails to write the file, halt the workflow and report the error. Do NOT proceed to Step 3.

---

### Step 3: Test Execution & Analysis (`spendly-test-runner`)
Invoke the **`spendly-test-runner`** subagent with the following context and parameters:
- **Target Test File**: `tests/test_$ARGUMENTS.py`
- **Spec Reference**: `specs/$ARGUMENTS.md`
- **Code Context**: `app.py` and `database/`
- **Execution Command**: `.venv/bin/python -m pytest tests/test_$ARGUMENTS.py -v`
- **Core Instruction**: Execute ONLY the specified test file (`tests/test_$ARGUMENTS.py`). Analyze any failures against spec requirements and implementation code to categorize them as bugs or missing features.

---

## Handoff & Guardrail Rules

1. **Strict Sequence**: Step 3 MUST NOT begin until Step 2 has completed successfully and verified file creation.
2. **Scope Isolation**: Execute ONLY `tests/test_$ARGUMENTS.py`. Do NOT run full test suite sweeps during feature testing unless explicitly requested.
3. **No Modification Rule**: Neither subagent nor the workflow orchestrator may attempt to modify application code (`app.py`, `database/db.py`, HTML templates) during test execution.
4. **Environment Standard**: Always use `.venv/bin/python -m pytest` for test execution.
5. **Database Isolation**: Tests must run against temporary SQLite database files via `tempfile.mkstemp()` fixtures.

---

## Structured Output Format

Upon completion of both steps, generate the final consolidated testing report:

```markdown
# Testing Pipeline Report — [Spec Name / $ARGUMENTS]

**Execution Date**: [Current Date]  
**Spec Target**: `specs/[Spec Name].md`  
**Test File**: `tests/test_[Spec Name].py`  

---

### Step 1 — Tests Written (`pytest-spec-writer`)
- `test_func_1`: Description of spec requirement validated
- `test_func_2`: Description of spec requirement validated
- `test_func_3`: Description of edge case validated

---

### Step 2 — Test Results (`spendly-test-runner`)

| Metric | Count |
|---|---|
| **Total Tests** | X |
| **Passed** | X |
| **Failed** | X |
| **Errors** | X |

#### Failure Details (if applicable)
- **Test**: `test_name`
  - **Error Type**: `AssertionError` / `Exception`
  - **Root Cause**: Explanation of failure
  - **Classification**: Bug / Missing Feature

---

### Verdict
- ✅ **Ready for code review** — All tests pass without failures.
- ❌ **Needs fixes** — Failures detected; review list above before proceeding.
```
