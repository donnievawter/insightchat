# Implementation Plan: Jupyter Notebook Support

**Branch**: `001-jupyter-notebook-support` | **Date**: 2026-01-26 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-jupyter-notebook-support/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Add Jupyter notebook (.ipynb) viewing and loading capabilities to the RAG chat interface. Users can view notebooks with formatted markdown cells and syntax-highlighted code cells, download original files, and load all notebook content into chat context for Q&A. Implementation extends existing document viewer infrastructure in chat.html with new .ipynb handler following patterns from PDF/CSV/DOCX viewers.

## Technical Context

**Language/Version**: Python 3.11+ (Flask backend), JavaScript ES6+ (frontend)
**Primary Dependencies**: Flask 3.0+, existing markdown renderer in chat.html, syntax highlighting library (Prism.js or Highlight.js via CDN)
**Storage**: RAG system backend already handles .ipynb indexing and chunking; frontend retrieves via existing `/get_document` and `/load_source` endpoints
**Testing**: Manual browser testing for P1-P2; pytest for backend routes if new endpoints added
**Target Platform**: Web browser (Chrome 90+, Firefox 88+, Safari 14+)
**Project Type**: Web application (Flask backend + vanilla JS frontend)
**Performance Goals**: <2s to display notebook viewer, <5s for notebooks up to 10MB
**Constraints**: <200ms p95 for document fetches (already met by existing endpoints); inline images truncated >1MB per cell output
**Scale/Scope**: Single feature (~300 LOC frontend JS, minimal backend changes), extends existing viewer with 1 new file type handler

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### I. Clean Code ✅ PASS
- **Functions <50 lines**: Notebook rendering functions will follow pattern from existing `displayPdfDocument()`, `displayCsvDocument()` (~40-60 LOC each)
- **Type hints**: JavaScript frontend (no static typing); Python backend routes already use Flask type patterns
- **Meaningful names**: Will use `displayNotebookDocument()`, `parseNotebookCell()`, `renderCodeCell()` following existing conventions
- **Single purpose**: Each function handles one cell type or one rendering concern

### II. Simple UX ✅ PASS
- **Intuitive interface**: Extends existing "View" button pattern; notebooks open in same modal as PDFs/CSVs
- **Clear feedback**: Loading spinner during fetch, error messages for corrupt notebooks, fallback for missing outputs
- **Sensible defaults**: Notebooks display immediately; execution count badges shown when present; code syntax highlighted
- **Progress indicators**: "Loading notebook..." message while fetching, consistent with PDF/DOCX viewers

### III. Responsive Design ✅ PASS  
- **Fast feedback**: Target <2s to display viewer (same as PDF viewer), async fetch prevents UI blocking
- **Performance**: Pagination for notebooks >100 cells (if needed); truncation for outputs >1MB prevents browser crashes
- **No blocking**: Uses existing async `fetch()` API; rendering happens incrementally as JSON parses
- **Benchmarks**: Will test with 10MB notebook, 50-cell notebook, notebook with large matplotlib outputs

### IV. Minimal Dependencies ⚠️ REQUIRES JUSTIFICATION
- **New dependency**: Prism.js or Highlight.js (CDN-loaded, ~20KB) for syntax highlighting
  - **Justification**: Native `<pre><code>` tags lack language-aware highlighting; implementing custom highlighter would be 500+ LOC and reinvent wheel
  - **Alternative considered**: No highlighting (poor UX for code readability)
  - **Mitigation**: Load from CDN (no npm dependency), lazy-load only when .ipynb viewed
- **Dependency count**: Still <15 (no change to pyproject.toml; JavaScript CDN only)

**GATE RESULT**: ✅ PASS (with justified CDN dependency)

## Project Structure

### Documentation (this feature)

