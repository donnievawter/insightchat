# InsightChat - Markdown Image Display: Quick Reference

## The Problem
```markdown
# document.md at /docs/guide/tutorial.md
![Diagram](../images/diagram.png)
```
❌ Browser cannot access filesystem paths → Image doesn't display

## The Solution

### 1. Parse Image Syntax
```javascript
// Regex matches: ![alt text](path)
/!\[([^\]]*)\]\(([^)]+)\)/g
```

### 2. Resolve Relative Paths
```javascript
Document:  /docs/guide/tutorial.md
Image:     ../images/diagram.png
→ Resolved: /docs/images/diagram.png
```

### 3. Convert to Backend URL
```javascript
/document?source=/docs/images/diagram.png
```

### 4. Server Delivers Image
```
Flask route → RAG API → Filesystem → Browser
```

## Architecture

```
┌─────────────────────────────────────────────────────┐
│ Browser                                             │
│  ├─ chat.html (markdown renderer)                   │
│  ├─ markdownToHtml(content, docSource)             │
│  └─ <img src="/document?source=...">               │
└───────────┬─────────────────────────────────────────┘
            │ HTTP GET /document?source=<path>
            ▼
┌─────────────────────────────────────────────────────┐
│ Flask Backend (routes.py)                           │
│  └─ get_document() route                            │
│     └─ fetch_document_content(source, rag_url)     │
└───────────┬─────────────────────────────────────────┘
            │ POST /document with file_path
            ▼
┌─────────────────────────────────────────────────────┐
│ RAG API                                             │
│  └─ Returns file content with content_type          │
└───────────┬─────────────────────────────────────────┘
            │ Reads from filesystem
            ▼
┌─────────────────────────────────────────────────────┐
│ Filesystem                                          │
│  └─ /mnt/devnotes/png/image.png                    │
└─────────────────────────────────────────────────────┘
```

## Code Changes

### Added: resolveMarkdownPath()
```javascript
function resolveMarkdownPath(imagePath, docSource) {
    // Handles: ../path, ../../path, ./path
    // Returns: absolute path
}
```

### Updated: markdownToHtml()  
```javascript
function markdownToHtml(markdown, docSource) {
    // NEW: Processes image syntax
    html = html.replace(/!\[([^\]]*)\]\(([^)]+)\)/g, ...);
    // ... existing markdown parsing ...
}
```

### Updated: Function Calls
```javascript
// Before
markdownToHtml(content)

// After  
markdownToHtml(content, source)
```

## Example Transformations

| Markdown | Document Path | Resolved Image Path |
|----------|---------------|---------------------|
| `![](img.png)` | `/docs/guide.md` | `/docs/img.png` |
| `![](../images/photo.png)` | `/docs/tutorial/page.md` | `/docs/images/photo.png` |
| `![](http://url.com/img.png)` | any | `http://url.com/img.png` |

## Testing

1. **View the test document:**
   - Path: `/mnt/devnotes/md/test-image-display.md`
   - Contains working and non-existent image examples

2. **Expected Results:**
   - ✅ Existing images display inline
   - ❌ Missing images show error message
   - 📝 Markdown text renders normally

## Error Handling

```html
<img src="..." onerror="this.style.display='none'; ..." />
<div style="display: none;">
  ⚠️ Image not found: /resolved/path.png
</div>
```

## Browser View

### Success:
```
┌─────────────────────────┐
│ # Markdown Title        │
│                         │
│ Some text content...    │
│                         │
│ ┌───────────────────┐   │
│ │                   │   │
│ │  [Image Displays] │   │
│ │                   │   │
│ └───────────────────┘   │
│                         │
│ More text content...    │
└─────────────────────────┘
```

### Failure:
```
┌─────────────────────────┐
│ # Markdown Title        │
│                         │
│ ┌─────────────────────┐ │
│ │ ⚠️ Image not found:  │ │
│ │ /path/to/image.png  │ │
│ └─────────────────────┘ │
│                         │
│ More text content...    │
└─────────────────────────┘
```

## Files Modified

- ✏️ `flask-chat-app/templates/chat.html` (~80 lines changed)
  - Added `resolveMarkdownPath()` helper
  - Updated `markdownToHtml()` to handle images
  - Updated function calls to pass document source

## No Backend Changes Required!

The existing `/document` route already handles:
- ✅ Fetching files via RAG API
- ✅ Binary content (images)
- ✅ Proper content types
- ✅ Error handling
