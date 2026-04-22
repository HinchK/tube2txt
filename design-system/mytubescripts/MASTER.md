# Design System Master File

> **LOGIC:** When building a specific page, first check `design-system/pages/[page-name].md`.
> If that file exists, its rules **override** this Master file.
> If not, strictly follow the rules below.

---

**Project:** MyTubeScripts Remote Gallery
**Category:** Dystopian Landing Page & App
**Style:** Cyberpunk, Neon, Dark Mode, Glassmorphism

---

## Global Rules

### Color Palette

| Role | Hex | CSS Variable |
|------|-----|--------------|
| Primary/Neon | `#00FF41` | `--color-primary` (Matrix Green) |
| Secondary | `#FF003C` | `--color-secondary` (Cyberpunk Red) |
| Accent/Glow | `#00F0FF` | `--color-accent` (Neon Cyan) |
| Background | `#0D0E15` | `--color-background` (Deep Void) |
| Surface/Glass | `rgba(20, 22, 35, 0.6)`| `--color-surface` |
| Text Primary | `#E0E6ED` | `--color-text` |
| Text Muted | `#8A95A5` | `--color-text-muted` |

**Color Notes:** High contrast neon accents on an abyssal dark background. Glow effects using box-shadows.

### Typography

- **Heading Font:** Orbitron or Share Tech Mono
- **Body Font:** Inter or Roboto Mono
- **Mood:** dystopian, hacker, terminal, futuristic, sleek
- **Google Fonts:**
```css
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;500;700;900&family=Inter:wght@400;500;600&family=Share+Tech+Mono&display=swap');
```

### Spacing Variables

| Token | Value | Usage |
|-------|-------|-------|
| `--space-xs` | `4px` / `0.25rem` | Tight gaps |
| `--space-sm` | `8px` / `0.5rem` | Icon gaps, inline spacing |
| `--space-md` | `16px` / `1rem` | Standard padding |
| `--space-lg` | `24px` / `1.5rem` | Section padding |
| `--space-xl` | `32px` / `2rem` | Large gaps |
| `--space-2xl` | `48px` / `3rem` | Section margins |
| `--space-3xl` | `64px` / `4rem` | Hero padding |

### Shadow & Glow Depths

| Level | Value | Usage |
|-------|-------|-------|
| `--glow-primary` | `0 0 10px rgba(0, 255, 65, 0.5), 0 0 20px rgba(0, 255, 65, 0.3)` | Primary buttons/cards |
| `--glow-secondary`| `0 0 10px rgba(255, 0, 60, 0.5), 0 0 20px rgba(255, 0, 60, 0.3)` | Alerts/Warnings |
| `--glow-accent` | `0 0 10px rgba(0, 240, 255, 0.5), 0 0 20px rgba(0, 240, 255, 0.3)`| Links, timestamps |
| `--glass-border`| `1px solid rgba(255, 255, 255, 0.1)` | Glassmorphism card borders |

---

## Component Specs

### Glassmorphism Cards

```css
.card-glass {
  background: var(--color-surface);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border: var(--glass-border);
  border-radius: 4px; /* Sharp corners for cyberpunk feel */
  padding: 24px;
  transition: all 300ms ease;
  position: relative;
  overflow: hidden;
}

/* Cyberpunk decorative corner cut or top border */
.card-glass::before {
  content: '';
  position: absolute;
  top: 0; left: 0; width: 100%; height: 2px;
  background: linear-gradient(90deg, var(--color-primary), var(--color-accent));
  opacity: 0;
  transition: opacity 300ms;
}

.card-glass:hover::before {
  opacity: 1;
}

.card-glass:hover {
  box-shadow: var(--glow-accent);
  transform: translateY(-2px);
  border-color: rgba(0, 240, 255, 0.3);
}
```

### Buttons

```css
/* Primary Neon Button */
.btn-neon {
  background: transparent;
  color: var(--color-primary);
  border: 1px solid var(--color-primary);
  padding: 12px 24px;
  font-family: 'Share Tech Mono', monospace;
  text-transform: uppercase;
  letter-spacing: 2px;
  transition: all 200ms ease;
  cursor: pointer;
  position: relative;
  overflow: hidden;
}

.btn-neon:hover {
  background: var(--color-primary);
  color: var(--color-background);
  box-shadow: var(--glow-primary);
}
```

### Timestamp Links (YouTube)

```css
.timestamp-link {
  color: var(--color-accent);
  font-family: 'Share Tech Mono', monospace;
  text-decoration: none;
  border-bottom: 1px dashed var(--color-accent);
  transition: all 200ms ease;
}

.timestamp-link:hover {
  color: white;
  background: var(--color-accent);
  border-bottom: 1px solid transparent;
  box-shadow: 0 0 8px var(--color-accent);
  padding: 0 4px;
}
```

---

## Layout Structure

**Pages:**
1. **Landing Page:** Hero section with neon glitch effects, "How-to run your own local analyzer" section, featured gallery, Creator Spotlight.
2. **Featured Gallery:** Grid of processed video scripts (Glassmorphism cards).
3. **Video Detail Page:** Transcript view with sparse screenshots (at key timestamps).
4. **How-To Page:** Quick instructions on setting up Tube2Txt locally.

**Content Rules:**
- **No Video Uploads:** Display sparse images only.
- **Timestamps:** Every timestamp must be a `<a href="https://youtube.com/watch?v=ID&t=SECONDS">` link.
- **Data Fetching:** Pull metadata from Supabase, linking out to YouTube for playback.

---

## Pre-Delivery Checklist

Before delivering UI code, verify:
- [ ] Neon glow effects do not cause performance stuttering (use opacity/box-shadow carefully).
- [ ] Glassmorphism background blur uses `-webkit-backdrop-filter` for Safari support.
- [ ] Text contrast on dark backgrounds is at least 4.5:1.
- [ ] No actual video files are hosted or embedded (only images and YouTube links).
- [ ] Hover states provide strong visual feedback (glow, color inversion).
- [ ] Typography sets the right dystopian mood (monospaced accents, sans-serif body).