```text
specs/001-jupyter-notebook-support/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0: Syntax highlighter evaluation, nbformat structure research
├── data-model.md        # Phase 1: Jupyter notebook JSON schema, cell types, output formats
├── quickstart.md        # Phase 1: How to test notebook viewing in dev environment
├── contracts/           # Phase 1: Example .ipynb fixtures for testing
│   ├── simple-notebook.ipynb      # Basic markdown + code cells
│   ├── output-notebook.ipynb      # Cells with text/image outputs
│   └── large-notebook.ipynb       # Performance test (10MB, 100+ cells)
└── tasks.md             # Phase 2: Task breakdown (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
flask-chat-app/
├── src/
│   ├── app.py                     # No changes (entry point)
│   └── chat/
│       ├── routes.py              # MODIFY: Add notebook badge to /browse_documents response
│       └── __init__.py            # No changes
├── templates/
│   └── chat.html                  # MODIFY: Add notebook viewer, syntax highlighting
└── static/
    ├── css/
    │   └── style.css              # MODIFY: Add notebook-specific styles (.notebook-cell, .execution-count)
    └── js/
        └── (none - inline JS)     # All JavaScript currently inline in chat.html

tests/
├── contract/                      # NEW: Contract tests for notebook viewer
│   └── test_notebook_viewer.py   # Validate FR-001 through FR-013
├── integration/                   # Optional: Backend integration tests
│   └── test_routes.py            # Test /browse_documents returns .ipynb with badge
└── unit/                          # Optional: JS unit tests (future)
```

**Structure Decision**: This is a web application following the existing Flask + vanilla JS architecture. All frontend logic resides in [flask-chat-app/templates/chat.html](../flask-chat-app/templates/chat.html) as inline JavaScript. Backend changes minimal (1-2 lines in routes.py to add notebook badge). No new directories required; extends existing viewer infrastructure.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Prism.js CDN dependency (~20KB) | Code syntax highlighting for Python/R/Julia cells in notebooks | Implementing custom tokenizer/highlighter would require 500+ LOC regex parsing, 20+ language grammars, and ongoing maintenance. Native `<pre><code>` tags provide no visual distinction between keywords, strings, comments. Poor readability for technical notebook content where syntax clarity is essential. |

**Mitigation Strategy**: Lazy-load Prism.js only when user clicks "View" on .ipynb file (not on page load). Use CDN with SRI hash for security. Fallback to unstyled `<code>` blocks if CDN fails.

---

## Phase 0: Outline & Research ✅ COMPLETE

**Objective**: Resolve all "NEEDS CLARIFICATION" items and establish technical approach.

### Completed Research Tasks

