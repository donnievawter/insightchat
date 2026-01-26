# Quickstart: Testing Jupyter Notebook Support

**Feature**: 001-jupyter-notebook-support | **Phase**: 1 | **Date**: 2026-01-26

## Prerequisites

- Flask development server running (`python flask-chat-app/src/app.py`)
- RAG backend accessible at configured URL (check `.env` for `RAG_API_URL`)
- Modern web browser (Chrome 90+, Firefox 88+, Safari 14+)

---

## Testing Phase 1: Viewing Notebooks

### Step 1: Upload Test Notebooks to RAG System

```bash
# From repository root
cd /opt/dockerapps/insightchat

# Upload simple notebook
curl -X POST http://localhost:5001/upload \
  -F "file=@specs/001-jupyter-notebook-support/contracts/simple-notebook.ipynb"

# Upload output notebook (with images/errors)
curl -X POST http://localhost:5001/upload \
  -F "file=@specs/001-jupyter-notebook-support/contracts/output-notebook.ipynb"

# Verify uploads
curl http://localhost:5001/documents | jq '.[] | select(.path | contains("notebook"))'
```

*Expected output*: JSON list with 2 .ipynb files

### Step 2: View Notebooks in Chat Interface

1. **Open chat interface**: Navigate to `http://localhost:5030/chat`
2. **Open document browser**: Click "Browse Documents" button
3. **Find notebooks**: Search for "notebook" or filter by .IPYNB badge
4. **Click "View"** on `simple-notebook.ipynb`

**Expected Behavior (FR-001 to FR-005)**:
- ✅ Notebook opens in modal viewer within 2 seconds (SC-001)
- ✅ Markdown cells render with HTML formatting (headers, bold, lists)
- ✅ Code cells show syntax highlighting (Python keywords in color)
- ✅ Execution count badges display: `In [1]:`, `In [2]:`, `In [ ]:` (FR-013)
- ✅ Text outputs appear below code cells

### Step 3: Test Output Rendering

1. **Click "View"** on `output-notebook.ipynb`
2. **Scroll through cells**

**Expected Behavior (FR-005)**:
- ✅ Cell 1: Shows 1x1 red PNG image inline
- ✅ Cell 2: Displays error in red with traceback text
- ✅ Cell 3: Renders HTML output (blue bold text)
- ✅ Cell 4: Shows all 20 lines of stdout (no truncation at ~500 bytes)

---

## Testing Phase 2: Download Functionality

### Step 4: Download Notebook

1. **Open** `simple-notebook.ipynb` in viewer
2. **Click "Download" button** (should be in viewer header)
3. **Check downloads folder**

**Expected Behavior (FR-006, SC-003)**:
- ✅ File downloads as `simple-notebook.ipynb`
- ✅ Open in local Jupyter Lab: `jupyter lab simple-notebook.ipynb`
- ✅ All cells, outputs, metadata preserved (100% fidelity)

---

## Testing Phase 3: Loading Context

### Step 5: Load Notebook into Chat Context

1. **Open document browser**
2. **Click "Load (All Chunks)"** on `simple-notebook.ipynb`
3. **Observe notification**: "Loaded context from simple-notebook.ipynb..."
4. **Ask question**: "What does this notebook do?"

**Expected Behavior (FR-007, SC-004)**:
- ✅ Success notification appears
- ✅ Button changes to "✅ Loaded" with green background
- ✅ Modal closes after 1 second
- ✅ Assistant response references notebook content (90% accuracy expected - SC-004)

**Example Valid Responses**:
- "This notebook demonstrates basic Jupyter features with markdown and code cells"
- "The notebook prints 'Hello from Jupyter Notebook!' and calculates squared numbers"
- *Invalid*: Generic response not mentioning notebook specifics

---

## Testing Phase 4: Edge Cases

### Step 6: Test Large Output Truncation

Create a notebook with >1MB output:

```python
# Run in Jupyter, then save as large-notebook.ipynb
for i in range(50000):
    print(f"Line {i}: " + "X" * 100)
```

Upload and view this notebook:

