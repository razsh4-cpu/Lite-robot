# Engineering knowledge baseline implementation plan

> **For Codex:** execute this plan inline using the approved evidence policy.

**Goal:** Establish a lightweight canonical engineering-knowledge entry point,
reconstruct high-value evidence-backed records, and add inert initialization
and validation tooling.

**Architecture:** Existing evidence stays authoritative in place. New Markdown
registries and records reference it. A dependency-free Python CLI initializes
and validates the controlled record format.

**Tech stack:** Markdown, Python 3 standard library, pytest.

---

### Task 1: Define and test record validation

1. Add failing focused tests for identifiers, controlled values, planned-test
   constraints, registry membership, link validation, and inert initializers.
2. Implement the smallest standard-library helper that makes them pass.
3. Run the focused test module.

### Task 2: Build the canonical knowledge entry point

1. Add templates and the canonical README/workflow.
2. Reconstruct only high-value sessions and findings backed by repository or
   retained NOMAD evidence.
3. Mark uncertainty explicitly rather than inferring missing metadata.
4. Add registries, capability matrix, current state, issues, lessons, and known
   bad approaches.

### Task 3: Persist the repository workflow

1. Update `AGENTS.md` to require consulting relevant engineering knowledge
   before subsystem work and updating it after meaningful work.
2. Do not alter runtime or safety instructions.

### Task 4: Validate and commit

1. Run the focused tests and the knowledge validator.
2. Run relevant static/document checks and `git diff --check`.
3. Inspect the complete scoped diff and confirm unrelated dirty files are
   excluded.
4. Create one logical commit containing only the engineering baseline.
