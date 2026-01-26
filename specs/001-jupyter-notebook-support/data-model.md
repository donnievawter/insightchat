# Data Model: Jupyter Notebook Support

**Feature**: 001-jupyter-notebook-support | **Phase**: 1 (Design & Contracts) | **Date**: 2026-01-26

## Entity: Jupyter Notebook

**Description**: A JSON file (.ipynb) containing executable code cells, markdown documentation, and cell outputs. Follows nbformat v4+ specification.

**Source**: User uploads to RAG system OR already indexed in RAG backend

### Attributes

| Attribute | Type | Required | Description | Validation |
|-----------|------|----------|-------------|------------|
| `cells` | Array\<Cell\> | ✅ | Ordered list of notebook cells | Min 0 cells, max 10,000 |
| `metadata` | Object | ✅ | Notebook-level metadata (kernel info, language) | Must contain `kernelspec` or empty object |
| `nbformat` | Integer | ✅ | Major version of nbformat spec | Must be 4 (v4.x supported) |
| `nbformat_minor` | Integer | ✅ | Minor version of nbformat spec | Typically 4 or 5 |

### State Transitions

*N/A - Notebooks are read-only in the viewer*

### Relationships

- **Contains** → Cell (1:many): One notebook has 0+ cells
- **Retrieved from** → RAG System (1:1): Notebook fetched via `/get_document` endpoint
- **Loaded into** → Chat Context (1:1): "Load (All Chunks)" retrieves combined chunks

---

## Entity: Cell

**Description**: A single unit of content within a notebook. Can be markdown (documentation), code (executable), or raw (unprocessed text).

**Source**: Parsed from notebook's `cells` array

### Attributes

| Attribute | Type | Required | Description | Validation |
|-----------|------|----------|-------------|------------|
| `cell_type` | String | ✅ | Type of cell: `"code"`, `"markdown"`, or `"raw"` | Enum: ["code", "markdown", "raw"] |
| `source` | Array\<String\> | ✅ | Cell content as array of lines | Each string is one line; join with `\n` |
| `execution_count` | Integer \| null | ⚠️ | Execution order for code cells; null if unexecuted | Required for `cell_type="code"` |
| `outputs` | Array\<CellOutput\> | ⚠️ | Results of code execution | Only present for `cell_type="code"` |
| `metadata` | Object | ❌ | Cell-level metadata (tags, collapsed state) | Optional; ignored in P1 implementation |

### State Transitions

*N/A - Cells are read-only in the viewer*

### Relationships

- **Belongs to** → Notebook (many:1): Cell is part of one notebook
- **Produces** → CellOutput (1:many): Code cells have 0+ outputs

---

## Entity: CellOutput

**Description**: The result of executing a code cell. Can be text, images, HTML, errors, or other MIME-typed data.

**Source**: Parsed from code cell's `outputs` array

### Attributes

| Attribute | Type | Required | Description | Validation |
|-----------|------|----------|-------------|------------|
| `output_type` | String | ✅ | Type of output: `"stream"`, `"display_data"`, `"execute_result"`, `"error"` | Enum: ["stream", "display_data", "execute_result", "error"] |
| `data` | Object | ⚠️ | MIME-typed output data (for display_data/execute_result) | Keys: MIME types (e.g., "text/plain", "image/png") |
| `text` | Array\<String\> | ⚠️ | Text output (for stream type) | Present when `output_type="stream"` |
| `name` | String | ⚠️ | Stream name: `"stdout"` or `"stderr"` | Required when `output_type="stream"` |
| `execution_count` | Integer \| null | ⚠️ | Matches cell execution_count (for execute_result) | Only for `output_type="execute_result"` |
| `ename` | String | ⚠️ | Error name (for error type) | Required when `output_type="error"` |
| `evalue` | String | ⚠️ | Error value/message | Required when `output_type="error"` |
| `traceback` | Array\<String\> | ⚠️ | Stack trace lines | Required when `output_type="error"` |

### MIME Type Handling

**Priority Order** (when rendering `data` field):

1. **image/png**, **image/jpeg** → Render as `<img>` with base64 data URI
2. **text/html** → Inject as HTML (future: sanitize for XSS)
3. **application/json** → Syntax-highlighted JSON
4. **text/plain** → Escaped text in `<pre>` block (fallback)

**Truncation Rule** (from spec FR-012):
- If `data["text/plain"].join('').length > 1,048,576` (1MB) → truncate
- Display first 102,400 bytes (100KB) with "Show More" button

### State Transitions

*N/A - Outputs are read-only in the viewer*

### Relationships

- **Belongs to** → Cell (many:1): Output is part of one code cell

---

## Validation Rules

