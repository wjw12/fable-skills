---
name: slop-free-frontend
description: Anti-slop guardrails for frontend design. Use ONLY when the user explicitly wants to avoid generic AI aesthetics — e.g. asks for a design that doesn't "look AI-generated"/"generic"/"like a template", to "remove the slop"/"de-slop"/"make it distinctive", or to review UI specifically for AI-slop tells. Do NOT auto-trigger on ordinary frontend or UI work (building a page, styling a component, fixing CSS) that doesn't mention slop or AI-generic concerns. Covers color, typography, spacing, layout, motion, imagery, and UX copy.
---

# Slop-Free Frontend

Generic AI aesthetics are a failure mode, not a default. This skill has three entry points — pick by phase, and read the shared **Register** section first in every case:

- **DESIGN** — about to make greenfield visual choices (palette, fonts, layout direction)
- **IMPLEMENT** — writing HTML/CSS/JSX right now
- **REVIEW** — auditing an existing surface for slop tells

Rules here are positive-first: reach for the stated default at write-time; scan for the named tell at review-time. A wall of "never X" primes X.

## Register: two kinds of surface, two slop tests

Decide which register the surface is in before applying any rule. Getting this wrong makes the rules backfire.

**Brand register** — design IS the product: landing pages, marketing, campaign pages, portfolios, long-form editorial. The slop test is *distinctiveness*: if a viewer could say "AI made that" without hesitation, it failed. Safe = invisible. Bold color strategies, expressive type, and asymmetric layout are permissions here.

**Product register** — design SERVES the product: app UI, dashboards, admin, settings, tools. The slop test is *earned familiarity*: would a user fluent in Linear/Figma/Stripe-quality tools trust this, or pause at every subtly-off component? Familiarity is a feature. System fonts, Inter, standard nav patterns, and restrained color are legitimate here — the failure mode is strangeness without purpose (display fonts in labels, decorative motion, invented affordances), not plainness.

**Identity preservation overrides everything below.** If the project already has committed brand fonts, colors, or an established lane, match them — the reflex-reject lists apply to *new greenfield choices*, never to an existing identity. Read the project's tokens/theme/components before inventing anything.

---

## DESIGN phase — before any code

Skipping this phase is how slop happens: with no committed direction, output regresses to the training-data mean.

**1. Write the scene sentence.** One sentence of physical scene: who uses this, where, under what ambient light, in what mood. Dark vs light, density, and tone should fall out of it. If they don't, the sentence isn't concrete enough — add detail until it forces the answer. Never dark "because tools look cool dark", never light "to be safe".

**2. Run the category-reflex check, both orders.**
- *First-order:* if someone could guess your theme + palette from the product category alone ("fintech → navy and gold", "AI tool → dark with glow"), it's the first training-data reflex. Rework until the domain doesn't predict the design.
- *Second-order:* if someone could guess it from category-plus-anti-reference ("AI tool that's *not* SaaS-cream → editorial serif + mono labels + ruled columns", "fintech that's not navy → terminal-dark"), that's the trap one tier deeper. The currently saturated second-order lane is **editorial-typographic**: display serif (often italic) + small mono labels + ruled separators + monochrome restraint. Avoid landing there by reflex too.

**3. Pick a color strategy before picking colors** (brand register mostly; product defaults to Restrained):
- **Restrained** — tinted neutrals + one accent ≤10% of surface. Product default.
- **Committed** — one saturated color carries 30–60%. Identity-driven brand pages.
- **Full palette** — 3–4 named roles used deliberately. Campaigns, data viz.
- **Drenched** — the surface IS the color. Brand heroes.

Name a real-world reference for the strategy ("Stripe purple-on-white restraint", "Klim orange drench") — unnamed ambition becomes beige. Then compose in OKLCH: hold chroma+hue, vary lightness for shades; reduce chroma near white/black. Don't reach for blue (hue ~250) or warm orange (~60) by reflex — those are the two dominant AI defaults.

**4. Select fonts by procedure, not reflex** (greenfield only):
1. Write three concrete, physical brand-voice words — "warm, mechanical, opinionated", not "modern and clean".
2. Note the fonts you'd reach for instinctively. If any are on the reflex-reject list, discard them: **Fraunces · Playfair Display · Cormorant · Lora · Crimson (all) · Newsreader · Space Grotesk · Space Mono · IBM Plex (all) · Syne · Inter · DM Sans · DM Serif · Outfit · Plus Jakarta Sans · Instrument Sans/Serif**. (Product UI is exempt: Inter/system-ui are fine where design serves the product.)
3. Browse a real catalog (Google Fonts, Pangram Pangram, Klim, ABC Dinamo, Future Fonts) with the three words in mind. Find the brand as a *physical object* — a museum caption, a 1970s terminal manual, a concert poster. Reject the first thing that "looks designy".
4. Anti-reflex cross-check: technical ≠ needs a serif for warmth; premium ≠ the expressive serif everyone uses; children's ≠ rounded display; "modern" ≠ geometric sans. If the final pick matches your step-2 instinct, look again.