1. **Jupyter Notebook File Format** ([research.md#1](research.md#1-jupyter-notebook-file-format-ipynb))
   - Decision: Native JSON parsing with nbformat v4 validation
   - No server-side library needed; frontend-only implementation

2. **Syntax Highlighting Library** ([research.md#2](research.md#2-syntax-highlighting-library-selection))
   - Decision: Prism.js v1.29+ (27KB) loaded from CDN
   - Alternatives evaluated: Highlight.js, CodeMirror, Monaco, custom regex
   - Selected for: Size (smallest), async loading, 200+ language support

3. **Cell Output Rendering** ([research.md#3](research.md#3-cell-output-rendering-strategies))
   - MIME type priority: image/png > text/html > text/plain
   - Truncation: >1MB outputs → show first 100KB + "Show More" button
   - Base64 image decoding handled natively by browser

4. **Document Viewer Pattern** ([research.md#4](research.md#4-existing-document-viewer-pattern-analysis))
   - Analyzed existing PDF/CSV/DOCX handlers
   - Consistent 3-step pattern: detect extension → fetch → render
   - Will extend `fetchDocumentContent()` with .ipynb case

5. **Performance Strategy** ([research.md#5](research.md#5-performance-considerations-for-large-notebooks))
   - Target: <2s view time, handle 10MB notebooks
   - Output truncation prevents DOM bloat
   - Lazy cell rendering deferred to Phase 2 if needed

**Artifacts**:
- ✅ [research.md](research.md) - 5 research tasks documented with decisions
- ✅ All NEEDS CLARIFICATION items resolved
- ✅ No blocking unknowns remaining

---

## Phase 1: Design & Contracts ✅ COMPLETE

**Objective**: Generate data models, API contracts, and test fixtures.

### Completed Design Tasks

1. **Data Model Definition** ([data-model.md](data-model.md))
   - Entity: Jupyter Notebook (cells, metadata, nbformat)
   - Entity: Cell (cell_type, source, execution_count, outputs)
   - Entity: CellOutput (output_type, data, MIME types)
   - Validation rules: nbformat === 4, size limits, MIME validation

2. **API Contracts (Test Fixtures)** ([contracts/](contracts/))
   - ✅ `simple-notebook.ipynb` - Basic markdown + code cells, execution counts
   - ✅ `output-notebook.ipynb` - Images, errors, HTML outputs, truncation test
   - Future: `large-notebook.ipynb` - 10MB performance test (deferred to implementation)

3. **Testing Guide** ([quickstart.md](quickstart.md))
   - 9-step testing workflow: upload → view → download → load → edge cases
   - Performance benchmarking instructions (DevTools timing)
   - Rollback procedures if critical issues found
   - Success checklist covering FR-001 through FR-013, SC-001 through SC-006

4. **Agent Context Update** ✅
   - Updated `.github/agents/copilot-instructions.md` with:
     - Technology: Python 3.11+, JavaScript ES6+, Flask 3.0+
     - Dependencies: Prism.js (CDN), existing markdown renderer
     - Database: RAG backend handles .ipynb indexing

**Artifacts**:
- ✅ [data-model.md](data-model.md) - 3 entities with attributes, validation, data flow
- ✅ [contracts/simple-notebook.ipynb](contracts/simple-notebook.ipynb) - 6 cells, tests FR-001 to FR-013
- ✅ [contracts/output-notebook.ipynb](contracts/output-notebook.ipynb) - 5 cells, tests FR-005, FR-012
- ✅ [quickstart.md](quickstart.md) - 9-step testing guide, rollback instructions
- ✅ [.github/agents/copilot-instructions.md](.github/agents/copilot-instructions.md) - Updated context

### Constitution Re-Check (Post-Design)

**I. Clean Code** ✅ PASS - Data model entities have clear single responsibility
**II. Simple UX** ✅ PASS - Testing guide confirms intuitive flow, clear error states
**III. Responsive Design** ✅ PASS - Performance targets specified (<2s, <5s for 10MB)
**IV. Minimal Dependencies** ✅ PASS - Prism.js justified, no new Python dependencies

**GATE RESULT**: ✅ PASS - No constitution violations introduced in design

---

## Next Steps: Phase 2 (Implementation) ✅ READY

**Tasks Generated**: [tasks.md](tasks.md) - 41 tasks organized by user story

**Quick Summary**:
- **Phase 1: Setup** (3 tasks) - Prism.js CDN, file upload
- **Phase 2: Foundational** (4 tasks) - Extension routing, viewer stub
- **Phase 3: US1 - View** (18 tasks) - Full notebook rendering (MVP 🎯)
- **Phase 4: US2 - Download** (4 tasks) - Download original .ipynb
- **Phase 5: US3 - Load Context** (4 tasks) - Load for Q&A
- **Phase 6: Polish** (8 tasks) - Edge cases, performance, docs

**Timeline**: 9-12 hours for single developer, all 3 user stories

**MVP Path** (US1 only): Setup (30m) → Foundational (1h) → View (4-6h) = ~6-8 hours

**Start Implementation**: Begin with Phase 1 tasks (T001-T003) in [tasks.md](tasks.md)

---

## Plan Status Summary

| Phase | Status | Artifacts | Notes |
|-------|--------|-----------|-------|
| **Phase 0: Research** | ✅ Complete | research.md (5 decisions) | All unknowns resolved |
| **Phase 1: Design** | ✅ Complete | data-model.md, contracts/, quickstart.md | Constitution re-check passed |
| **Phase 2: Tasks** | ✅ Complete | tasks.md (41 tasks, 6 phases) | All tasks implemented |
| **Implementation** | ✅ Complete | See IMPLEMENTATION_COMPLETE.md | All 41 tasks done, ready for testing |

**Status**: ✅ IMPLEMENTATION COMPLETE - All 6 phases finished. See [IMPLEMENTATION_COMPLETE.md](IMPLEMENTATION_COMPLETE.md) for details. Ready for manual testing via [quickstart.md](quickstart.md).
