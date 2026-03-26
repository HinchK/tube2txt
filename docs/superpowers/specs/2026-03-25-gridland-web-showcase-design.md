# Gridland Web Showcase -- Design Spec

**Date**: 2026-03-25
**Status**: Approved (YOLO Mode)
**Scope**: A standalone React component with a TUI/Gridland aesthetic for showcasing `tube2txt`.

## Summary
The goal is to provide a browser-based "Terminal User Interface" (TUI) showcase for `tube2txt` that mimics the Gridland.io aesthetic. This includes high-contrast monospace typography, CRT scanlines, box-drawing characters, and a simulated CLI command flow.

## Architecture

### Visual Components
- **`TUIContainer`**: The outer shell that handles the CRT overlay (scanlines, flicker, glow) and global font settings (Monospace).
- **`TerminalEmulator`**: A custom-built typing simulator that "runs" `tube2txt` commands, shows progress bars, and renders the "cyan" AI output.
- **`FeatureGrid`**: A 2x2 or 3x1 grid of terminal-style boxes highlighting key features (AI Voice, Smart Clips, Global Search).
- **`TUIBox`**: A reusable component that uses Tailwind's border utilities or CSS `border-image` to mimic box-drawing characters (┌ ─ ┐ │ └ ─ ┘).

### Interactive Flow
1. **Initial State**: A cursor blinking at a `$` prompt.
2. **Typing Phase**: `tube2txt --ai https://youtube.com/watch?v=...` is typed out automatically.
3. **Execution Phase**: 
   - A simulated download progress bar (`[====>    ] 50%`).
   - A "Parsing..." status.
   - A rapid "Thinking..." step.
4. **Output Phase**: The terminal clears and renders a vibrant Cyan AI Outline with timestamped segments.

## Tech Stack
- **Framework**: React / Next.js
- **Styling**: Tailwind CSS (with custom `box-shadow` for glow and `keyframes` for flicker).
- **Icons**: Lucide-React (optional, but ASCII-style characters are preferred).
- **Animation**: CSS transitions and basic React state for the typing effect.

## Proposed Solution: The "Matrix" Approach
- Use a deep background (`#0A0A0A` or Dracula's dark grey) with high-vibrancy Cyan (`#00FFFF`) and Magenta/Purple accents.
- Implement scanlines via a linear-gradient overlay on the `::after` pseudo-element of the main container.
- Use `framer-motion` for smooth layout transitions if needed, but standard React state is preferred for the "hard" terminal feel.

## Alternative Considered: `@opentui/react`
While the project uses OpenTUI for the actual TUI, a "showcase" for a standard website is often easier to distribute as a standard HTML/CSS component. This allows it to be dropped into a landing page without requiring the OpenTUI renderer setup.

## Implementation Details
The single-file component will include:
1.  **Tailwind Config Overrides**: (Inlined as classes where possible).
2.  **CRT Scanline CSS**: Injected via a `<style>` tag or Tailwind arbitrary values.
3.  **Terminal Simulation Hook**: To manage the sequence of states (Idle -> Typing -> Progress -> Result).

## Verification
- Visually verify CRT effect in browser.
- Verify typing simulation timing.
- Check responsiveness (Terminal should "wrap" like a real TUI).
