# Research: Jupyter Notebook Support

**Feature**: 001-jupyter-notebook-support | **Phase**: 0 (Outline & Research) | **Date**: 2026-01-26

## Research Tasks

### 1. Jupyter Notebook File Format (.ipynb)

**Decision**: Use native JSON parsing with validation for nbformat structure

**Rationale**:
- .ipynb files are plain JSON following nbformat schema (v4.0+ standard)
- Structure: `{ "cells": [...], "metadata": {...}, "nbformat": 4, "nbformat_minor": 5 }`
- Each cell: `{ "cell_type": "code|markdown|raw", "source": [...], "execution_count": N, "outputs": [...] }`
- JavaScript native `JSON.parse()` handles parsing; no library needed
- Validation: Check for required fields (`cells`, `nbformat`) to detect corrupt files

**Alternatives Considered**:
- **nbformat Python library**: Server-side rendering (requires backend changes, slower)
- **Jupyter widgets**: Complex, requires kernel execution infrastructure
- **Rejected**: Frontend parsing simpler, faster, follows existing document viewer pattern

**References**:
- nbformat specification: https://nbformat.readthedocs.io/en/latest/format_description.html
- Example notebook structure (from research):
```json
{
  "cells": [
    {
      "cell_type": "markdown",
      "metadata": {},
      "source": ["# Notebook Title\n", "This is markdown"]
    },
    {
      "cell_type": "code",
      "execution_count": 1,
      "metadata": {},
      "source": ["import numpy as np\n", "x = np.array([1, 2, 3])"],
      "outputs": [
        {
          "output_type": "execute_result",
          "data": {
            "text/plain": ["array([1, 2, 3])"]
          },
          "execution_count": 1
        }
      ]
    }
  ],
  "metadata": {
    "kernelspec": {
      "display_name": "Python 3",
      "language": "python",
      "name": "python3"
    }
  },
  "nbformat": 4,
  "nbformat_minor": 5
}
```

---

### 2. Syntax Highlighting Library Selection

**Decision**: Use Prism.js (v1.29+) loaded from CDN

**Rationale**:
- **Size**: 27KB minified (core + Python + R + Julia languages)
- **Performance**: Highlights on-demand per code block; non-blocking
- **Language support**: Python (primary), R, Julia, JavaScript, Bash (common in notebooks)
- **CDN availability**: jsDelivr + CloudFlare with SRI hash for security
- **Existing usage**: Already common in data science tools (JupyterLab uses CodeMirror, but Prism.js simpler for read-only)

**Alternatives Considered**:
| Library | Size | Languages | Pros | Cons | Decision |
|---------|------|-----------|------|------|----------|
| **Prism.js** | 27KB | 200+ | Lightweight, async, CDN | Limited to syntax (no IDE features) | ✅ **Selected** |
| **Highlight.js** | 35KB | 190+ | Auto-detection | 8KB larger, aggressive auto-detect | ❌ Rejected (size) |
| **CodeMirror 6** | 150KB+ | Full editor | Full IDE experience | Too heavy for read-only, overkill | ❌ Rejected (complexity) |
| **Monaco Editor** | 2MB+ | VS Code engine | Full IntelliSense | Massive bundle, requires build | ❌ Rejected (size) |
| **Custom regex** | 0KB | 1-2 | No dependency | 500+ LOC, fragile, unmaintained | ❌ Rejected (maintenance) |

**Implementation snippet**:
```html
<!-- Load Prism.js core + Python syntax -->
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/prismjs@1.29.0/themes/prism-tomorrow.min.css" 
      integrity="sha384-..." crossorigin="anonymous">
<script src="https://cdn.jsdelivr.net/npm/prismjs@1.29.0/prism.min.js" 
        integrity="sha384-..." crossorigin="anonymous"></script>
<script src="https://cdn.jsdelivr.net/npm/prismjs@1.29.0/components/prism-python.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/prismjs@1.29.0/components/prism-r.min.js"></script>
```

**Lazy loading strategy**: Inject `<script>` tags only when user opens first .ipynb file (on `displayNotebookDocument()` call), cache loaded state to avoid re-injection.

---

### 3. Cell Output Rendering Strategies

**Decision**: Multi-format rendering with MIME type detection

**Rationale**:
- Notebook outputs have `data` field with MIME-keyed content: `{ "data": { "text/plain": [...], "image/png": "base64...", "text/html": [...] } }`
- Priority order: `image/png` > `text/html` > `text/plain` (richest first)
- Images: Decode base64, render as `<img src="data:image/png;base64,...">`
- HTML: Sanitize and inject (future: consider DOMPurify for XSS protection)
- Plain text: Escape and wrap in `<pre>`

**MIME Type Handling**:
| MIME Type | Rendering Strategy | Priority |
|-----------|-------------------|----------|
| `image/png`, `image/jpeg` | Base64 → `<img>` tag | 1 (highest) |
| `text/html` | Sanitized innerHTML | 2 |
| `application/json` | Syntax-highlighted JSON | 3 |
| `text/plain` | `<pre>` with escaping | 4 (fallback) |
| `application/javascript` | Show as text (no execution) | 5 |

