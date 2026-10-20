# DESIGN.md — Saint Mary's University Knowledge Assistant
> **Design Philosophy: Academic Heritage meets Modern Humanist Software**  
> Inspired by Stripe's precision, Apple's typographic rhythm, and institutional Ivy heritage. Zero AI-slop design.

---

## 1. Color Palette (Realtime Colors Validated — WCAG AAA Compliant)

| Token | Hex Value | Semantic Usage |
| :--- | :--- | :--- |
| `--bg-base` | `#0A0E17` | Deepest canvas obsidian background |
| `--surface-card` | `rgba(16, 24, 39, 0.75)` | Glassmorphic primary cards (backdrop blur 16px) |
| `--surface-card-hover` | `rgba(24, 36, 58, 0.85)` | Interactive card hover elevation |
| `--border-subtle` | `rgba(255, 255, 255, 0.08)` | Default card border |
| `--border-focus` | `rgba(139, 18, 60, 0.65)` | Active focus outline & glowing highlights |
| `--smu-crimson` | `#8B123C` | Saint Mary's official primary brand accent |
| `--smu-crimson-glow` | `rgba(139, 18, 60, 0.35)` | Subtle ambient aura and shadow |
| `--smu-gold` | `#D4AF37` | Institutional heraldic gold accent |
| `--text-primary` | `#F8FAFC` | Main headings and high-contrast reading text |
| `--text-secondary` | `#94A3B8` | Subtitles, labels, and metadata |
| `--text-muted` | `#64748B` | Footers and micro-details |
| `--status-emerald` | `#10B981` | Grounded verification, high confidence |
| `--status-amber` | `#F59E0B` | Moderate confidence warning |
| `--status-rose` | `#F43F5E` | Abstention, out-of-scope inquiry |

---

## 2. Typography Hierarchy

* **Brand & Hero Serif:** `Source Serif 4` / `Instrument Serif` (editorial, scholarly, authoritative)
  * `48px` / `56px` line-height for main hero statement.
  * `-0.02em` letter tracking.
* **UI Controls & Body:** `Plus Jakarta Sans` / `Inter` (geometric, balanced, clean)
  * Body text: `15px` / `1.65` line-height for sustained reading comfort.
  * Captions & Badges: `12px` / `600` weight with uppercase tracking `+0.06em`.
* **Data, Citations & Metrics:** `JetBrains Mono`
  * Monospaced for document IDs (`SMU-FAQ-010-C1`), latency scores (`⚡ 124 ms`), and confidence percentages.

---

## 3. Anti-Slop Design Mandates (Impeccable Rules)

1. **No Purple-to-Blue Gradients**: Color accents are anchored strictly in SMU Crimson (`#8B123C`) and Warm Gold (`#D4AF37`).
2. **No Cards Nested Inside Cards**: Containers have clean, single-depth hierarchy. Secondary information uses understated dividers and subtle row borders.
3. **No Low-Contrast Gray on Colors**: All text against badges or cards maintains a minimum `4.5:1` (AA) or `7:1` (AAA) contrast ratio.
4. **No Cookie-Cutter Icon Tiles**: Icons are delicate, custom-drawn inline SVGs, not chunky generic square app tiles.
5. **Generous Breathing Room**: Components use an 8px mathematical spacing grid (`8px`, `16px`, `24px`, `32px`, `48px`).

---

## 4. Layout Architecture

* **Top App Bar**:
  * Left: Architectural SMU Crest + Institutional title.
  * Center: Live Knowledge Base index pill (256 documents verified).
  * Right: Engine badge (Gemini Cloud LLM / Edge Synthesizer) + Slide-over Settings toggle + Evaluation Benchmark modal.
* **Hero Inquiries (Spotlight Bento Cards)**:
  * 6 common student inquiry categories (Athletics Tickets, Metro Transit, Self-Service Banner, IT Support, Tuition & Fees, Dining Hours).
  * Hover: Micro-elevation, border shimmer, and ambient radial glow.
* **Chat Stream**:
  * Asymmetric, readable chat dialogue.
  * Assistant responses feature an executive summary, grounded answer, verifiable trust strip, and expandable source citations drawer.
* **Floating Command Dock**:
  * Pinned bottom center with ambient glassmorphism (`backdrop-filter: blur(20px)`).
  * Instant keyboard trigger (`Enter` to submit, `Ctrl+K` or `/` to focus).
