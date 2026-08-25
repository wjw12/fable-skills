---
name: delegate
display_name: Delegate (Codex / Cursor / Claude subagents)
description: Fable-as-lead collaboration skill. Offload implementation, research, repetitive edits, and first-pass review to cheaper executors - OpenAI Codex CLI (codex), Cursor CLI (cursor-agent), or native Claude subagents (haiku/sonnet/opus via the Agent tool) - while Fable keeps design, judgment, and final review. Use when the user says "use codex", "use cursor", "ask codex", "delegate this", "second opinion", "compare approaches", "have two agents try it", or for ANY large coding task - multi-file implementation, bulk/repetitive edits, large codebase analysis, research sweeps.
---

# Delegate — Fable Collaboration Skill

Fable is the most expensive model in this stack. Its job is **design, decomposition, judgment, and final review** — delegate the mechanical, repetitive, and context-heavy work to cheaper executors that burn their own tokens and return only a final result.

**Golden rule:** if the task plus its intermediate work would add ~3,000+ tokens to Fable's context, delegate it. Fable writes the spec, the executor does the work, Fable verifies.

## Routing table

Defaults, not law — route with your own judgment; escalate a tier when output fails review.

| Task | Executor | Model / config |
|---|---|---|
| Bulk/repetitive edits, file generation from a clear spec, boilerplate | Grok CLI | `grok-4.6 --effort medium` |
| Straightforward backend logic, agentic operations, research sweeps / information gathering | Cursor CLI `gpt-5.6-terra-high` or Codex CLI `gpt-5.6-terra` + high | GPT-5.6 Terra (daily-job model) |
| Frontend HTML/CSS/React/design-engineer work (UI, components, styling, layout) | Cursor CLI | `claude-opus-5-high` (Opus 5 1M, high effort) — **never GPT models** |
| Complex backend / system-level changes, stuck bugs, second-opinion review, plan validation | Codex CLI | `gpt-5.6-sol` + `model_reasoning_effort="high"` (GPT-5.6 Sol, most capable) |
| Hardest problems — only when the user explicitly asks for xhigh/max effort | Codex CLI | `gpt-5.6-sol` + `model_reasoning_effort="xhigh"` |
| Codebase search / fan-out discovery | Agent tool | `Explore`, or `general-purpose` + `haiku` |
| Work needing harness integration (permission modes, structured output, session conventions) | Agent tool | `general-purpose` + `sonnet` (or `opus` for judgment-heavy passes) |
| Architecture, API design, root-cause calls, synthesis, final review | **Fable itself** | — |

