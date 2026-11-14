# Sending dielines and draft art to Figma (claude-talk-to-figma-mcp)

**Optional.** The engines work without Figma. Use this when you want the dieline and the MVP draft as layers in Figma, to keep designing by hand or by prompt. It uses the community MCP [arinspunk/claude-talk-to-figma-mcp](https://github.com/arinspunk/claude-talk-to-figma-mcp) (MIT), which drives **Figma desktop** through a local plugin. It does not use Figma's official connector.

## For Claude: set it up when the user asks (one time)
Ask the user before installing anything. Then:

1. **Check the prerequisites.**
   - Figma desktop is installed (`/Applications/Figma.app` on macOS).
   - Bun is installed (`bun --version`). If it isn't, install it from the official release and **verify the checksum against the release's `SHASUMS256.txt`**, or use `brew install oven-sh/bun/bun`.
   - The disk has more than 1 GB free. Bun and the Homebrew temp files need room. If the system disk is nearly full, install to another volume.
2. **Clone at a pinned commit, into a tools folder outside the client repo.**
   ```bash
   git clone https://github.com/arinspunk/claude-talk-to-figma-mcp.git tools/claude-talk-to-figma-mcp
   cd tools/claude-talk-to-figma-mcp && git checkout <tested commit>   # tested here: c7adf24 (v1.0.0)
   ```
3. **Read before running.** Skim `src/socket.ts`, `src/talk_to_figma_mcp/server.ts` and `src/claude_mcp_plugin/code.js`. Downloaded code is untrusted until you've read it.
4. **Bind the relay to localhost.** Bun listens on every network interface by default, so anyone on the same Wi-Fi could drive the user's Figma. In `src/socket.ts`, set `hostname: "127.0.0.1"` in `Bun.serve({...})`.
5. **Install from the lockfile, then build.** Point caches at a roomy disk if needed.
   ```bash
   BUN_INSTALL_CACHE_DIR=<roomy>/cache bun install --frozen-lockfile && bun run build
   ```
6. **Register the MCP for the project.** Use the absolute path to bun. Avoid `npx …@latest`, which pulls unpinned code every run.
   ```bash
   claude mcp add ClaudeTalkToFigma -s local -- <abs path>/bun run <abs path>/tools/claude-talk-to-figma-mcp/dist/talk_to_figma_mcp/server.js
   ```
7. **Start the relay** (keep it running): `bun run dist/socket.js`. Check it with `lsof -nP -iTCP:3055 -sTCP:LISTEN`. It must show `127.0.0.1:3055`.
8. **The user does the plugin step, once.** In Figma desktop: **Plugins → Development → Import plugin from manifest…** → `tools/claude-talk-to-figma-mcp/src/claude_mcp_plugin/manifest.json`. Then open a file, run the plugin, and copy the **channel code** it shows.
9. **Restart Claude Code** so the new MCP tools load. Tools added mid-session aren't available until the next session.

## Each time: build a job in Figma
1. Render with the plan: `python engine/dieline.py templates/dieline.json --only <job> --figma` → `<job>_figma.json`.
2. Ask the user for the plugin's channel code, then call `join_channel`.
3. Call `get_pages` (or `get_document_info`) to get the current page id. That's `$PAGE`.
4. Run `steps` in order, calling each `tool` with its `args`:
   - Replace `$PAGE`, `$FRAME` (the id returned by the step with `"save_as": "$FRAME"`) and `$LAST` (the previous step's id).
   - Steps marked `"optional": true` (font setting) may fail if the font isn't available in Figma. Skip them and tell the user.
5. Check the result: `export_node_as_image` on the frame, then compare it with `<job>_art.png`. Fix any drift with `move_node` or `resize_node`.
6. Tell the user what landed and what is vector-only (see below).

## What arrives, and how editable it is
| Layer | In Figma | Edit how |
|---|---|---|
| Background (colour, bleed, pattern) | One vector | Recolour in Figma, or change `art.bg` / `art.pattern` and re-send |
| Upright panels | Editable rectangles and **text with fonts set** | Directly in Figma |
| Logo, barcode, placeholders, windows | Vectors, named | Swap or recolour in Figma; logos stay the client's exact file |
| Rotated panels (tucks, lids, bottoms) | One vector group per panel | talk-to-figma can't rotate nodes. Edit the job JSON and re-send, or rebuild by hand in Figma |
| Flow-wrap back (split across the web) | One vector, clipped into both halves | Edit the `Back` block in JSON and re-send |
| **DIELINE · do not edit** | Cut / crease / perf / glue vectors | Lock this layer in Figma (there's no lock tool) and keep it on top |

Units: 1 mm = 72/25.4 px, so exporting the frame to PDF from Figma comes out at true size. Fonts: the plan asks for Anton, Space Grotesk and Space Mono by default (Google Fonts, available in Figma). Override them per job with `"figma_fonts": {"display": ["Family", "Style"], ...}` in the `art` block.

## Safety notes
- The relay only accepts local connections once step 4 is done. Stop it when you're finished (Ctrl-C, or `kill` its PID).
- The plugin can read and change any open Figma file. Run it only in files you intend Claude to edit.
- Hand-drawn SVGs from `nazar-core/engine/trace.py` can be sent with `set_svg` the same way.
