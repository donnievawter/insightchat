# Image Display Solution for Markdown Files

## Problem
The InsightChat application displays markdown files but images referenced with relative paths (e.g., `![alt text](../images/photo.png)`) were not rendering in the browser because:

1. Browser cannot access filesystem paths directly
2. The markdown parser didn't handle image syntax `![alt](path)`
3. Image URLs weren't converted to use the backend document serving route

## Solution Implemented

### 1. Updated Markdown Parser (`markdownToHtml` function)
**Location:** `flask-chat-app/templates/chat.html` (line ~1550)

Added support for:
- Parsing markdown image syntax: `![alt text](image/path.png)`
- Accepting an optional `docSource` parameter for resolving relative paths
- Converting image paths to use the backend `/document` route
- Error handling when images fail to load

### 2. Added Path Resolution Helper (`resolveMarkdownPath` function)  
**Location:** `flask-chat-app/templates/chat.html` (line ~1552)

Features:
- Resolves relative paths (e.g., `../png/image.png`) based on the markdown document's location
- Handles absolute paths and HTTP(S) URLs
- Normalizes paths by processing `../ `and `./` segments

### 3. Updated Function Calls
Updated `markdownToHtml()` calls to pass document source path where available:
- In `displayTextDocument()` - when viewing markdown files
- In `openMarkdownInNewTab()` - when opening markdown in new tab

## How It Works

### Example Scenario
Given a markdown file at: `/mnt/devnotes/md/networktopology.md`

Containing: `![Network Topology](../png/networkinfrastructure.png)`

**Processing Steps:**
1. Markdown parser detects image syntax
2. `resolveMarkdownPath()` resolves `../png/networkinfrastructure.png` relative to `/mnt/devnotes/md/`
3. Result: `/mnt/devnotes/png/networkinfrastructure.png`
4. Converts to backend URL: `/document?source=/mnt/devnotes/png/networkinfrastructure.png`
5. Browser fetches image through the backend route
6. Backend's `get_document()` route serves the image with proper content type

### Existing Backend Infrastructure
The solution leverages the existing `/document` route in `routes.py` which already:
- Fetches files via the RAG API's `/document` endpoint
- Handles binary content (images, PDFs, etc.)
- Sets appropriate content types (`image/png`, `image/jpeg`, etc.)

## Testing

To test, view any markdown document in the RAG system that contains images:

1. Browse documents in InsightChat
2. Select a markdown file with image references
3. Images should now display inline with the markdown content
4. If an image is not found, an error message will display

## Path Resolution Examples

From document at `/docs/tutorial/guide.md`:

| Markdown Image Path | Resolved Path |
|---------------------|---------------|
| `image.png` | `/docs/tutorial/image.png` |
| `../images/photo.png` | `/docs/images/photo.png` |
| `../../assets/logo.png` | `/assets/logo.png` |
| `http://example.com/img.png` | `http://example.com/img.png` (unchanged) |
| `/absolute/path.png` | `/absolute/path.png` (unchanged) |

## Error Handling

When an image cannot be loaded:
- Image element hides automatically (via `onerror` handler)
- Error message displays showing the resolved path
- Rest of markdown content continues to render normally

## Browser Compatibility

The solution uses:
- Standard HTML `<img>` tags
- CSS for responsive sizing (`max-width: 100%; height: auto`)
- JavaScript `onerror` event handler (widely supported)

## Future Enhancements

Potential improvements:
1. Image caching to reduce backend requests
2. Thumbnail generation for large images  
3. Lightbox/zoom functionality
4. Support for image sizing attributes
5. Lazy loading for documents with many images

## Files Modified

- `flask-chat-app/templates/chat.html`:
  - Added `resolveMarkdownPath()` function
  - Updated `markdownToHtml()` to handle images and accept `docSource` parameter
  - Updated function calls to pass document source paths
