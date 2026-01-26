<!--
SYNC IMPACT REPORT
==================
Version Change: Initial → 1.0.0
Rationale: Initial constitution establishment for mail_summary project

Principles Defined:
  - I. Clean Code: Emphasizes readability, maintainability, PEP 8 compliance, type hints, and comprehensive documentation
  - II. Simple UX: Prioritizes intuitive interfaces, clear feedback, minimal user input, and sensible defaults
  - III. Responsive Design: Ensures fast feedback, async operations, progress indicators, and performance optimization
  - IV. Minimal Dependencies: Mandates dependency justification, stdlib-first approach, and regular audits

Added Sections:
  - Technology Stack: Defines Python 3.11+ requirement, allowed frameworks, and dependency policies
  - Development Workflow: Establishes TDD approach, code review requirements, and quality gates
  - Governance: Amendment procedures, versioning policy, and compliance reviews

Templates Status:
  ✅ plan-template.md: Reviewed - Constitution Check section aligns with defined principles
  ✅ spec-template.md: Reviewed - Requirements structure supports UX and functional principles
  ✅ tasks-template.md: Reviewed - Task categorization supports test-driven development
  ⚠ No commands/*.md directory found - skipped
  ⚠ No README.md found yet - will need creation when project code exists

Follow-up TODOs:
  - RATIFICATION_DATE set to 2026-01-01 (today) as initial establishment
  - Create README.md documenting these principles when project structure is established
  - Ensure .github/agents/*.md files reference this constitution for runtime guidance
-->

# Insight Chat  Constitution

## Core Principles

### I. Clean Code

All code MUST prioritize readability and maintainability over cleverness. Every module, function, and class must serve a clear, singular purpose.

**Non-Negotiable Rules**:
- Follow PEP 8 style guidelines without exception
- Use type hints for all function signatures and class attributes
- Functions MUST be under 50 lines; classes under 300 lines
- Cyclomatic complexity MUST NOT exceed 10 per function
- Every public interface requires docstrings (Google or NumPy style)
- No magic numbers or strings—use named constants
- Meaningful names: no abbreviations except standard conventions (e.g., `msg`, `idx` only in tight loops)

**Rationale**: Clean code reduces cognitive load, accelerates onboarding, minimizes bugs, and enables confident refactoring. In a mail processing system where data integrity is critical, clear logic prevents data loss and security vulnerabilities.

---

### II. Simple UX

User experience MUST be intuitive and require minimal learning curve. Every interface (CLI, API, web) must provide clear feedback and sensible defaults.

**Non-Negotiable Rules**:
- CLI commands MUST follow Unix philosophy: do one thing well
- Error messages MUST be actionable (state what went wrong AND how to fix)
- Configuration MUST work out-of-the-box with secure defaults
- No feature requires reading documentation for basic usage
- Progress indicators MUST appear for operations >2 seconds
- Output MUST support both human-readable and JSON formats
- Confirmation required for destructive operations

**Rationale**: Mail processing affects critical communications. Users must trust the system immediately without extensive training. Poor UX leads to misconfigurations that could result in lost or misdirected emails.

---

### III. Responsive Design

System MUST provide fast feedback and never block user interaction. All operations must feel instantaneous or show clear progress.

**Non-Negotiable Rules**:
- API responses MUST return within 200ms for 95th percentile (p95)
- Long-running operations (>2s) MUST use async/background processing
- UI/CLI MUST remain responsive during background operations
- Progress indicators required for batch operations
- Pagination MANDATORY for results >100 items
- Implement connection pooling for external services (IMAP, SMTP)
- Database queries MUST use indexes; no full table scans in production
- Memory usage MUST NOT exceed 500MB for typical workloads

**Rationale**: Email processing involves high-volume data. Responsive design ensures scalability and maintains user confidence. Blocking operations create perception of system failure.

---

### IV. Minimal Dependencies

Every external dependency MUST be justified by significant value. Prefer Python standard library solutions when feasible.

**Non-Negotiable Rules**:
- New dependencies require explicit justification in PR description
- MUST NOT add dependencies for functionality achievable with stdlib in <100 LOC
- Dependency count MUST NOT exceed 15 direct production dependencies
- All dependencies MUST be actively maintained (commit in last 6 months)
- Security advisories MUST be addressed within 7 days
- Quarterly dependency audits MANDATORY (review necessity, updates, alternatives)
- No transitive dependencies with known CVEs

**Rationale**: Each dependency introduces supply chain risk, maintenance burden, and potential security vulnerabilities. Mail systems handle sensitive data requiring strict security posture. Fewer dependencies = smaller attack surface and faster security patches.

---

## Technology Stack

**Primary Language**: Python 3.11+

**Rationale**: Python 3.11+ provides significant performance improvements, enhanced type system (PEP 673, 675, 681), and better error messages. The ecosystem offers mature email processing libraries.

**Approved Core Dependencies**:
- Email processing: stdlib `email`, `imaplib`, `smtplib` (prefer stdlib unless advanced features required)
- Async: `asyncio` (stdlib), `aiohttp` for async HTTP if needed
- CLI: `click` or `argparse` (stdlib)
- Testing: `pytest`, `pytest-asyncio`
- Type checking: `mypy`
- Linting: `ruff` (replaces multiple tools)

**Prohibited**:
- Frameworks adding >10 transitive dependencies without justification
- Unmaintained libraries (no updates in 12+ months)
- Dependencies with known security issues

---

## Development Workflow

**Test-Driven Development**: Tests written → user approved → tests fail → implementation begins → tests pass

**Code Review Requirements**:
- All PRs require review from at least one maintainer
- Constitution compliance MUST be verified in review checklist
- Breaking changes require documentation update before merge

**Quality Gates**:
- Type checking: `mypy --strict` passes
- Linting: `ruff check` with zero errors
- Test coverage: MUST NOT decrease below baseline (target 80%+)
- Performance: No regression in benchmark suite

---

## Governance

**Amendment Process**:
1. Proposed changes documented in issue with rationale
2. Discussion period (minimum 7 days)
3. Approval required from project maintainers
4. Version bump according to semantic versioning
5. Update all dependent documentation before merging
6. Migration plan for breaking governance changes

**Versioning Policy**:
- MAJOR: Backward-incompatible principle removals or redefinitions
- MINOR: New principles added or materially expanded guidance
- PATCH: Clarifications, wording improvements, non-semantic refinements

**Compliance Reviews**:
- All PRs MUST include constitution compliance verification
- Quarterly audits of codebase against all principles
- Complexity violations require explicit justification and mitigation plan
- Constitution supersedes all other coding standards and practices

**Runtime Guidance**: See `.github/agents/` files for AI agent instructions that enforce these principles during development.

---

**Version**: 1.0.0 | **Ratified**: 2026-01-01 | **Last Amended**: 2026-01-01