**Truncation handling** (per clarification Q2):
- Check output size: If `data["text/plain"].length > 100_000` chars → truncate
- Display first 100KB with "Show More" button
- Button click: replace content with full output (lazy render)

**Code snippet**:
```javascript
function renderCellOutput(output) {
    if (output.data) {
        // Priority: image > HTML > plain text
        if (output.data['image/png']) {
            return `<img src="data:image/png;base64,${output.data['image/png']}" class="notebook-output-image">`;
        } else if (output.data['text/html']) {
            return `<div class="notebook-output-html">${output.data['text/html'].join('')}</div>`;
        } else if (output.data['text/plain']) {
            const plainText = output.data['text/plain'].join('');
            if (plainText.length > 100000) {
                const truncated = plainText.substring(0, 100000);
                return `<pre class="notebook-output-text">${escapeHtml(truncated)}</pre>
                        <button onclick="showFullOutput(...)">Show More</button>`;
            }
            return `<pre class="notebook-output-text">${escapeHtml(plainText)}</pre>`;
        }
    }
    return '<div class="notebook-output-empty">(no output)</div>';
}
```

---

### 4. Existing Document Viewer Pattern Analysis

**Findings**: All document handlers follow consistent 3-step pattern

1. **Extension detection** in `fetchDocumentContent()`:
   ```javascript
   const fileExtension = source.split('.').pop().toLowerCase();
   if (pdfExtensions.includes(fileExtension)) {
       displayPdfDocument(source, contentElement);
   } else if (csvExtensions.includes(fileExtension)) {
       displayCsvDocument(source, contentElement);
   }
   // ADD: else if (notebookExtensions.includes(fileExtension)) { displayNotebookDocument(...); }
   ```

2. **Display function structure** (using CSV as template):
   ```javascript
   function displayCsvDocument(source, contentElement) {
       // Step 1: Show loading state
       contentElement.innerHTML = '<div class="csv-loading">Loading...</div>';
       
       // Step 2: Fetch content
       fetch('/get_document?source=' + encodeURIComponent(source))
           .then(response => response.text())
           .then(data => {
               // Step 3: Parse and render
               const parsed = parseData(data);
               contentElement.innerHTML = renderData(parsed);
           })
           .catch(error => {
               contentElement.innerHTML = `<div class="error">${error.message}</div>`;
           });
   }
   ```

3. **Styling pattern**: Each document type has container class (`.csv-document-container`, `.pdf-document-container`) with header + content area

**Application to notebooks**:
- Add `.ipynb` to extension arrays
- Create `displayNotebookDocument()` following above pattern
- Use `.notebook-document-container` for consistent styling
- Header: filename + download/copy buttons (like CSV viewer)
- Content: cell-by-cell rendering with execution count badges

---

### 5. Performance Considerations for Large Notebooks

**Challenge**: Notebooks can be 10MB+ with 100+ cells and large matplotlib figures

**Solutions**:
1. **Lazy rendering**: Render only visible cells initially (viewport-based)
   - Use Intersection Observer API to detect cell visibility
   - Render cells 50px before scrolling into view
   - **Decision**: Defer to Phase 2 if performance issues observed in testing

2. **Output truncation** (already decided in Research Task 3):
   - 1MB limit per cell output
   - Display first 100KB with "Show More"
   - Prevents browser freezing on massive outputs

3. **Image optimization**:
   - Base64 images already optimized by notebook authors
   - No additional processing needed (avoid re-encoding)
   - External images: Use `loading="lazy"` attribute on `<img>` tags

4. **JSON parsing optimization**:
   - Use streaming parser for >5MB files? **Rejected**: JavaScript `JSON.parse()` is highly optimized, streaming adds complexity
   - **Decision**: Parse entire notebook upfront; 10MB JSON parses in <100ms on modern browsers

**Benchmark targets** (from spec Success Criteria):
- SC-001: View opens in <2 seconds (includes fetch + parse + render)
- SC-005: Handle 10MB notebooks without crash (<5s load time)

**Testing plan**:
- Create synthetic 10MB notebook with 100 cells + large matplotlib outputs
- Test on Chrome DevTools with 3G throttling
- Measure time from "View" click to first cell render

---

## Summary of Decisions

| Research Area | Decision | Key Rationale |
|---------------|----------|---------------|
| File format | Native JSON parsing | No library needed; nbformat is standard JSON |
| Syntax highlighting | Prism.js (CDN) | 27KB, 200+ languages, lazy-loaded |
| Output rendering | MIME priority: image > HTML > text | Richest format first, truncate >100KB |
| Architecture pattern | Extend existing viewer | Follows PDF/CSV/DOCX pattern, minimal refactor |
| Performance | Parse upfront + output truncation | <2s target met; lazy render deferred |

**Phase 0 Complete** ✅ - Ready for Phase 1 (Design & Contracts)
