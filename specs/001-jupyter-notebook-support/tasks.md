# Tasks: Jupyter Notebook Support

**Input**: Design documents from `/specs/001-jupyter-notebook-support/`
**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md), [data-model.md](data-model.md), [contracts/](contracts/)

**Tests**: Manual browser testing (no automated test tasks - testing via [quickstart.md](quickstart.md))

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `- [ ] [ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `flask-chat-app/templates/` (frontend), `flask-chat-app/src/chat/` (backend), `flask-chat-app/static/css/` (styles)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Prepare development environment and load syntax highlighting library

- [X] T001 Verify Prism.js CDN availability and select version (27KB core + Python/R/Julia languages from jsDelivr)
- [X] T002 [P] Create syntax highlighting loader utility function (lazy load on first .ipynb view)
- [X] T003 [P] Add .ipynb to file upload accept list in flask-chat-app/templates/chat.html line ~1705 (openFileUpload function)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core notebook detection and routing infrastructure - MUST be complete before any user story

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Add notebook extension detection to fetchDocumentContent() in flask-chat-app/templates/chat.html (~line 508): `const notebookExtensions = ['ipynb'];`
- [X] T005 Add notebook routing case to fetchDocumentContent() if/else chain: `else if (notebookExtensions.includes(fileExtension)) { displayNotebookDocument(source, contentElement); }`
- [X] T006 Create displayNotebookDocument() stub function in flask-chat-app/templates/chat.html (returns loading state HTML)
- [X] T007 Add .notebook-document-container CSS styles to flask-chat-app/static/css/style.css (follow .csv-document-container pattern)

**Checkpoint**: Foundation ready - extension routing works, viewer stub renders

---

## Phase 3: User Story 1 - View Notebook Content in Browser (Priority: P1) 🎯 MVP

**Goal**: Users can view Jupyter notebooks with formatted markdown cells and syntax-highlighted code cells

**Independent Test**: Upload [contracts/simple-notebook.ipynb](contracts/simple-notebook.ipynb), click "View", verify rendering per [quickstart.md Step 2](quickstart.md#step-2-view-notebooks-in-chat-interface)

### Implementation for User Story 1

- [X] T008 [P] [US1] Implement notebook JSON parsing in displayNotebookDocument() - fetch, parse, validate nbformat === 4
- [X] T009 [P] [US1] Create renderNotebookCell(cell, index) helper function - routes by cell_type to specific renderers
- [X] T010 [US1] Implement renderMarkdownCell(cell) in flask-chat-app/templates/chat.html - reuse existing markdownToHtml() function
- [X] T011 [US1] Implement renderCodeCell(cell) - syntax highlighting with Prism.js, execution count badge "In [N]:"
- [X] T012 [US1] Implement renderRawCell(cell) - display as plain text in <pre> block
- [X] T013 [US1] Create renderCellOutput(output) helper - handles MIME type priority (image > HTML > text)
- [X] T014 [US1] Add image output rendering - base64 PNG/JPEG as `<img src="data:image/png;base64,...">` with lazy loading
- [X] T015 [US1] Add text output rendering - escape HTML, wrap in <pre class="notebook-output-text">
- [X] T016 [US1] Add error output rendering - red styling, display ename/evalue/traceback with ANSI escape stripping
- [X] T017 [US1] Add HTML output rendering - inject as innerHTML in <div class="notebook-output-html"> (future: sanitize for XSS)
- [X] T018 [US1] Build complete notebook HTML structure - header (filename + actions) + cells loop + viewer container
- [X] T019 [US1] Implement output truncation logic - check size >1MB, show first 100KB + "Show More" button (FR-012)
- [X] T020 [US1] Add execution count badge styling in flask-chat-app/static/css/style.css - `.execution-count` class (gray badge, monospace font)
- [X] T021 [US1] Add notebook cell styling - `.notebook-cell`, `.notebook-cell-markdown`, `.notebook-cell-code` classes with borders, padding
- [X] T022 [US1] Handle unexecuted cells (execution_count: null) - display "In [ ]:" badge, skip output rendering (FR-011)
- [X] T023 [US1] Handle notebooks with missing cells gracefully - show "This notebook contains no cells" message (FR-008)
- [X] T024 [US1] Handle invalid nbformat version - show error "Unsupported notebook version (nbformat X)" (validation rule)
- [X] T025 [US1] Add loading state animation and error state styling to notebook viewer CSS

**Checkpoint**: View notebook completely functional - all cell types render, outputs display, execution counts shown

**Manual Test**: Follow [quickstart.md Steps 2-3](quickstart.md#step-2-view-notebooks-in-chat-interface) with contract notebooks

---

## Phase 4: User Story 2 - Download Notebooks (Priority: P2)

**Goal**: Users can download Jupyter notebook files to their local machine in original .ipynb format

**Independent Test**: View notebook, click "Download", verify .ipynb file downloads and opens in local Jupyter Lab ([quickstart.md Step 4](quickstart.md#step-4-download-notebook))

### Implementation for User Story 2

- [X] T026 [US2] Add "Download" button to notebook viewer header in displayNotebookDocument() HTML template
- [X] T027 [US2] Implement downloadNotebook(source) utility function in flask-chat-app/templates/chat.html - create download link, trigger click
- [X] T028 [US2] Style download button in flask-chat-app/static/css/style.css - follow `.csv-btn` pattern with download icon
- [X] T029 [US2] Test download with [contracts/simple-notebook.ipynb](contracts/simple-notebook.ipynb) - verify 100% fidelity when reopened

**Checkpoint**: Download functional - notebooks download and reopen in Jupyter Lab without loss

**Manual Test**: Follow [quickstart.md Step 4](quickstart.md#step-4-download-notebook)

---

## Phase 5: User Story 3 - Load Notebook Context for Chat (Priority: P2)

**Goal**: Users can load entire notebook content into chat context for Q&A about code, analysis, or results

**Independent Test**: Click "Load (All Chunks)", ask "What does this notebook do?", verify assistant references notebook content ([quickstart.md Step 5](quickstart.md#step-5-load-notebook-into-chat-context))

### Implementation for User Story 3

- [X] T030 [US3] Add notebook badge to /browse_documents response in flask-chat-app/src/chat/routes.py - detect .ipynb extension, set badge "IPYNB"
- [X] T031 [US3] Update displayDocuments() in flask-chat-app/templates/chat.html to show "IPYNB" badge (following CSV badge pattern)
- [X] T032 [US3] Verify "Load (All Chunks)" button works for notebooks - existing loadDocumentFromBrowser() should handle .ipynb via /load_source endpoint
- [X] T033 [US3] Test context loading with [contracts/simple-notebook.ipynb](contracts/simple-notebook.ipynb) - ask questions, verify 90%+ accuracy (SC-004)

**Checkpoint**: Load context functional - RAG retrieves all chunks, assistant answers notebook questions

**Manual Test**: Follow [quickstart.md Step 5](quickstart.md#step-5-load-notebook-into-chat-context)

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Edge cases, performance, and documentation

- [X] T034 [P] Test large output truncation with >1MB cell output - create test notebook, verify "Show More" button works ([quickstart.md Step 6](quickstart.md#step-6-test-large-output-truncation))
- [X] T035 [P] Test invalid notebook handling - nbformat 3 notebook, corrupted JSON, empty cells ([quickstart.md Step 7-8](quickstart.md#step-7-test-invalid-notebook))
- [X] T036 Performance test with 10MB notebook - verify <5s load time per SC-005 ([quickstart.md Step 9](quickstart.md#step-9-load-time-benchmark))
- [X] T037 [P] Add "Open in New Tab" button to notebook viewer (optional enhancement, follow markdown viewer pattern)
- [X] T038 Browser compatibility test - Chrome 90+, Firefox 88+, Safari 14+ per plan.md
- [X] T039 Update README.md with Jupyter notebook support announcement and screenshot
- [X] T040 [P] Run complete quickstart.md validation - all 9 steps pass
- [X] T041 Code review and cleanup - remove console.log statements, ensure <50 LOC per function (constitution)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-5)**: All depend on Foundational phase completion
  - User stories can proceed in priority order: US1 (P1) → US2/US3 (P2)
- **Polish (Phase 6)**: Depends on US1-US3 being complete

### User Story Dependencies

- **User Story 1 (P1 - View)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2 - Download)**: Can start after US1 complete (needs viewer infrastructure) - Independently testable
- **User Story 3 (P2 - Load Context)**: Can start after Foundational (Phase 2) - Independent of US1/US2, but typically done after US1 for UX flow

### Within Each User Story

**US1 (View)**:
1. Parse notebook JSON (T008)
2. Cell rendering helpers in parallel: renderNotebookCell (T009), renderMarkdownCell (T010), renderCodeCell (T011), renderRawCell (T012)
3. Output rendering in parallel: renderCellOutput (T013), image (T014), text (T015), error (T016), HTML (T017)
4. Build HTML structure (T018)
5. Truncation + styling in parallel: truncation logic (T019), CSS styles (T020-T021)
6. Edge cases in parallel: unexecuted cells (T022), missing cells (T023), invalid version (T024), loading/error states (T025)

**US2 (Download)**:
1. Add button (T026) → implement function (T027) → style (T028) → test (T029)

**US3 (Load Context)**:
1. Backend badge (T030) + frontend badge (T031) can run in parallel
2. Verify existing functionality (T032) → test (T033)

### Parallel Opportunities

- **Setup phase**: T002 (loader utility) and T003 (file upload) can run in parallel
- **Foundational phase**: T004-T007 can run sequentially (same file edits in chat.html)
- **US1**: T009-T012 (cell renderers), T014-T017 (output renderers), T020-T021 (CSS), T022-T025 (edge cases) - all parallelizable
- **US3**: T030 (backend) and T031 (frontend) can run in parallel
- **Polish**: T034, T035, T037, T039, T040 can all run in parallel

---

## Parallel Example: User Story 1

```bash
# Launch all cell renderers together:
Task T009: "Create renderNotebookCell(cell, index) helper"
Task T010: "Implement renderMarkdownCell(cell)"
Task T011: "Implement renderCodeCell(cell)"
Task T012: "Implement renderRawCell(cell)"

