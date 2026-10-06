# SEAM v1.0.0 — Client-Grade UI/UX Design System Specification

**Project:** SEAM (Self-Evolving Autonomous Multi-Agent Framework)  
**Roles:** Principal UI/UX Designer, Design System Architect, Accessibility Engineer  
**Status:** **APPROVED & IMPLEMENTED**  
**CSS Source of Truth:** `seam-ide/src/styles.css`

---

## 1. Design System Philosophy & Identity

SEAM is a professional, commercial-grade software-engineering platform. Its visual design communicates:
- **Intelligence & Automation:** The interface feels alive and responsive to autonomous agent activities.
- **Control & Transparency:** The engineer is never left guessing what an agent is executing, which model is responding, or what failed.
- **Restrained Density:** Professional code-oriented density without visual clutter, chaotic animations, or SaaS marketing fluff.

---

## 2. Design Tokens Catalog

### 2.1 Color Palette
Centralized in CSS custom properties under `:root`:

| Token Name | Hex / Value | Semantic Role |
| :--- | :--- | :--- |
| `--seam-bg` | `#0d1117` | Deep neutral canvas background (Graphite foundation) |
| `--seam-surface` | `#161b22` | Primary panel, card, and sidebar surface |
| `--seam-surface-elevated` | `#21262d` | Elevated cards, topbar, modal backgrounds |
| `--seam-surface-hover` | `#30363d` | Interactive element hover states |
| `--seam-border` | `#30363d` | Standard container and divider borders |
| `--seam-border-subtle` | `#21262d` | Inner card and list-item delimiters |
| `--seam-text-primary` | `#f0f6fc` | High-contrast body text and titles |
| `--seam-text-secondary` | `#8b949e` | Explanatory labels, descriptions, and metadata |
| `--seam-text-muted` | `#6e7681` | Disabled states, timestamps, and placeholders |
| `--seam-accent` | `#388bfd` | Primary brand accent and focus rings |
| `--seam-accent-hover` | `#58a6ff` | Hover state for buttons and links |
| `--seam-accent-subtle` | `rgba(56, 139, 253, 0.15)` | Active navigation tabs and selected rows |
| `--seam-success` | `#238636` | Verified passes and completed tasks |
| `--seam-success-text` | `#3fb950` | Text/icon color for pass states |
| `--seam-warning` | `#9e6a03` | Stale diagrams and warnings |
| `--seam-warning-text` | `#d29922` | Text/icon color for warning badges |
| `--seam-danger` | `#da3633` | Test failures, blocked tasks, and errors |
| `--seam-danger-text` | `#f85149` | Text/icon color for error states |
| `--seam-info` | `#1f6feb` | Informational announcements and telemetry |

### 2.2 Typography
- **Sans-Serif Font Stack:** `'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif`
- **Monospace Font Stack:** `'JetBrains Mono', 'Fira Code', 'SF Mono', Consolas, monospace`

| Scale Role | Font Size | Weight | Line Height | Usage |
| :--- | :--- | :--- | :--- | :--- |
| **Display** | 24px | 700 | 1.2 | KPI values, hero headings |
| **Page Title** | 20px | 600 | 1.3 | Top-level view headings |
| **Section Title** | 14px | 600 | 1.4 | Card headers, sidebar category labels |
| **Body** | 13px | 400 | 1.5 | Primary descriptions, table cells |
| **Metadata** | 11px | 400 | 1.4 | Timestamps, file paths, tools |
| **Code / Mono** | 12px | 400 | 1.4 | Code blocks, diffs, API endpoints |
| **Badge / Label** | 10px | 700 | 1.2 | Uppercase status badges, shortcuts |

### 2.3 Spacing Scale
- `2px` (`--seam-space-2`), `4px` (`--seam-space-4`), `8px` (`--seam-space-8`), `12px` (`--seam-space-12`), `16px` (`--seam-space-16`), `20px` (`--seam-space-20`), `24px` (`--seam-space-24`), `32px` (`--seam-space-32`), `48px` (`--seam-space-48`), `64px` (`--seam-space-64`).

### 2.4 Border Radii
- **`xs` (2px):** Badges, keyboard shortcuts.
- **`sm` (4px):** Buttons, inputs, dropdowns.
- **`md` (6px):** Cards, panel tabs, drawer headers.
- **`lg` (8px):** Modals, Command Palette overlay window.
- **`full` (9999px):** Pills, scrollbar thumbs.

### 2.5 Motion & Transitions
- `--seam-motion-instant`: `50ms ease` (Active clicks, toggles).
- `--seam-motion-fast`: `120ms ease` (Button hover, tab highlight).
- `--seam-motion-standard`: `200ms ease` (Drawer slide, dropdown reveal).
- `--seam-motion-slow`: `350ms ease` (Modal backdrop, page route transition).

---

## 3. Core Component Library

1. **Status Badges (`.statusBadge`):**
   - High-contrast, semantic pills supporting: `PASS`, `FAIL`, `RUNNING`, `NOT_CONFIGURED`, `NOT_APPLICABLE`, `UNKNOWN`, `BLOCKED`, `STALE`.
2. **Command Palette (`CommandPalette`):**
   - Modal overlay with search input, arrow key navigation, Enter execution, and Escape dismissal.
3. **Data & Routing Tables (`.routingTable`):**
   - Compact 12px typography, zebra-bordered rows, fixed sticky headers, and responsive horizontal scroll.
4. **Code & Trace Boxes (`.codeBlock`, `.evidenceLog`):**
   - Monospace font, background `#0d1117`, border `#30363d`, syntax-highlighted containers with single-click copy buttons.
5. **Interactive Cards (`.productCard`, `.testCard`, `.modelCard`):**
   - Elevated borders, hover state transitions, and clear metadata hierarchy.

---

## 4. Accessibility (WCAG 2.1 AA) Compliance

- **Contrast Ratio:** Body text exceeds 7.2:1 against background; badge text exceeds 4.8:1 against tinted backgrounds.
- **Focus Indicators:** Interactive elements feature `focus-visible` outline in `--seam-accent` (`#388bfd`) with `-1px` offset.
- **Keyboard Navigation:** Command Palette navigable via `Ctrl+K`, `ArrowUp`, `ArrowDown`, `Enter`, and `Escape`.
- **Screen Reader Support:** Semantic HTML5 elements (`<header>`, `<aside>`, `<main>`, `<article>`), ARIA labels on icon buttons, and non-icon-only status indicators.
