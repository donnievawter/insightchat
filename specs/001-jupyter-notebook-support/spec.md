# Feature Specification: Jupyter Notebook Support in RAG System

**Feature Branch**: `001-jupyter-notebook-support`  
**Created**: January 26, 2026  
**Status**: Draft  
**Input**: User description: "handle jupyter notebooks - The RAG system now handles jupiter notebooks as content and they need to be handled correctly here. In particular our view document will have to be updated. It would be nice to be able to run the notebook but before we do that, we need an estimate of the feasibility of that."

## Clarifications

### Session 2026-01-26

- Q: How should the system handle embedded images in notebooks (inline base64 vs. external URLs)? → A: Render inline base64 images directly; external URLs attempt to fetch and display with fallback message if unavailable
- Q: What is the threshold and behavior for truncating extremely large cell outputs? → A: Truncate outputs over 1MB; display first 100KB with "Show More" button to load full content
- Q: When user clicks "Load (All Chunks)" on a notebook, what should be retrieved from the RAG system? → A: All indexed chunks combined
- Q: When the notebook viewer displays code cells, should cell execution metadata (execution count, kernel info) be shown? → A: Only execution count badges (e.g., "In [5]:", "Out [5]:")

## User Scenarios & Testing *(mandatory)*

### User Story 1 - View Notebook Content in Browser (Priority: P1)

Users can view Jupyter notebook (.ipynb) files directly in the chat interface when they appear as sources or are browsed through the document browser. The notebook is displayed with proper formatting showing markdown cells and code cells with syntax highlighting, preserving the structure and readability of the original notebook.

**Why this priority**: This is the foundational capability - users must be able to see notebook content before any other interactions are useful. Without viewing, notebooks are opaque binary files.

**Independent Test**: Can be fully tested by uploading a .ipynb file to the RAG system, then clicking "View" in the document browser. The notebook displays with formatted markdown and syntax-highlighted code cells, delivering immediate value for content review.

**Acceptance Scenarios**:

1. **Given** a Jupyter notebook has been indexed by the RAG system, **When** the user clicks "View" on the notebook in the document browser, **Then** the notebook opens in the document viewer displaying all cells with proper formatting
2. **Given** a chat response includes a notebook as a source, **When** the user clicks the source link, **Then** the notebook content is displayed with markdown cells rendered and code cells syntax-highlighted
3. **Given** a notebook with mixed cell types (markdown, code, raw), **When** the user views it, **Then** each cell type is visually distinct and properly formatted
4. **Given** a notebook with cell outputs (text, images, tables), **When** the user views it, **Then** the outputs are displayed below their respective code cells

---

### User Story 2 - Download Notebooks (Priority: P2)

Users can download Jupyter notebook files from the chat interface to their local machine, preserving the original .ipynb format and all cell content, outputs, and metadata.

**Why this priority**: This enables users to work with notebooks locally in their own Jupyter environment, which is essential for editing and re-running analyses.

**Independent Test**: Can be fully tested by viewing a notebook and clicking a "Download" button, verifying the downloaded .ipynb file opens correctly in local Jupyter Lab/Notebook.

**Acceptance Scenarios**:

1. **Given** a notebook is displayed in the viewer, **When** the user clicks the "Download" button, **Then** the original .ipynb file is downloaded to their default download location
2. **Given** a downloaded notebook file, **When** the user opens it in Jupyter Lab or Notebook, **Then** all cells, outputs, and metadata are preserved exactly as they were in the RAG system

---

### User Story 3 - Load Notebook Context for Chat (Priority: P2)

Users can load the entire content of a notebook (all cells and outputs) into the chat context, allowing them to ask questions about the notebook's code, analysis, or results.

**Why this priority**: This leverages the RAG system's core value - enabling natural language queries about technical content. Users can ask about algorithms, explain visualizations, or get help debugging notebook code.

**Independent Test**: Can be fully tested by clicking "Load" on a notebook, then asking a question like "What does this notebook analyze?" and receiving a response based on the notebook's full content.

**Acceptance Scenarios**:

1. **Given** a notebook in the document browser, **When** the user clicks "Load (All Chunks)", **Then** all notebook cells are loaded into the chat context and available for questioning
2. **Given** notebook content has been loaded, **When** the user asks "What libraries does this notebook use?", **Then** the assistant responds with libraries imported in the notebook's code cells
3. **Given** a notebook with data visualizations, **When** the user asks "What insights does the analysis show?", **Then** the assistant can reference both code cells and their outputs to explain findings

---

### User Story 4 - Interactive Notebook Execution (Priority: P3)

Users can execute individual code cells or entire notebooks directly from the browser interface, seeing live outputs without leaving the chat application. This requires a backend kernel connection and security considerations.

**Why this priority**: This is a "nice to have" advanced feature that would provide the most interactive experience, but it requires significant infrastructure (kernel management, security sandboxing, resource limits) and may not be feasible initially.

**Independent Test**: Requires backend Jupyter kernel server, execution sandboxing, and security model as detailed in the Feasibility Assessment section. Can be tested by running a simple code cell and verifying output appears correctly.

**Acceptance Scenarios**:

1. **Given** a notebook is displayed with a "Run" button on each cell, **When** the user clicks "Run" on a code cell, **Then** the cell executes and displays output below it
2. **Given** a notebook with dependencies, **When** the user attempts to run a cell, **Then** the system checks if required packages are available and displays appropriate warnings if missing
3. **Given** a long-running cell execution, **When** the user wants to stop it, **Then** an "Interrupt" button is available to halt execution

---

### Edge Cases

- What happens when viewing a notebook with very large outputs (e.g., 10MB of data printed to stdout)?
- How does the system handle notebooks with embedded images or custom widgets that require JavaScript?
- What happens when a notebook file is corrupted or has invalid JSON structure?
- How does the viewer handle notebooks created with different Jupyter versions or kernels (Python, R, Julia)?
- What happens when users try to load a notebook that exceeds the chat context size limit?
- How are notebooks with special characters or non-ASCII content in cell outputs displayed?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST detect .ipynb files by extension and MIME type when processing documents in the RAG system
- **FR-002**: System MUST parse the JSON structure of .ipynb files to extract cells, cell types, and content
- **FR-003**: System MUST render markdown cells with proper HTML formatting (headers, lists, code blocks, links, images)
- **FR-004**: System MUST display code cells with syntax highlighting appropriate to the notebook's kernel language
- **FR-005**: System MUST display cell outputs including text, error messages, tables, and images inline below code cells; inline base64-encoded images render directly while external image URLs attempt fetch with fallback message on failure
- **FR-006**: System MUST provide a "Download" action that serves the original .ipynb file with correct MIME type
- **FR-007**: System MUST provide a "Load (All Chunks)" action that retrieves all indexed chunks from the RAG system and combines them into the chat context
- **FR-008**: System MUST handle notebooks with missing or empty cells gracefully without errors
- **FR-009**: System MUST display a distinct visual indicator (badge or icon) for notebook files in the document browser
- **FR-010**: System MUST preserve the cell execution order when displaying notebooks (respecting execution_count metadata)
- **FR-011**: System MUST handle notebooks without outputs (unexecuted notebooks) by showing only the source code
- **FR-012**: System MUST truncate cell outputs exceeding 1MB by displaying first 100KB with "Show More" button to load remaining content on demand
- **FR-013**: System MUST display execution count badges (e.g., "In [5]:", "Out [5]:") for code cells that have execution_count metadata

### Key Entities *(include if feature involves data)*

- **Jupyter Notebook**: A JSON file containing cells, metadata, and optional execution outputs. Key attributes: cells array, metadata object, nbformat version
- **Notebook Cell**: A unit of content within a notebook. Key attributes: cell_type (code/markdown/raw), source (text content), outputs (for code cells), execution_count
- **Cell Output**: The result of executing a code cell. Key attributes: output_type (stream/display_data/execute_result/error), data (content in various MIME types like text/plain, image/png, text/html), metadata

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can view any valid .ipynb file in the browser within 2 seconds of clicking "View"
- **SC-002**: Notebook viewer correctly renders 95% of notebooks without formatting errors (based on test suite of diverse notebooks)
- **SC-003**: Users can successfully download notebooks and re-open them in local Jupyter environments with 100% fidelity
- **SC-004**: Loaded notebook context enables accurate question answering - assistant can correctly identify notebook libraries, functions, and analysis results in 90% of test queries
- **SC-005**: System handles notebooks up to 10MB in size without browser crashes or excessive loading times (under 5 seconds)
- **SC-006**: Cell outputs with images up to 5MB render correctly in the viewer

