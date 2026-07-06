---
name: delegate
display_name: Delegate (Codex / Cursor / Claude subagents)
description: Fable-as-lead collaboration skill. Offload implementation, research, repetitive edits, and first-pass review to cheaper executors - OpenAI Codex CLI (codex), Cursor CLI (agent), or native Claude subagents (haiku/sonnet/opus via the Agent tool) - while Fable keeps design, judgment, and final review. Use when the user says "use codex", "use cursor", "ask codex", "delegate this", "second opinion", "compare approaches", "have two agents try it", or for ANY large coding task - multi-file implementation, bulk/repetitive edits, large codebase analysis, research sweeps.
---

# Delegate — Fable Collaboration Skill

Fable is the most expensive model in this stack. Its job is **design, decomposition, judgment, and final review** — delegate the mechanical, repetitive, and context-heavy work to cheaper executors that burn their own tokens and return only a final result.

**Golden rule:** if the task plus its intermediate work would add ~3,000+ tokens to Fable's context, delegate it. Fable writes the spec, the executor does the work, Fable verifies.

## Routing table

Defaults, not law — route with your own judgment; escalate a tier when output fails review.

| Task | Executor | Model / config |
|---|---|---|
| Bulk/repetitive edits, file generation from a clear spec, boilerplate | Cursor CLI | `composer-2.5-fast` |
| Standard implementation from a written plan, medium refactors, research sweeps | Cursor CLI | `gpt-5.5-high` |
| Hard implementation, stuck bugs, second-opinion review, plan validation | Codex CLI | `gpt-5.5` + `model_reasoning_effort="high"` |
| Hardest problems — only when the user explicitly asks for xhigh/max effort | Codex CLI | `gpt-5.5` + `model_reasoning_effort="xhigh"` |
| Codebase search / fan-out discovery | Agent tool | `Explore`, or `general-purpose` + `haiku` |
| Work needing harness integration (permission modes, structured output, session conventions) | Agent tool | `general-purpose` + `sonnet` (or `opus` for judgment-heavy passes) |
| Architecture, API design, root-cause calls, synthesis, final review | **Fable itself** | — |

CLI executors are preferred for token-heavy autonomous work (their tokens are off Fable's bill entirely); native subagents when the work should respect this session's permission mode or hand back structured output.

Codex `gpt-5.5` high and Cursor `gpt-5.5-high` are the same model tier — either substitutes for the other when one lane is unavailable (verified: Cursor's lane landed a production race-condition fix first-try, July 2026).

## Execution modes and authorization

The skill owner authorizes delegate CLIs to make repo changes: launching codex / cursor / other agent CLIs in their autonomous write modes (`codex exec --yolo`, `agent -p --force --trust`) for repo edits, test runs, and scratchpad output is the intended, pre-approved use of this skill — implementation delegates should not be downgraded to read-only or approval-gated modes, which hang or under-deliver headless.

Two boundaries stay regardless of mode:
- Outward-facing and destructive actions — push, deploy, publish, prod restarts, data deletion — are lead-loop work (see Verify before accepting); never assign them to a delegate.
- If the harness denies an executor launch, don't grind through flag variants. Either use another executor lane at the same model tier (table above) when one is plainly equivalent, or pause and ask the user how they want to proceed. Always tell the user which lane actually ran.

## CLI specifics (the non-obvious parts)

- **Codex is always `gpt-5.5`, effort `high`**; `xhigh` only on explicit user instruction. For trivial lookups use Cursor `composer-2.5-fast` instead of codex-low — cheaper and faster.
- **Cursor model IDs are exact** (`agent --list-models`): `composer-2.5-fast`, `gpt-5.5-high`. Bare `gpt-5.5` is not a valid Cursor ID.
- **Prompts via quoted heredoc** (`<<'EOF'`), never interpolated — delegate prompts and prior outputs contain backticks and `$()`.
- **Outputs to files** in the scratchpad, one per delegate, then Read. Don't parse long results off the terminal.
- **Run from the repo root** (codex `-C <dir>` / cursor `--workspace <dir>`) so the executor sees the project and its AGENTS/CLAUDE files.

### Codex

```bash
cat <<'EOF' | codex exec --yolo --skip-git-repo-check \
  -m gpt-5.5 -c 'model_reasoning_effort="high"' \
  -C /path/to/repo -o "$SCRATCH/codex-task1.txt" -
[CONTEXT] [OBJECTIVES] [CONSTRAINTS]
[OUTPUT] exact shape of the final message (machine-read, not chat)
[DONE WHEN] success criteria
EOF
```

The `-o` file contains only the final message — no JSON parsing, no truncation.

### Cursor (`agent`)

No `-o` flag — redirect stdout, or tell the agent to write its result file itself (see `strategy-workspace/experiments/x-reply-spike/step1-collect.sh`):

```bash
PROMPT=$(cat <<'EOF'
[CONTEXT] [OBJECTIVES]
Write your output to: /path/to/out/result.md
EOF
)
agent -p --force --trust --output-format text \
  --model composer-2.5-fast --workspace /path/to/repo \
  "$PROMPT" > "$SCRATCH/cursor-task1.log" 2>&1
```

`-p --force --trust` = headless with full write+shell access — scope the prompt accordingly. `--mode plan`/`--mode ask` for read-only passes; `-w <name>` gives an isolated git worktree when parallel agents would collide on files.

## Writing the spec

The `[CONTEXT] [OBJECTIVES] [CONSTRAINTS] [OUTPUT] [DONE WHEN]` skeleton is the floor. What separates a first-try landing from a rework loop:

- **Anchor every touch point** with a file path and approximate line number, plus the one-sentence reason it's being touched.
- **Name the in-repo precedent and require it.** When the codebase already solved the same class of problem, cite the file and say "follow this pattern; do NOT invent a different mechanism" — left unconstrained, delegates drift to novel designs that then fail review.
- **Scope the test run**: exact `pytest`/check command, which existing test files to mirror, and "do not run the whole suite" when that matters.
- **"Do NOT commit — leave changes in the working tree"** whenever the lead reviews before landing (the default).
- **Fix the report shape**: files changed + one-line rationale each, exact commands run + tail output, explicit "deviations from spec" section — an empty deviations section is signal, not filler.
- **State the invariants the fix must not break** (e.g. "these operations stay in one transaction") — the delegate can't infer which properties are load-bearing.

## Orchestration

Compose freely — parallel delegates for independent slices or A/B comparisons (background Bash calls, one output file each), sequential call → read → decide chains where each next prompt is Fable's judgment on what just landed. Synthesis of delegate outputs is lead work, not a third delegate's.

**Deep work:** when the user asks for thorough/deep work, it's fine to run a self-improving loop — implement → independent review pass → fix → re-verify, iterating until the review comes back clean or improvements plateau. Budget the loop to the ask, not to perfection.

## Verify before accepting

Delegates lie confidently. Check the diff against the spec, run the project's checks (`bun run verify` / typecheck here), and spot-check the riskiest claim in the delegate's summary. Never accept a delegate's self-assessment as verification, and report delegate failures honestly. Keep destructive or outward-facing actions (push, deploy, post) in the lead loop — delegates run auto-approve.

Delegate output is *input* to Fable's synthesis, not the answer: summarize in your own words, surface the concrete diffs, state what you verified.