# Launch all output renderers together:
Task T014: "Add image output rendering"
Task T015: "Add text output rendering"
Task T016: "Add error output rendering"
Task T017: "Add HTML output rendering"

# Launch styling tasks together:
Task T020: "Add execution count badge styling"
Task T021: "Add notebook cell styling"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T003) - ~30 min
2. Complete Phase 2: Foundational (T004-T007) - ~1 hour (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (T008-T025) - ~4-6 hours
4. **STOP and VALIDATE**: Test with [contracts/simple-notebook.ipynb](contracts/simple-notebook.ipynb) and [contracts/output-notebook.ipynb](contracts/output-notebook.ipynb)
5. If validation passes, MVP is ready for demo/deployment

**MVP Delivers**: View notebooks with markdown, code, outputs, syntax highlighting, execution counts

### Incremental Delivery

1. **Foundation** (Setup + Foundational) → Extension routing works
2. **Add US1 (View)** → Test independently → Deploy/Demo (MVP! 🎯)
3. **Add US2 (Download)** → Test independently → Deploy/Demo
4. **Add US3 (Load Context)** → Test independently → Deploy/Demo
5. **Polish** (Phase 6) → Performance test → Final deployment

Each increment adds value without breaking previous functionality.

### Single Developer Timeline

- **Phase 1-2 (Foundation)**: 1.5 hours
- **Phase 3 (US1 - View)**: 4-6 hours
- **Phase 4 (US2 - Download)**: 30 minutes
- **Phase 5 (US3 - Load Context)**: 1 hour
- **Phase 6 (Polish)**: 2-3 hours

**Total**: 9-12 hours for complete implementation

---

## Notes

- [P] tasks = different files or independent functions, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify rendering after each batch of parallel tasks
- Commit after each logical group (e.g., all cell renderers, all output renderers)
- Stop at any checkpoint to validate story independently via [quickstart.md](quickstart.md)
- **Constitution compliance**: All functions <50 LOC, meaningful names (renderCodeCell, displayNotebookDocument), Prism.js dependency justified

---

## Success Criteria Mapping

| Task(s) | Functional Requirement | Success Criterion |
|---------|------------------------|-------------------|
| T004-T005 | FR-001 (detect .ipynb) | - |
| T008 | FR-002 (parse JSON) | - |
| T010 | FR-003 (render markdown) | SC-002 (95% formatting accuracy) |
| T011 | FR-004 (syntax highlighting) | SC-002 |
| T013-T017 | FR-005 (display outputs) | SC-006 (5MB images render) |
| T026-T029 | FR-006 (download) | SC-003 (100% fidelity) |
| T030-T033 | FR-007 (load context) | SC-004 (90% Q&A accuracy) |
| T022-T024 | FR-008 (handle missing/empty cells) | - |
| T030 | FR-009 (visual indicator) | - |
| T011 | FR-010 (execution order) | - |
| T022 | FR-011 (unexecuted notebooks) | - |
| T019, T034 | FR-012 (truncate >1MB outputs) | - |
| T011 | FR-013 (execution count badges) | - |
| T008, T025 | SC-001 (<2s view time) | - |
| T036 | SC-005 (10MB notebooks <5s) | - |

**All requirements and success criteria covered** ✅
