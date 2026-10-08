---
name: gpt-image
description: Create or edit images with OpenAI's paid image model gpt-image-2.5-sunburst at high quality from text and up to 16 input images. Use for one-off images and edits - change part of a picture, combine several pictures, copy the style of a reference, put objects from images A and B into image C, cut an object out onto a transparent background, portraits, banners, cards and illustrations.
---

# GPT Image 2.5 Sunburst

One script, `image.sh`, sends a prompt and optional input images to `gpt-image-2.5-sunburst` at `high` quality and saves the result. Every call takes about 30 seconds and is billed. With `--image` it calls the edits endpoint; without, it generates from text. It uses `OPENAI_API_KEY` from the environment, or from `.env` in the current directory. Never print the key or put it in a prompt.

`S` is this skill's `scripts` folder, e.g. `S=~/.claude/skills/gpt-image/scripts`. Put results in a folder that is not committed, e.g. `output/`.

```bash
$S/image.sh --prompt "..." --out output/images/<name>.png                       # text only
$S/image.sh --image a.png --image b.png --prompt "..." --out output/images/<name>.png   # with inputs
```

Each run also writes `<name>.json` next to the image with the prompt, inputs, settings, seconds taken and token usage. Keep it: it is how you redo or tweak a result later.

## Settings

| Flag | Values | Default |
|---|---|---|
| `--size` | `auto`, `1024x1024`, `1536x1024`, `1024x1536`, or any `WxH` with both sides multiples of 16, ratio at most 3:1, longest side at most 3840, total pixels 655,360 to 8,294,400 | `auto` |
| `--background` | `transparent`, `opaque`, `auto` | unset |
| `--format` | `png`, `webp`, `jpeg` | `png` |
| `--n` | number of variants of the same prompt; files get `-1`, `-2`... | 1 |
| `--mask` | PNG with an alpha channel, same size as the first `--image`; transparent pixels may change | unset |
| `--prompt-file` | read a long prompt from a file instead of `--prompt` | |

- `--background transparent` gives a real alpha channel on 2.5. Do not ask for "a transparent background" in words only; the model then draws a checkerboard.
- Input images: PNG, JPEG or WebP, under 50 MB each, up to 16 per call. Convert GIFs to PNG first. Every extra input adds cost.
- Do not pass `input_fidelity`; 2.5 always reads inputs at full detail.

## Writing the prompt

1. **Number every input and give it one job.** "Image 1 is the edit target. Image 2 is a straw hat. Image 3 is a style reference only." The order in the prompt must match the order of `--image` flags. Put the main picture (the one being edited, or the one whose layout wins) first.
2. **Say what not to take from a reference.** A style reference otherwise leaks its objects, colours and layout: "use image 3 for palette and pixel style only; do not copy its objects".
3. **Say which input wins when they disagree.** "If image 2 and image 3 disagree on colour, follow image 2."
4. **Name the change, then list what stays.** "Change only the sky to sunset. Keep the house, the creatures, the framing and the lighting on the ground unchanged." Vague words like "make it nicer" give the model permission to redraw everything.
5. **For an inserted object, say how it sits in the scene**: where, how big relative to something already there, what it rests on, and that light and shadow match the scene.
6. **List what must not appear**: text, labels, extra objects, borders, drop shadows, watermarks.
7. **Quote exact text** if the image must contain words, and say font style and placement. Short text only; add long or exact text afterwards with code.
8. **Describe the object, its main colour and the view angle** for small or unusual objects; otherwise the model swaps them for something more common.

When pictures must match an existing look, pass one of the project's finished images as a style reference every time.

## Recipes

**Change part of an image**
```bash
$S/image.sh --image target.png --prompt "Image 1 is the edit target. Change only <X> to <Y>. Keep everything else unchanged: <list>." --out ...
```
If the change must stay inside a region, add a mask. `mask.py` makes one from boxes in pixel coordinates (left,top,right,bottom) of the target:
```bash
uv run --with pillow python $S/mask.py target.png output/images/mask.png 200,0,824,420
$S/image.sh --image target.png --mask output/images/mask.png --prompt "..." --out ...
```
The mask guides the model but is not a hard boundary; pixels outside it can still shift slightly. When a region must stay pixel-identical, paste the changed region back over the original with Pillow afterwards.

**Put objects from A and B into C**
```bash
$S/image.sh --image C.png --image A.png --image B.png --prompt "Image 1 is the scene to edit. Image 2 shows a lantern, image 3 a wooden bench. Place the lantern from image 2 on the left of the porch and the bench from image 3 under the window, each at the scale of the door in image 1, standing on the floor, lit like the rest of image 1, redrawn in image 1's style. Change nothing else in image 1." --out ...
```
If the inserted object looks pasted on, add more about scale, contact with the ground and light direction rather than more adjectives.

**Copy a style onto new content**
```bash
$S/image.sh --image style.png --prompt "Image 1 is a style reference only: copy its palette, outlines, shading and pixel size; do not copy its objects or layout. Draw <subject>, <view angle>, <composition>. No text." --out ...
```

**Redraw an image in another style**: image 1 is the content to keep (shapes, layout, identity), image 2 is the style. Say "keep every object of image 1 in the same place and proportions; take only the look from image 2".

**Combine several pictures into a new one**: list each input's role, then describe the new picture as a whole (scene, framing, who is where). Without a scene description the model lays the inputs side by side.

**Cut an object out**
```bash
$S/image.sh --image photo.png --background transparent --prompt "Image 1 contains a <object>. Return only the <object>, unchanged, on a transparent background. No shadow, no outline, no halo." --out output/images/<name>.png
```
A transparent PNG flattened onto black shows its soft edges as a dark halo. To feed a cut-out into another edit, either pass the PNG with its transparency or flatten it onto a plain light colour.

**Several variants**: `--n 3` for different takes on one prompt. Different objects need separate runs, not `--n`.

## Working in steps

- One change per call. For "change the hat, then make it night", run the hat edit, check it, then pass the approved output into the night edit.
- Repeat the "keep unchanged" list on every step; the model forgets it between calls and details drift.
- Save each accepted step under a new name (`room-1.png`, `room-2.png`). If a step damages something, go back to the last good file instead of trying to repair the damage.
- Edits several in a row slowly change the whole picture (colours shift, details soften). Compare the latest file with the first one side by side every few steps.

## Checking the result

Look at every output yourself (Read the PNG) before showing it:

- The requested change is complete, and nothing else changed: faces, eyes, shapes, layout, text.
- No extra objects, text, borders or drawn checkerboards.
- Inserted objects are the right size, touch the ground, and their light matches the scene.
- Transparency is real if asked for (the file mode is RGBA and the background alpha is 0).