## Assumptions

- Notebooks in the RAG system are assumed to be in standard Jupyter nbformat (v4.0+)
- The existing document viewer infrastructure can be extended to support notebook rendering
- Users have modern browsers with JavaScript enabled for interactive notebook viewing
- For P1-P3 priorities, server-side rendering of notebook HTML is acceptable (no kernel execution required)
- Notebook execution (P4) would require a separate backend service (JupyterHub, BinderHub, or custom kernel manager)
- Security model for notebook execution would need to include sandboxing, resource limits, and user authentication

## Scope

### In Scope

- Viewing Jupyter notebooks with formatted cells in the browser
- Rendering markdown cells with standard markdown elements
- Syntax highlighting for code cells (Python, R, Julia, etc.)
- Displaying cell outputs including text, tables, images, and error messages
- Downloading notebooks in original .ipynb format
- Loading notebook content into chat context for Q&A
- Visual distinction of notebooks in document browser

### Out of Scope (for initial release)

- Interactive notebook execution/kernel management (deferred to P4 feasibility study)
- Editing notebook cells in the browser
- Creating new notebooks from scratch in the chat interface
- Support for Jupyter widgets or interactive visualizations requiring JavaScript execution
- Version control or diff viewing for notebook changes
- Collaborative editing or real-time multi-user notebook sessions

## Dependencies

- Existing document viewer modal and routing infrastructure in chat.html
- Backend document processing pipeline in document_processor.py
- File type detection and MIME type handling in the RAG indexing system
- Markdown rendering library or function (already exists for .md files)
- Syntax highlighting library for code cells (e.g., Prism.js, highlight.js)
- JSON parsing capability for .ipynb file structure

## Feasibility Assessment: Interactive Notebook Execution (P4)

### Technical Requirements

To enable in-browser notebook execution, the system would need:

1. **Jupyter Kernel Server**: A backend service running Jupyter kernels (e.g., JupyterHub, JupyterLab Server, or custom kernel gateway)
2. **WebSocket Connection**: Real-time bidirectional communication between browser and kernel for code execution and output streaming
3. **Kernel Management**: Lifecycle management (start, stop, restart), resource allocation, and cleanup for user sessions
4. **Security Sandboxing**: Isolated execution environments to prevent malicious code from accessing system resources or other users' data
5. **Resource Limits**: CPU, memory, and execution time constraints to prevent abuse and ensure system stability
6. **Package Management**: Mechanism to handle notebooks requiring specific Python packages or dependencies
7. **Authentication & Authorization**: User identity verification and permissions for kernel access

### Estimated Complexity

- **High Complexity**: Requires significant infrastructure beyond current Flask application
- **Estimated Development Time**: 4-6 weeks for MVP (basic execution), 8-12 weeks for production-ready system
- **Infrastructure Costs**: Additional server resources for kernel processes, potentially separate execution environment
- **Security Risks**: Code execution is inherently risky - requires thorough security review and sandboxing

### Alternatives to Full Execution

1. **Static Preview Only**: Show pre-executed notebooks with saved outputs (current P1-P3 approach)
2. **External Execution Links**: Provide "Open in Binder" or "Open in Google Colab" buttons that launch notebooks in external services
3. **Scheduled Batch Execution**: Allow users to request notebook execution, which runs server-side and updates outputs asynchronously
4. **Read-Only Kernel Replay**: Display saved execution outputs in sequence, simulating execution without actually running code

### Recommendation

For the initial release (P1-P3), focus on robust viewing, downloading, and context loading. Defer interactive execution (P4) until:
- User demand is validated through usage metrics of notebook viewing
- Infrastructure and security requirements are fully scoped
- Budget and resources are allocated for kernel management infrastructure

If execution becomes a priority, consider "External Execution Links" as a low-effort intermediate solution that leverages existing services like Binder or Colab.

