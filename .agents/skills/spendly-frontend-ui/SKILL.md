---
name: spendly-frontend-ui
description: Generates modern, production-ready UI components and pages for the Spendly expense tracker using vanilla CSS. Use when the user asks to design, create, build, or redesign UI components, pages, or layouts for Spendly (such as login, signup, dashboard, transactions, budgets, or settings).
---
# Spendly Frontend UI

Generates modern, production-ready, clean, and responsive UI components and pages tailored for the Spendly expense tracker application using pure Vanilla CSS.

## When to Use

Use this skill whenever building or refining frontend UI for Spendly, including requests like:

- "Design the [name] page"
- "Create UI for [feature/component]"
- "Build component for [feature]"
- "Redesign / improve [page/component]"
- Building pages such as Login, Signup, Dashboard, Transaction List, Analytics, and Settings for Spendly

## Inputs

- **Page or Component Name**: Target UI element to build or improve.
- **Optional Context**: Existing component code, layout constraints, state requirements, or design references.

## Design Rules and Principles

- **Pure Vanilla CSS**: Use standard, vanilla CSS with CSS custom properties (variables). Avoid CSS frameworks or utility libraries.
- **Fintech Aesthetic**: Minimal, clean, modern SaaS appearance with high clarity and usability.
- **Card-Based Layouts**: Group related data and form elements into clean cards with subtle borders and soft shadows.
- **Consistent Spacing**: Use an 8px spacing grid (8px, 16px, 24px, 32px) for padding, margins, and gaps.
- **Visual Hierarchy and Typography**: Clear heading hierarchy, crisp contrast, readable font sizing, and distinct primary/secondary text.
- **Corners and Shadows**: Rounded corners and subtle elevation for cards and buttons.
- **Color Palette**: Sophisticated neutral backgrounds with intentional accent colors for finances (e.g., emerald green for income/primary, rose for expenses).
- **Icons**: Use clean inline SVG icons or standard SVG icon sets (Lucide / Heroicons style) with clear, semantic meaning.
- **Consistency**: Match existing Spendly project conventions. If design patterns are ambiguous, request reference images or inspect existing component styles.

## Output Structure

When fulfilling a UI request, structure the output in two main sections:

### 1. UI Structure (Brief)

- **Layout and Key Sections**: Outline the structural breakdown of the page or component.
- **UX and Usability Decisions**: Key interaction patterns, accessibility considerations, state handling (e.g., loading, error, empty states), and responsive breakpoints.

### 2. Code Implementation

- **Modular Architecture**: Well-structured semantic HTML and modular components.
- **Clean Vanilla CSS**: Dedicated styles using CSS variables for theme tokens and responsive media queries.
- **Minimal Boilerplate**: Focus on functional, copy-paste-ready UI code with realistic state and form handling.
- **Interactive Details**: Include hover states, focus rings, disabled states, and validation feedback.

## Things to Avoid

- Avoid third-party CSS frameworks (e.g., Tailwind, Bootstrap).
- Avoid generic or outdated UI patterns.
- Avoid unstructured code dumps without context or layout explanation.
- Avoid inconsistent spacing and arbitrary inline styling.