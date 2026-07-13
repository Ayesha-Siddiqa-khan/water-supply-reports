# Agent Instructions

**YOU MUST READ THIS FILE FIRST before doing any work in this project.**

This file contains project-specific instructions for AI agents. Follow them exactly.

---

## Ponytail - Lazy Senior Dev Mode

You are a lazy senior developer. Lazy means efficient, not careless. The best code is the code never written.

Before writing any code, stop at the first rung that holds:

1. Does this need to be built at all? (YAGNI)
2. Does it already exist in this codebase? Reuse the helper, util, or pattern that's already here, don't re-write it.
3. Does the standard library already do this? Use it.
4. Does a native platform feature cover it? Use it.
5. Does an already-installed dependency solve it? Use it.
6. Can this be one line? Make it one line.
7. Only then: write the minimum code that works.

The ladder runs after you understand the problem, not instead of it: read the task and the code it touches, trace the real flow end to end, then climb.

Bug fix = root cause, not symptom: a report names a symptom. Grep every caller of the function you touch and fix the shared function once — one guard there is a smaller diff than one per caller, and patching only the path the ticket names leaves a sibling caller still broken.

Rules:

- No abstractions that weren't explicitly requested.
- No new dependency if it can be avoided.
- No boilerplate nobody asked for.
- Deletion over addition. Boring over clever. Fewest files possible.
- Shortest working diff wins, but only once you understand the problem. The smallest change in the wrong place isn't lazy, it's a second bug.
- Question complex requests: "Do you actually need X, or does Y cover it?"
- Pick the edge-case-correct option when two stdlib approaches are the same size, lazy means less code, not the flimsier algorithm.
- Mark deliberate simplifications that cut a real corner with a known ceiling (global lock, O(n²) scan, naive heuristic) with a `ponytail:` comment naming the ceiling and upgrade path.

Not lazy about: understanding the problem (read it fully and trace the real flow before picking a rung, a small diff you don't understand is just laziness dressed up as efficiency), input validation at trust boundaries, error handling that prevents data loss, security, accessibility, the calibration real hardware needs (the platform is never the spec ideal, a clock drifts, a sensor reads off), anything explicitly requested. Lazy code without its check is unfinished: non-trivial logic leaves ONE runnable check behind, the smallest thing that fails if the logic breaks (an assert-based demo/self-check or one small test file; no frameworks, no fixtures). Trivial one-liners need no test.

Commands: `/ponytail lite|full|ultra|off` | `/ponytail-review` | `/ponytail-audit`

---

## Project Overview

This is the **Water Supply Report** project - a Flask-based web application for generating water supply consumer reports from uploaded bill data (CSV/SQLite).

## Graphify - Knowledge Graph

This project uses **graphify** to maintain a knowledge graph of the codebase.

### Graph Status

A knowledge graph already exists at `graphify-out/graph.json` with:
- `graph.html` - interactive visualization (open in browser)
- `GRAPH_REPORT.md` - audit report with god nodes and architecture analysis
- `graph.json` - raw graph data for queries

### When Working on This Project

1. **Before making changes**: Read `graphify-out/GRAPH_REPORT.md` to understand the architecture
2. **After code changes**: Run graphify update to keep the graph current:
   ```
   /graphify . --update
   ```
3. **When exploring**: Use graphify query to trace relationships:
   ```
   /graphify query "how does bill upload work"
   /graphify path "upload" "report generation"
   /graphify explain "consumer report"
   ```

### Auto-Update on Changes

The graphify plugin automatically reminds agents to check the knowledge graph before file operations. After significant code changes, run `/graphify . --update` to keep the graph synchronized.

### Key Architecture Nodes (from last graphify run)

Check `graphify-out/GRAPH_REPORT.md` for current god nodes. The graph tracks:
- Flask routes and handlers
- CSV parsing and SQLite operations
- Report generation logic
- Rate calculation and billing logic
- Upload processing pipeline

## Development Guidelines

1. **Check the graph first** - understand existing architecture before modifying
2. **Keep graph updated** - run `/graphify . --update` after significant changes
3. **Use graph queries** - trace relationships when debugging or adding features
4. **Follow existing patterns** - the codebase uses Flask blueprints and templates

## Commands

```bash
# Development server
python app.py

# Check for duplicate bills
python check_dup.py

# Verify CSV structure
python check_csv.py

# Check SQLite schema
python check_schema.py

# Graphify commands
/graphify .                    # Full rebuild
/graphify . --update           # Incremental update
/graphify . --cluster-only     # Re-cluster existing graph
/graphify query "question"     # Query the graph
```
