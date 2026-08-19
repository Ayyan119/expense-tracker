# Spendly — Specifications Directory

This directory contains specifications and technical design documents for Spendly using Specification-Driven Development.

## Directory Structure

```
specs/
├── README.md                 # Overview & workflow instructions (this file)
├── templates/                # Reusable spec templates
│   └── feature_spec_template.md
├── features/                 # Specifications for application features & user flows
└── architecture/             # System design, database schemas, and API standards
```

## Workflow Guide

1. **Drafting a Spec:**
   Create a new specification document in `specs/features/` or `specs/architecture/` using `specs/templates/feature_spec_template.md`.
2. **Review & Alignment:**
   Align on user requirements, technical requirements, acceptance criteria, and edge cases before writing implementation code.
3. **Test-Driven Execution:**
   Write unit tests in `test_app.py` based on the acceptance criteria in the spec.
4. **Verification:**
   Ensure all automated tests pass (`.venv/bin/pytest`) before merging or completing the specification.