CLI executors are preferred for token-heavy autonomous work (their tokens are off Fable's bill entirely); native subagents when the work should respect this session's permission mode or hand back structured output.

Codex `gpt-5.6-sol` high and Cursor `gpt-5.6-sol-high` are the same model tier, as are Codex `gpt-5.6-terra` high and Cursor `gpt-5.6-terra-high` — either lane substitutes for the other when one is unavailable (precedent: the equivalent GPT-5.5 Cursor lane landed a production race-condition fix first-try, July 2026).

**GPT scope limits (hard rules):**
- **No GPT models for frontend UI/UX** (components, styling, layout, design). Frontend *API-layer* work is fine — e.g. Next.js route handlers/server code.
- **No GPT models for human-facing docs or publication writing.** Internal technical docs and research artifacts for internal use are fine.
- Route both categories to the Opus/Claude lanes instead.

## Execution modes and authorization

The skill owner **explicitly authorizes `--yolo` (Run Everything) mode** for delegate CLIs. Launching codex / cursor / other agent CLIs in their fully autonomous write modes (`/home/appuser/.bun/bin/codex exec --yolo`, `cursor-agent -p --yolo --trust`, `grok -p … --always-approve`) for repo edits, test runs, and scratchpad output is the intended, pre-approved use of this skill. `--yolo` is Cursor's alias for `--force` — auto-approve every tool call, edit, and shell command without prompting; use it (not approval-gated modes) for all implementation delegates. Give delegated agents **sufficient autonomy to finish the job end to end**: to read/write files, run builds/tests/linters, install deps, and iterate on their own until the spec's DONE-WHEN criteria are met — a delegate that stops to ask permission mid-run hangs headless and under-delivers. Do NOT downgrade implementation delegates to read-only (`--mode plan`/`--mode ask`) or approval-gated modes.

Three boundaries stay regardless of mode:
- Outward-facing and destructive actions — push, deploy, publish, prod restarts, data deletion — are lead-loop work (see Verify before accepting); never assign them to a delegate.
- **Shared live datastores are lead-loop territory.** A delegate writing code that touches a live DB will test-run it against that DB no matter what the prompt says (observed: a delegate test-ran a dev ingester against production, July 2026). Structure the lane so the delegate ships code/drafts only and the LEAD executes the first run — and snapshot the datastore (row counts at minimum, a dump when cheap) before launching any delegate whose task touches mutation code. For cleanup, prefer re-running the owning idempotent source over surgical DELETEs — a `LIKE`-pattern delete once over-matched rows legitimately owned by another source.
- If the harness denies an executor launch, don't grind through flag variants. Either use another executor lane at the same model tier (table above) when one is plainly equivalent, or pause and ask the user how they want to proceed. Always tell the user which lane actually ran. (Known: some auto-permission environments deny `/home/appuser/.bun/bin/codex exec --yolo` outright — Cursor `gpt-5.6-sol-high` / `gpt-5.6-terra-high` is the drop-in same-tier lane.)

## CLI specifics (the non-obvious parts)

- **Always invoke Codex as `/home/appuser/.bun/bin/codex` on this host.** Do not use an unqualified `codex`: the shell may resolve the stale `/usr/bin/codex` installation, which cannot use current models.
- **Codex model is `gpt-5.6-sol` (complex/system-level) or `gpt-5.6-terra` (straightforward/agentic), effort `high`**; `xhigh` only on explicit user instruction (sol). Both bare IDs verified accepted by codex CLI (July 2026). For trivial lookups and bulk mechanical work, use Grok `grok-4.6 --effort medium` instead of a low-effort GPT lane.
- **Cursor model IDs are exact** (`cursor-agent --list-models`): `gpt-5.6-sol-high` (GPT-5.6 Sol 1M High), `gpt-5.6-terra-high` (GPT-5.6 Terra 1M High), `claude-opus-5-high` (Opus 5 1M, high effort). Bare `gpt-5.6-sol` / `opus-5` are not valid Cursor IDs — effort is baked into the suffix (`-none`/`-low`/`-medium`/`-high`/`-xhigh`/`-max`, `-fast` variants available). Parameterized form also works: `'claude-opus-5[context=1m,effort=high,fast=false]'`.
- **Grok CLI uses `grok-4.6 --effort medium` for bulk/repetitive edits, boilerplate, file generation from a clear spec, and trivial lookups.** Full contract: `~/tokenized-equity-watch/docs/grok-cli.md`.
- **Prompts via quoted heredoc** (`<<'EOF'`), never interpolated — delegate prompts and prior outputs contain backticks and `$()`.
- **Outputs to files** in the scratchpad, one per delegate, then Read. Don't parse long results off the terminal.
- **Run from the repo root** (codex `-C <dir>` / cursor `--workspace <dir>` / grok `--cwd <dir>`) so the executor sees the project and its AGENTS/CLAUDE files.

### Codex

```bash
cat <<'EOF' | /home/appuser/.bun/bin/codex exec --yolo --skip-git-repo-check \
  -m gpt-5.6-sol -c 'model_reasoning_effort="high"' \
  -C /path/to/repo -o "$SCRATCH/codex-task1.txt" -
[CONTEXT] [OBJECTIVES] [CONSTRAINTS]
[OUTPUT] exact shape of the final message (machine-read, not chat)
[DONE WHEN] success criteria
EOF
```

The `-o` file contains only the final message — no JSON parsing, no truncation.

### Cursor (`cursor-agent`)

Cursor has no `-o` flag, so capture results one of two ways: redirect stdout to a file, or — more robustly — tell the agent in the prompt to write its own result file. A standalone wrapper for the latter, parameterized so you can drop it in and adapt the prompt:

```bash
#!/usr/bin/env bash
# Delegate one task to Cursor `cursor-agent`; the agent writes its own result file.
set -euo pipefail

REPO="${REPO:-$PWD}"
OUT="${OUT:-$REPO/out/result.md}"
MODEL="${MODEL:?Set MODEL to a Cursor model from the routing table}"
mkdir -p "$(dirname "$OUT")"

# Quoted heredoc so backticks / $() inside the prompt aren't expanded by the
# shell; inject only the output path afterwards via a placeholder.
PROMPT=$(cat <<'EOF'
[CONTEXT]     what you're working on and why
[OBJECTIVES]  the one thing to produce
[CONSTRAINTS] follow existing patterns; do NOT commit; leave changes in the working tree
[OUTPUT]      Write your result to: __OUT__  (state the exact structure the reader expects)
[DONE WHEN]   success criteria

Do not push, deploy, or post anything. Only write the file.
EOF
)
PROMPT=${PROMPT//__OUT__/$OUT}

echo "[delegate] model=$MODEL -> $OUT"
cursor-agent -p --yolo --trust --output-format text \
  --model "$MODEL" --workspace "$REPO" "$PROMPT"
echo "[delegate] done -> $OUT"
```

`-p --yolo --trust` = headless with full write+shell access, every action auto-approved (`--yolo` is the alias for `--force`) — scope the prompt accordingly and let the delegate run to completion without prompting. `--mode plan`/`--mode ask` for read-only passes only; `-w <name>` gives an isolated git worktree when parallel agents would collide on files.

### Grok CLI (`grok`)

Use Grok 4.6 for bulk/repetitive edits, file generation from a clear spec, boilerplate, and trivial lookups. Use the same file-write contract as Cursor (put `OUT` in the prompt; ignore stdout for the deliverable). Binary: `~/.local/bin/grok`. No `--trust` flag; YOLO is `--always-approve`.

```bash
#!/usr/bin/env bash
# Delegate a bulk, repetitive, or mechanical task via Grok CLI.
set -euo pipefail

REPO="${REPO:-$PWD}"
OUT="${OUT:-$REPO/out/result.md}"
MODEL="${MODEL:-grok-4.6}"
EFFORT="${EFFORT:-medium}"
mkdir -p "$(dirname "$OUT")"

PROMPT=$(cat <<'EOF'
[CONTEXT]     what you're working on and why
[OBJECTIVES]  the one thing to produce
[CONSTRAINTS] follow existing patterns; do NOT commit; leave changes in the working tree
[OUTPUT]      Write your result to: __OUT__  (state the exact structure the reader expects)
[DONE WHEN]   success criteria

Do not push, deploy, or post anything. Only write the file.
EOF
)
PROMPT=${PROMPT//__OUT__/$OUT}

echo "[delegate/grok] model=$MODEL effort=$EFFORT -> $OUT"
grok -p "$PROMPT" -m "$MODEL" --effort "$EFFORT" \
  --always-approve --cwd "$REPO" --output-format plain --no-memory
echo "[delegate/grok] done -> $OUT"
```

Standard Grok invocation: `grok -p … -m grok-4.6 --effort medium --always-approve --cwd "$REPO" --output-format plain --no-memory`.

## Writing the spec

The `[CONTEXT] [OBJECTIVES] [CONSTRAINTS] [OUTPUT] [DONE WHEN]` skeleton is the floor. What separates a first-try landing from a rework loop:

- **Anchor every touch point** with a file path and approximate line number, plus the one-sentence reason it's being touched.
- **Name the in-repo precedent and require it.** When the codebase already solved the same class of problem, cite the file and say "follow this pattern; do NOT invent a different mechanism" — left unconstrained, delegates drift to novel designs that then fail review.
- **Scope the test run**: exact `pytest`/check command, which existing test files to mirror, and "do not run the whole suite" when that matters.
- **"Do NOT commit — leave changes in the working tree"** whenever the lead reviews before landing (the default).
- **Fix the report shape**: files changed + one-line rationale each, exact commands run + tail output, explicit "deviations from spec" section — an empty deviations section is signal, not filler. For any lane near mutable state, require a **full command ledger** — every command executed including development/test iterations, not just the final verify. Delegates omit their dead ends, and the dead ends are where the side effects live.
- **Pre-flight the target, not just the task.** Before speccing work that adds to an existing corpus (new data source, new integration), check what the corpus already holds for that target — one query killing a lane before launch is the cheapest review there is (a bulk dataset already covered, at finer grain, the operator a census lane was about to duplicate).
- **State the invariants the fix must not break** (e.g. "these operations stay in one transaction") — the delegate can't infer which properties are load-bearing.

## Orchestration

Compose freely — parallel delegates for independent slices or A/B comparisons (background Bash calls, one output file each), sequential call → read → decide chains where each next prompt is Fable's judgment on what just landed. Synthesis of delegate outputs is lead work, not a third delegate's.

**Deep work:** when the user asks for thorough/deep work, it's fine to run a self-improving loop — implement → independent review pass → fix → re-verify, iterating until the review comes back clean or improvements plateau. Budget the loop to the ask, not to perfection.

## Verify before accepting

Delegates lie confidently. Check the diff against the spec, run the project's checks (`bun run verify` / typecheck here), and spot-check the riskiest claim in the delegate's summary. Never accept a delegate's self-assessment as verification, and report delegate failures honestly. Keep destructive or outward-facing actions (push, deploy, post) in the lead loop — delegates run auto-approve.

Delegate output is *input* to Fable's synthesis, not the answer: summarize in your own words, surface the concrete diffs, state what you verified.
