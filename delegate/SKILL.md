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
| Bulk/repetitive edits, file generation from a clear spec, boilerplate | Grok CLI | `grok-4.7 --effort medium` |
| Backend logic, agentic operations, research sweeps, system-level changes, stuck bugs, second-opinion review, plan validation | Codex CLI | `gpt-6.1-sol` + `model_reasoning_effort="high"` |
| Frontend HTML/CSS/React/design-engineer work (UI, components, styling, layout) | Cursor CLI | `claude-opus-5-5-high` (Opus 5.5 1M, high effort) — **never GPT models** |
| Hardest problems — only when the user explicitly asks for xhigh effort | Codex CLI | `gpt-6.1-sol` + `model_reasoning_effort="xhigh"` |
| Codebase search / fan-out discovery | Agent tool | `Explore`, or `general-purpose` + `haiku` (Haiku 4.5) |
| Work needing harness integration (permission modes, structured output, session conventions) | Agent tool | `general-purpose` + `sonnet` (Sonnet 5.5), or `opus` (Opus 5.5) for judgment-heavy passes |
| Architecture, API design, root-cause calls, synthesis, final review | **Fable itself** | — |

CLI executors are preferred for token-heavy autonomous work (their tokens are off Fable's bill entirely); native subagents when the work should respect this session's permission mode or hand back structured output.

The only GPT model in this skill is Codex `gpt-6.1-sol` (verified on codex-cli 0.159.2 with a ChatGPT login, 30 Sep 2026). Do not send GPT work to `cursor-agent`. Cursor is the Opus frontend lane only.

**GPT scope limits (hard rules):**
- **No GPT models for frontend UI/UX** (components, styling, layout, design). Frontend *API-layer* work is fine — e.g. Next.js route handlers/server code.
- **No GPT models for human-facing docs or publication writing.** Internal technical docs and research artifacts for internal use are fine.
- **No `cursor-agent --model gpt-*`.** If a task needs a GPT model, run Codex `gpt-6.1-sol`. If it needs Cursor, the model is `claude-opus-5-5-high`.
- Route frontend and publication writing to the Opus/Claude lanes instead.

## Execution modes and authorization

The skill owner **explicitly authorizes fully autonomous write mode** for delegate CLIs. Launching codex / cursor / other agent CLIs in their write modes (`~/.local/bin/codex exec --dangerously-bypass-approvals-and-sandbox`, `cursor-agent -p --yolo --trust`, `grok -p … --always-approve`) for repo edits, test runs, and scratchpad output is the intended, pre-approved use of this skill. Codex 0.159.2 has no `--yolo` flag; that name is Cursor's alias for `--force`. Auto-approve every tool call, edit, and shell command without prompting; use it (not approval-gated modes) for all implementation delegates. Give delegated agents **sufficient autonomy to finish the job end to end**: to read/write files, run builds/tests/linters, install deps, and iterate on their own until the spec's DONE-WHEN criteria are met — a delegate that stops to ask permission mid-run hangs headless and under-delivers. Do NOT downgrade implementation delegates to read-only (`--mode plan`/`--mode ask`) or approval-gated modes.

Three boundaries stay regardless of mode:
- Outward-facing and destructive actions — push, deploy, publish, prod restarts, data deletion — are lead-loop work (see Verify before accepting); never assign them to a delegate.
- **Shared live datastores are lead-loop territory.** A delegate writing code that touches a live DB will test-run it against that DB no matter what the prompt says (observed: a delegate test-ran a dev ingester against production, July 2026). Structure the lane so the delegate ships code/drafts only and the LEAD executes the first run — and snapshot the datastore (row counts at minimum, a dump when cheap) before launching any delegate whose task touches mutation code. For cleanup, prefer re-running the owning idempotent source over surgical DELETEs — a `LIKE`-pattern delete once over-matched rows legitimately owned by another source.
- If the harness denies an executor launch, don't grind through flag variants. Use another executor from the table only when it is the lane for that task (Grok for mechanical work, Cursor Opus for frontend). Do not fall back to `cursor-agent` with a GPT model. Otherwise pause and ask the user how they want to proceed. Always tell the user which lane actually ran.

## CLI specifics (the non-obvious parts)

- **Invoke Codex as `~/.local/bin/codex`.** That symlink tracks the current standalone install. Do not use an unqualified `codex` when a stale binary is earlier on `PATH`. `gpt-6.1-sol` needs codex-cli 0.159.2 or newer; 0.158 returns `400 The 'gpt-6.1-sol' model is not supported when using Codex with a ChatGPT account.` Fix with `codex update`.
- **Codex model is `gpt-6.1-sol`, effort `high`.** `xhigh` only when the user explicitly asks for it. For trivial lookups and bulk mechanical work, use Grok `grok-4.7 --effort medium` instead of a low-effort GPT lane.
- **Do not pass GPT model IDs to `cursor-agent`.** The only Cursor model in this skill is `claude-opus-5-5-high` (Opus 5.5 1M, high effort). Bare `opus-5-5` is not a valid Cursor ID — effort is baked into the suffix. Parameterized form also works: `'claude-opus-5-5[context=1m,effort=high,fast=false]'`.
- **Grok CLI uses `grok-4.7 --effort medium` for bulk/repetitive edits, boilerplate, file generation from a clear spec, and trivial lookups.** Full contract: `~/tokenized-equity-watch/docs/grok-cli.md`.
- **Prompts via quoted heredoc** (`<<'EOF'`), never interpolated — delegate prompts and prior outputs contain backticks and `$()`.
- **Outputs to files** in the scratchpad, one per delegate, then Read. Don't parse long results off the terminal.
- **Run from the repo root** (codex `-C <dir>` / cursor `--workspace <dir>` / grok `--cwd <dir>`) so the executor sees the project and its AGENTS/CLAUDE files.

### Codex

```bash
cat <<'EOF' | ~/.local/bin/codex exec --dangerously-bypass-approvals-and-sandbox --skip-git-repo-check \
  -m gpt-6.1-sol -c 'model_reasoning_effort="high"' \
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
MODEL="${MODEL:-claude-opus-5-5-high}"
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

`-p --yolo --trust` = headless with full write+shell access, every action auto-approved (`--yolo` is the alias for `--force`) — scope the prompt accordingly and let the delegate run to completion without prompting. `--model` must be `claude-opus-5-5-high` (or another non-GPT Cursor ID the user named). Do not pass `gpt-*`. `--mode plan`/`--mode ask` for read-only passes only; `-w <name>` gives an isolated git worktree when parallel agents would collide on files.

### Grok CLI (`grok`)

Use Grok 4.7 for bulk/repetitive edits, file generation from a clear spec, boilerplate, and trivial lookups. Use the same file-write contract as Cursor (put `OUT` in the prompt; ignore stdout for the deliverable). Binary: `~/.local/bin/grok`. No `--trust` flag; YOLO is `--always-approve`.

```bash
#!/usr/bin/env bash
# Delegate a bulk, repetitive, or mechanical task via Grok CLI.
set -euo pipefail

REPO="${REPO:-$PWD}"
OUT="${OUT:-$REPO/out/result.md}"
MODEL="${MODEL:-grok-4.7}"
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

Standard Grok invocation: `grok -p … -m grok-4.7 --effort medium --always-approve --cwd "$REPO" --output-format plain --no-memory`.

## Image generation

Two lanes. Do not mix them, and do not describe a built-in image as Image 2.5.

### Simple visualization and prototypes — built-in Image 2

Use the Codex built-in `image_gen` tool. It runs on the ChatGPT login. It does not need `OPENAI_API_KEY`. The tool hardcodes `gpt-image-2`. Its only arguments are `prompt`, `transparent_background`, `referenced_image_paths`, and `num_last_images_to_include`. There is no model, quality, or size argument.

The ChatGPT images proxy ignores `model`, `quality`, and `size` on `https://chatgpt.com/backend-api/codex/images/generations` (verified 30 Sep 2026: an unknown model id still returned 200, and a `quality=high` / `size=1024x1024` request came back `quality=low`, `1254x1254`). Use this lane for sketches, prototypes, and simple visualization. Do not use it when the deliverable is a production asset.

Codex saves under `$CODEX_HOME/generated_images/<thread-id>/`. Copy the chosen PNG into the workspace before finishing. Do not leave a project-referenced asset only under `$CODEX_HOME`.

```bash
cat <<'EOF' | ~/.local/bin/codex exec --dangerously-bypass-approvals-and-sandbox \
  --skip-git-repo-check --ephemeral \
  -m gpt-6.1-sol -c 'model_reasoning_effort="low"' \
  -C /path/to/repo -o "$SCRATCH/imagegen-last.txt" -
Use the built-in image_gen tool exactly once. Do not call the Image API.
Prompt: <one concrete visual>
Copy the PNG to: /path/to/repo/output/imagegen/<name>.png
Report the source path, destination path, and byte size.
EOF
```

`-m gpt-6.1-sol` is the agent that calls the tool. It is not the image model. The image model is `gpt-image-2`.

### Production — `gpt-image-2.5-sunburst` with the paid API key

Use this when the image is a final asset. `gpt-image-2.5-sunburst` is selected only by the Image API, with `OPENAI_API_KEY` from the repo `.env` (mode `600`, listed in `.gitignore`). Never print the key, never commit `.env`, and never paste the key into a prompt. The ChatGPT access token cannot call this: `api.openai.com` returns 401 missing scope `api.model.images.request`.

Text-only generation uses `generate`:

```bash
set -a
source /path/to/repo/.env
set +a
uv run --with openai python ~/.codex/skills/.system/imagegen/scripts/image_gen.py generate \
  --model gpt-image-2.5-sunburst \
  --prompt "<prompt>" \
  --quality high \
  --size 1024x1024 \
  --no-augment \
  --out output/imagegen/<name>.png
```

Script limits, from `~/.codex/skills/.system/imagegen/scripts/image_gen.py`:

- `--model` must start with `gpt-image-`. Omitting it defaults to `gpt-image-2`, which is the prototype lane, not production.
- `--quality` is only `low`, `medium`, `high`, or `auto`. The 2.5 API also accepts `xhigh` and `max`; this script rejects them before the request. Do not edit the script to add them.
- For any model other than the exact string `gpt-image-2`, `--size` is only `1024x1024`, `1536x1024`, `1024x1536`, or `auto`.
- Do not modify `scripts/image_gen.py`.

Verified 30 Sep 2026, same prompt, `--quality high --size 1024x1024`: Sunburst (28.5s) looked like a photographed surface; `gpt-image-2` via the same API (85.4s) looked smoother and more synthetic. One sample. Use Sunburst for production.

### Attaching reference images

Both lanes accept multiple reference images. `generate` does not take images. If the task has input files, use built-in `referenced_image_paths` or the API `edit` subcommand.

Number every file in the prompt and give it one role: tree silhouette, wood swatch, dirt tile, edit target. Order in the prompt must match the path order. Cap the built-in list at 5. Pass either `referenced_image_paths` or `num_last_images_to_include`, not both.

Built-in prototype. One `image_gen` call. Absolute paths. Do not call the Image API.

```bash
cat <<'EOF' | ~/.local/bin/codex exec --dangerously-bypass-approvals-and-sandbox \
  --skip-git-repo-check --ephemeral \
  -m gpt-6.1-sol -c 'model_reasoning_effort="low"' \
  -C /path/to/repo -o "$SCRATCH/imagegen-refs.txt" -
Use the built-in image_gen tool exactly once.
Pass these files together in referenced_image_paths, in this order:
1. /abs/tree.png — tree silhouette, leaf color, trunk color
2. /abs/wood.png — wood material swatch
3. /abs/dirt.png — repeating ground tile
Prompt: Pixel-art side view. One tree from image 1, trunk colored like image 2, ground tiled from image 3. Crisp pixels, no text.
If this is a tileset, require a sheet with one cell per tile and say which reference locks which cell. A scene prompt returns one scene, not a tile grid.
Copy the PNG to: /path/to/repo/output/imagegen/<name>.png
EOF
```

Production. `edit`, repeated `--image`, same order as the prompt. Do not pass `--input-fidelity`. `gpt-image-2` rejects it, and Sunburst should leave it unset.

```bash
set -a
source /path/to/repo/.env
set +a
uv run --with openai python ~/.codex/skills/.system/imagegen/scripts/image_gen.py edit \
  --model gpt-image-2.5-sunburst \
  --image /abs/tree.png \
  --image /abs/wood.png \
  --image /abs/dirt.png \
  --prompt "Image 1 is the tree. Image 2 is the wood color. Image 3 is the repeating dirt tile." \
  --quality high \
  --size 1024x1536 \
  --no-augment \
  --out output/imagegen/<name>.png
```

Verified 30 Sep 2026 with `Tree (Forest).png`, `Wood.png`, and `starter-tiles-16px/dirt-xxxx.png`. Built-in `referenced_image_paths` was accepted and wrote a 1024×1536 pixel tree on a dirt row (`pixel-forest-builtin.png`). The same three files through Sunburst `edit` finished in 27.9s (`pixel-forest-sunburst.png`) and stayed closer to the source sprite. Both invented a grass cap that is not in the dirt tile. Neither emitted a 16×16 tile grid, because the prompt asked for a scene.

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