**5. Commit the direction in writing** — a short comment block at the top of the main file: three adjectives, type choices, palette + strategy, density, radius/shadow stance, motion stance. Vague directions ("modern, clean") produce generic output; every value thereafter traces to this block. Build one small surface (hero, card, button group) with it and check it reads as the three adjectives before going wide.

**6. If asked for variations: variety must be designed, not hoped for.** There is no temperature knob — unspecified variations converge on one default look. Spec each variation before building: distinct palette family, distinct type pairing, distinct layout skeleton, written down. Order them safe → bold, make at least one genuinely off-distribution, and make every pair differ on something you can state in one sentence.

---

## IMPLEMENT phase — defaults while writing code

### Color
- Every value traces to a token or the committed palette. Five slightly-different blues in one file means colors were invented inline — consolidate.
- Tone whites and blacks toward the palette (`#FAFAFA`/`#1A1A1A` scale, or brand-hued). Pure `#FFF` on `#000` reads unfinished.
- Tinted neutrals: add 0.005–0.015 chroma toward *this brand's* hue — not warm-by-default (that's the cream monoculture), not cool-by-default.
- Body text contrast ≥4.5:1, large text ≥3:1, UI components ≥3:1. The most common AI-design failure is muted-gray body text on tinted near-white "for elegance" — when in doubt, darken toward the ink end.
- Gray text on a colored background looks washed out: use a darker shade of the background's own hue, or alpha of the text color.
- Never color alone for state — pair with icon, text, or position.
- Dark mode is not inverted light mode: depth via lighter surfaces (3-step lightness scale), slightly desaturated accents, body weight down a notch (light-on-dark reads heavier).

### Typography
- 1–2 families. Pair on a contrast axis (serif+sans, geometric+humanist) or use one family in weights — never two similar-but-not-identical sans.
- Commit to a scale. Brand/marketing: fluid `clamp()` headings, ratio ≥1.25, clamp max ≤6rem — above ~96px the page is shouting. Product: fixed rem scale, ratio 1.125–1.2; no fluid type in app UI.
- Body ≥16px, line length 45–75ch (`max-width: 65ch`), line-height ~1.5 body / 1.1–1.2 headings. `text-wrap: balance` on h1–h3, `text-wrap: pretty` on prose.
- Letter-spacing floor for display type: ≥ −0.04em (tighter = cramped, a known tell). All-caps labels need +0.05–0.12em and stay short — never all-caps body copy.
- `tabular-nums` for data tables; rem not px for font sizes; never disable zoom.

### Spacing & layout
- All spacing on a 4px-base scale; tokens, not `padding: 17px`. Rhythm comes from *varying* it: tight within groups (8–12px), generous between sections (48–96px). Uniform spacing everywhere is monotony — a tell in itself.
- Cards are the lazy answer — use them only when content is truly distinct and actionable. Spacing and alignment group things fine without boxes. **Nested cards are always wrong.**
- Flexbox for 1D, Grid for 2D; `repeat(auto-fit, minmax(280px, 1fr))` for breakpoint-free grids; container queries for components.
- Semantic z-index scale (dropdown → sticky → backdrop → modal → toast → tooltip); never 999/9999.
- Hierarchy: combine 2–3 signals (size ≥3:1 ratio, weight bold-vs-regular, space) — squint test: primary element still obvious when blurred.
- Touch targets ≥44×44px (expand hit area with a pseudo-element if the visual is smaller).

### Motion
- Purposeful, part of the build — but state-conveying in product UI (150–250ms, no page-load choreography), and orchestrated-once rather than scattered in brand surfaces.
- Ease-out exponential curves (quart/quint/expo). No bounce, no elastic.
- Animate transform/opacity (blur/clip-path/mask when they earn it), never layout properties.
- The scroll-reveal tell is the *uniform reflex* — one identical fade-up applied to every section — not motion itself. Each reveal should fit what it reveals; zero motion everywhere is also a failure.
- Reveal animations must enhance an already-visible default — never gate content visibility on a class-triggered transition (hidden tabs and headless renderers ship the section blank).
- `prefers-reduced-motion` alternative for every animation: crossfade or instant.

### Imagery
- When the brief implies imagery (restaurant, hotel, travel, product, portfolio), ship imagery — zero images is a bug, not restraint. Search for the brand's physical object ("handmade pasta on a scratched wooden table"), not the category ("Italian food"). One decisive photo beats five mediocre ones.
- Verify stock URLs actually resolve before shipping; a broken image is worse than fewer images.
- No asset yet? Use an honest placeholder — striped background + monospace label (`product shot 1200×800`) — never a weak hand-drawn SVG illustration pretending to be final.
- Icons from an established set (Phosphor, Lucide, Heroicons, Material); consistent style throughout.
- Emoji only when functional (real status/category) or the brand already uses them. No 🚀 for visual color.