```bash
curl -X POST http://localhost:5001/upload \
  -F "file=@large-notebook.ipynb"
```

**Expected Behavior (FR-012)**:
- ✅ Viewer does NOT crash or freeze
- ✅ Output truncated to first 100KB
- ✅ "Show More" button appears below truncated output
- ✅ Clicking "Show More" loads full output

### Step 7: Test Invalid Notebook

Create corrupted notebook:

```bash
echo '{"cells": [], "nbformat": 3}' > /tmp/bad-notebook.ipynb
curl -X POST http://localhost:5001/upload -F "file=@/tmp/bad-notebook.ipynb"
```

**Expected Behavior (FR-008)**:
- ✅ Viewer shows error message: "Unsupported notebook version (nbformat 3)"
- ✅ No JavaScript console errors or crashes
- ✅ User can close modal and continue using app

### Step 8: Test Missing Cells

```bash
echo '{"cells": [], "metadata": {}, "nbformat": 4, "nbformat_minor": 5}' > /tmp/empty-notebook.ipynb
curl -X POST http://localhost:5001/upload -F "file=@/tmp/empty-notebook.ipynb"
```

**Expected Behavior (FR-008, FR-011)**:
- ✅ Viewer opens successfully
- ✅ Displays message: "This notebook contains no cells"
- ✅ No errors in console

---

## Performance Testing

### Step 9: Load Time Benchmark

Use browser DevTools to measure:

```javascript
// In browser console before clicking "View"
performance.mark('view-start');

// After notebook renders
performance.mark('view-end');
performance.measure('notebook-load', 'view-start', 'view-end');
console.log(performance.getEntriesByName('notebook-load')[0].duration);
```

**Expected Metrics (SC-001, SC-005)**:
- ✅ `simple-notebook.ipynb` (<50KB): <500ms
- ✅ `output-notebook.ipynb` (~200KB): <1000ms  
- ✅ 10MB notebook (if available): <5000ms
- ✅ No browser crash for any size ≤10MB

---

## Rollback Instructions

If testing reveals critical issues:

1. **Disable notebook viewing temporarily**:
   ```javascript
   // In chat.html, comment out .ipynb extension detection
   // const notebookExtensions = ['ipynb'];
   ```

2. **Remove test notebooks from RAG**:
   ```bash
   curl -X DELETE http://localhost:5001/documents/simple-notebook.ipynb
   curl -X DELETE http://localhost:5001/documents/output-notebook.ipynb
   ```

3. **Revert git branch**:
   ```bash
   git checkout main
   git branch -D 001-jupyter-notebook-support
   ```

---

## Success Checklist

Before proceeding to Phase 2 (Implementation):

- [ ] All FR-001 through FR-013 functional requirements tested
- [ ] All SC-001 through SC-006 success criteria met
- [ ] No browser console errors during normal usage
- [ ] Performance targets achieved (<2s view, <5s for 10MB)
- [ ] Download produces valid .ipynb files
- [ ] Load context enables accurate Q&A
- [ ] Edge cases handled gracefully (errors, empty notebooks, large outputs)

**Phase 1 Testing Complete** → Proceed to Phase 2 (Implementation)

---

## Troubleshooting

### Issue: Notebook doesn't open
- **Check**: Browser console for errors
- **Verify**: RAG backend is running (`curl http://localhost:5001/health`)
- **Test**: Try opening PDF/CSV to isolate notebook-specific issue

### Issue: Syntax highlighting not working
- **Check**: Prism.js loaded (inspect Network tab for CDN requests)
- **Verify**: Code cells have `language-python` class applied
- **Fallback**: Unstyled code still readable (feature degrades gracefully)

### Issue: Images not displaying
- **Check**: Base64 data is valid (inspect HTML `<img>` src attribute)
- **Verify**: MIME type is `image/png` or `image/jpeg`
- **Fallback**: `text/plain` representation shows as fallback

### Issue: Performance too slow
- **Profile**: Use Chrome DevTools Performance tab
- **Check**: JSON parse time (>100ms is concerning for <1MB file)
- **Optimize**: Consider lazy rendering for >50 cells (defer to Phase 2)