### Notebook Level
1. **Required fields**: Must have `cells`, `metadata`, `nbformat`, `nbformat_minor`
2. **Version check**: `nbformat` must equal 4 (reject v3 notebooks with error message)
3. **Size limit**: Total JSON size <10MB (spec SC-005 constraint)

### Cell Level
1. **Type validation**: `cell_type` must be "code", "markdown", or "raw"
2. **Source format**: `source` must be array of strings (join with newline for display)
3. **Code cell requirements**: If `cell_type="code"`, must have `execution_count` (can be null) and `outputs` array

### Output Level
1. **MIME type validation**: All keys in `data` must be valid MIME types (contain `/`)
2. **Base64 validation**: Image data must be valid base64 (no decoding attempted; browser handles)
3. **Size limits**: Individual output size <1MB (FR-012); notebook-level size <10MB (SC-005)

---

## Example Data Structures

### Minimal Valid Notebook
```json
{
  "cells": [
    {
      "cell_type": "markdown",
      "source": ["# Hello Notebook"],
      "metadata": {}
    },
    {
      "cell_type": "code",
      "execution_count": 1,
      "source": ["print('Hello, World!')"],
      "outputs": [
        {
          "output_type": "stream",
          "name": "stdout",
          "text": ["Hello, World!\n"]
        }
      ],
      "metadata": {}
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

### Cell with Image Output
```json
{
  "cell_type": "code",
  "execution_count": 5,
  "source": ["import matplotlib.pyplot as plt\n", "plt.plot([1,2,3])\n", "plt.show()"],
  "outputs": [
    {
      "output_type": "display_data",
      "data": {
        "image/png": "iVBORw0KGgoAAAANSUhEUgAAAX...(base64 encoded)...",
        "text/plain": ["<Figure size 640x480 with 1 Axes>"]
      },
      "metadata": {}
    }
  ]
}
```

### Cell with Error Output
```json
{
  "cell_type": "code",
  "execution_count": 3,
  "source": ["1 / 0"],
  "outputs": [
    {
      "output_type": "error",
      "ename": "ZeroDivisionError",
      "evalue": "division by zero",
      "traceback": [
        "\u001b[0;31m---------------------------------------------------------------------------\u001b[0m",
        "\u001b[0;31mZeroDivisionError\u001b[0m: division by zero"
      ]
    }
  ]
}
```

---

## Data Flow

### 1. View Notebook (User clicks "View" button)

```
User Action: Click "View" on notebook in document browser
    ↓
fetchDocumentContent(source, 0, contentElement)
    ↓
Detect .ipynb extension
    ↓
displayNotebookDocument(source, contentElement)
    ↓
Fetch: GET /get_document?source={encoded_path}
    ↓
Response: Raw .ipynb JSON string
    ↓
Parse: JSON.parse(notebookData)
    ↓
Validate: Check nbformat === 4, cells array exists
    ↓
Render: Loop through cells[], create HTML for each
    ↓
Display: Inject HTML into contentElement
```

### 2. Load Notebook Context (User clicks "Load (All Chunks)")

```
User Action: Click "Load (All Chunks)" on notebook
    ↓
loadDocumentFromBrowser(sourcePath, button)
    ↓
POST /load_source { "source_path": "path/to/notebook.ipynb" }
    ↓
Backend: RAG system retrieves all indexed chunks for this notebook
    ↓
Response: { "enhanced_context": "combined_chunks", "source_path": "...", "context_type": "all_chunks" }
    ↓
Store in hidden form field: loaded-context
    ↓
User's next question includes this context
```

### 3. Download Notebook (User clicks "Download")

```
User Action: Click "Download" button in notebook viewer
    ↓
downloadNotebook(source)
    ↓
Create <a> with href="/get_document?source={encoded_path}"
    ↓
Set download attribute to filename.ipynb
    ↓
Programmatic click() triggers browser download
    ↓
User receives original .ipynb file
```

---

## Performance Considerations

### Parsing Performance
- **10MB notebook**: ~100ms to parse JSON on modern browsers
- **100 cells**: ~50ms to render initial HTML structure
- **Large outputs**: Truncated to 100KB prevents DOM bloat

### Memory Usage
- **Parsed notebook object**: ~10MB (in memory copy of JSON)
- **Rendered DOM**: ~2MB (HTML + CSS computed styles)
- **Total**: <15MB per notebook viewer instance (within browser limits)

### Optimization Opportunities (Future)
- Virtual scrolling for notebooks >100 cells
- Lazy image decoding (use `loading="lazy"` on `<img>`)
- Worker thread for JSON parsing (>20MB notebooks)

---

**Phase 1 Data Model Complete** ✅ - Ready for contract generation
