# Changelog

All notable changes to Markdown Outline are documented here.

## 1.0.0 — 2026-10-12

First GitHub-ready release.

### Added
- Right-side Markdown heading outline.
- Click-to-jump heading navigation.
- Global Fold Level 1 through 6.
- Progressive branch-by-branch drill-down.
- Synchronized outline-driven editor folding.
- Refresh, Unfold All, Fold Level 1 and Close toolbar actions.
- Command Palette commands.
- Tools menu entry.
- Fenced-code-block heading exclusion.

### Stabilized
- Normal editing no longer triggers automatic refolding.
- Structural node identity survives line-number shifts better than row-only state.
- MarkdownOutline tracks only its own managed fold regions.
- Adjacent sibling headings use corrected fold boundaries to avoid N/N-1 section mismatch.
- Visible headings retain separate physical lines while folded.