### UX copy
- Specific verbs and nouns that say what the product literally does. Marketing buzzwords are instant tells: streamline, empower, supercharge, unleash, world-class, enterprise-grade, next-generation, cutting-edge.
- AI cadence tells: >2 em-dashes in body copy; three-plus sections ending on a manufactured-contrast aphorism ("Not a feature. A platform." / "X. No Y." / "X. Just Y."); "X theater" framing. Once is voice; a pattern is grammar.
- Error messages specific and field-adjacent ("Email address is invalid", not "Invalid"). Real copy, never lorem in anything hi-fi.

### Interaction completeness (product surfaces)
- Every interactive element: default / hover / active / focus-visible / disabled, plus loading for async. Hover ≠ opacity-fade (looks disabled). Focus ring 2px + 2px offset, ≥3:1 contrast — `outline: none` without replacement never ships.
- Skeletons over spinners; empty states that teach; disabled buttons that explain why; double-submit prevented; Escape closes modals; dropdowns escape `overflow:hidden` ancestors (popover API / `position: fixed` / portal).

---

## REVIEW phase — the tell checklist

Walk the surface against every group. **Report everything you find, including uncertain and low-severity hits, each with confidence and severity** — coverage first, filtering after; silently dropping "minor" findings lowers recall. Then fix directly, noting judgment calls. A finding that traces to the project's committed design system is a false positive — skip it, say so.

### Structural tells (near-certain slop; rewrite the element)
- **Side-stripe accent** — `border-left`/`right` >1px as colored accent on cards/callouts. Full hairline border, background tint, or leading icon instead.
- **Gradient text** — `background-clip: text` over a gradient. Solid color; emphasis via weight/size.
- **Icon-tile stack** — small rounded-square icon container above a heading, repeated per card: the universal AI feature-card template. Icon beside heading, or no container.
- **Hero eyebrow / pill chip** — tiny uppercase tracked label (or pill) above an oversized headline; and its sibling, **kickers on every section** ("ABOUT / PROCESS / PRICING"). One named kicker can be voice; per-section grammar is scaffolding.
- **Numbered section markers** — 01/02/03 as decoration. Numbers earn their place only when order carries real information.
- **Hero-metric template** — big number + small label + stat row + gradient accent, with decorative numbers.
- **Identical card grids** — same icon+heading+text card repeated endlessly; nested cards anywhere.
- **Glassmorphism as default** — decorative blur/glass everywhere.
- **Thin border + wide diffuse shadow** on the same element — commit to a defined edge or a soft elevation, not both.
- **Decorative grid-line background** (two-axis 1px linear-gradient mesh) and **repeating-gradient stripes** as surface texture.

### Palette tells
- **Purple/violet gradients, cyan-on-dark neon, dark-with-colored-glow** — the recognizable AI trio.
- **Cream/sand/beige body background** (OKLCH L 0.84–0.97, C <0.06, hue 40–100) reached silently — the current default "tasteful" AI surface. Token names are tells in themselves: `--paper`, `--cream`, `--sand`, `--bone`, `--linen`, `--parchment`, `--ivory`. Warmth belongs in accent + type + imagery, not body bg — unless the direction block explicitly committed to it.
- **The warm-editorial bundle** — cream bg + serif display (Playfair/Fraunces/Georgia) + italic word-accents + terracotta/amber. Any one element can be deliberate; all together on a dashboard/dev-tool/fintech surface is today's purple gradient.
- Untraceable inline colors; pure #FFF/#000; gray-on-color; contrast below WCAG (compute the ratios).

### Type tells
- Reflex-reject font as silent greenfield default (see DESIGN list; Inter in product UI is fine).
- Oversized italic serif hero; full-sentence headline at display size overflowing the fold; letter-spacing < −0.04em; flat scale (sizes <1.2:1 apart); all-caps body; justified text without hyphenation; skipped heading levels.
- Text overflowing its container at tablet/mobile widths — test the actual headline copy at breakpoints; the viewport is part of the design.

### Motion & interaction tells
- Uniform entrance animation on every section; bounce/elastic easing; layout-property transitions; content gated on reveal classes; missing `prefers-reduced-motion`; image scale-on-hover as default; missing hover/focus/disabled/loading states; `outline: none` bare.

### Copy tells
- Buzzword strings, em-dash density, aphoristic cadence, "X theater", lorem in finals, made-up stats ("99.9% uptime", "47% faster") supporting nothing.

### Verdict
Close with: findings by category (confidence/severity), fixes applied, false positives skipped and why, and open judgment calls for the user (font swap candidates, palette direction) — pick a defensible default yourself and note it rather than blocking on questions.
