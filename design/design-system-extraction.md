 # Design System Extraction

 Source: extracted verbatim from project files in this repository.

 All values below are taken directly from the code. Each value includes the source file path where it was found.

 **Files checked first (source of truth):**
 - `postcss.config.mjs` (project uses Tailwind via PostCSS)
 - `src/app/globals.css` (CSS custom properties, animations, radii, tokens)
 - `components.json` (shadcn config; shows icon library + css vars usage)
 - `src/app/layout.tsx` (font registration via `next/font/local`)
 - `src/components/ui/button.tsx` (button primitives)
 - `src/components/theme-provider.tsx`, `src/components/theme-toggle.tsx` (theme handling)
 - `src/components/GradualBlur.css`, `src/components/NeumorphButton.tsx`, `src/components/PixelTransition.tsx`, `src/components/shimmering-text.tsx`, `src/components/ui/background-beams.tsx`, `src/components/ui/tooltip.tsx`, `src/components/ui/dropdown-menu.tsx` (visual effects & primitives)

 ---

 **1. Color palette**

 Source: `src/app/globals.css` (:root and .dark blocks)

 - CSS custom properties (light theme :root):
   - `--radius: 0.625rem;` (used to derive radii) — src/app/globals.css
   - `--background: hsl(97 4% 100%);` — src/app/globals.css
   - `--foreground: oklch(0.241 0.005 285.823);` — src/app/globals.css
   - `--loader-bg: hsl(97 4% 100%);` — src/app/globals.css
   - `--card: oklch(1 0 0);` — src/app/globals.css
   - `--card-foreground: oklch(0.241 0.005 285.823);` — src/app/globals.css
   - `--popover: oklch(1 0 0);` — src/app/globals.css
   - `--popover-foreground: oklch(0.241 0.005 285.823);` — src/app/globals.css
   - `--primary: oklch(0.31 0.006 285.885);` — src/app/globals.css
   - `--primary-foreground: oklch(0.985 0 0);` — src/app/globals.css
   - `--secondary: oklch(0.967 0.001 286.375);` — src/app/globals.css
   - `--secondary-foreground: oklch(0.31 0.006 285.885);` — src/app/globals.css
   - `--muted: oklch(0.967 0.001 286.375);` — src/app/globals.css
   - `--muted-foreground: oklch(0.652 0.016 285.938);` — src/app/globals.css
   - `--accent: oklch(0.967 0.001 286.375);` — src/app/globals.css
   - `--accent-foreground: oklch(0.31 0.006 285.885);` — src/app/globals.css
   - `--destructive: oklch(0.577 0.245 27.325);` — src/app/globals.css
   - `--border: oklch(0.85 0.004 286.32);` — src/app/globals.css
   - `--input: oklch(0.85 0.004 286.32);` — src/app/globals.css
   - `--ring: oklch(0.605 0.015 286.067);` — src/app/globals.css
   - `--chart-1: oklch(0.646 0.222 41.116);` — src/app/globals.css
   - `--chart-2: oklch(0.6 0.118 184.704);` — src/app/globals.css
   - `--chart-3: oklch(0.398 0.07 227.392);` — src/app/globals.css
   - `--chart-4: oklch(0.828 0.189 84.429);` — src/app/globals.css
   - `--chart-5: oklch(0.769 0.188 70.08);` — src/app/globals.css
   - sidebar tokens (`--sidebar`, `--sidebar-foreground`, etc.) — src/app/globals.css

 - Dark theme overrides (class `.dark`):
   - `--background: #000000;` — src/app/globals.css
   - `--foreground: oklch(0.985 0 0);` — src/app/globals.css
   - `--card: #0f0f0f;` — src/app/globals.css
   - `--card-foreground: oklch(0.985 0 0);` — src/app/globals.css
   - `--primary: oklch(0.92 0.004 286.32);` — src/app/globals.css
   - `--primary-foreground: #0f0f0f;` — src/app/globals.css
   - `--secondary: #111111;` — src/app/globals.css
   - `--muted: #111111;` — src/app/globals.css
   - `--destructive: oklch(0.704 0.191 22.216);` — src/app/globals.css
   - `--border: oklch(1 0 0 / 10%);` — src/app/globals.css
   - `--input: oklch(1 0 0 / 15%);` — src/app/globals.css
   - `--ring: oklch(0.552 0.016 285.938);` — src/app/globals.css
   - chart/different shades listed in `.dark` — src/app/globals.css

 - Additional accent/illustration colors found in `src/components/ui/background-beams.tsx` (SVG gradients):
   - `#18CCFC` — stop color — src/components/ui/background-beams.tsx
   - `#6344F5` — stop color — src/components/ui/background-beams.tsx
   - `#AE48FF` — stop color — src/components/ui/background-beams.tsx
   - `strokeOpacity="0.4"`, `strokeWidth="0.5"` on paths — src/components/ui/background-beams.tsx

 - Tailwind palette note: no `tailwind.config.*` present; `components.json` indicates Tailwind CSS used and `baseColor: "zinc"` — components.json

 Source files: `src/app/globals.css`, `src/components/ui/background-beams.tsx`, `components.json`.

 ---

 **2. Typography**

 Sources: `src/app/layout.tsx`, `src/app/globals.css`, `src/fonts/*`, compiled CSS in `.next/static/css/app/layout.css`

 - Fonts (how loaded & exact family names):
   - GeistPixel loaded via `next/font/local` in `src/app/layout.tsx`:
     - local file: `src/fonts/GeistPixel-Regular-VariableFont_ELSH.ttf` — src/app/layout.tsx
     - variable name used in layout: `--font-geist-pixel-square` — src/app/layout.tsx
     - compiled @font-face shows family `'geistPixelSquare'` and variable `--font-geist-pixel-square` — .next/static/css/app/layout.css
   - ClashDisplay files present in `src/fonts/` (ClashDisplay-Bold.woff2, ClashDisplay-Regular.woff2, ClashDisplay-Semibold.woff2) — src/fonts/

 - Where used (examples):
   - Root HTML uses `geistPixelSquare.variable` and `body` uses `geistPixelSquare.className` — src/app/layout.tsx
   - `--font-geist-pixel-square` referenced in `src/app/globals.css` as `--font-sans` — src/app/globals.css

 - Type scale tokens (defined/available in compiled CSS):
   - `--text-xs: 0.75rem` — .next/static/css/app/layout.css
   - `--text-sm: 0.875rem` — .next/static/css/app/layout.css
   - `--text-base: 1rem` — .next/static/css/app/layout.css
   - `--text-lg: 1.125rem` — .next/static/css/app/layout.css
   - `--text-xl: 1.25rem` — .next/static/css/app/layout.css
   - `--text-2xl: 1.5rem` — .next/static/css/app/layout.css
   - `--text-3xl: 1.875rem` — .next/static/css/app/layout.css
   - `--text-4xl: 2.25rem` — .next/static/css/app/layout.css

 - Actual font-size classes observed in components (examples):
   - `text-[15px]` — src/components/BlogCard.tsx, src/components/MasonryProjectCard.tsx
   - `text-[13px]` — src/components/ui/tooltip-card.tsx
   - `text-[10px]`, `text-[11px]`, `text-[28px]`, `text-[1.10rem]` — observed in component usages (see `src/components/*`)
   - Tailwind responsive usage: `text-sm`, `text-base`, `text-lg`, `text-xl`, `sm:text-xl`, `md:text-4xl` — many components

 - Font weights: `font-medium`, `font-semibold`, `font-bold` used across components — see `src/components/*`

 Source files: `src/app/layout.tsx`, `src/app/globals.css`, `src/fonts/*`, `.next/static/css/app/layout.css`, many `src/components/*` usages.

 ---

 **3. Spacing and layout**

 Sources: compiled CSS `.next/static/css/app/layout.css`, `src/app/globals.css`, component class usage

 - Base spacing unit: `--spacing: 0.25rem` (4px) — .next/static/css/app/layout.css
   - utilities like `.size-4` map to `calc(var(--spacing) * 4)` → 1rem — .next/static/css/app/layout.css

 - Common spacing classes observed: `p-4`, `px-4`, `py-2`, `p-6`, `px-6`, `py-3`, `gap-2`, `gap-3`, `gap-4`, responsive `sm:` variants — seen across `src/components/*`

 - Container / max-width variables:
   - `--container-sm: 24rem` — .next/static/css/app/layout.css
   - `--container-md: 28rem` — .next/static/css/app/layout.css
   - `--container-lg: 32rem` — .next/static/css/app/layout.css
   - `--container-4xl: 56rem` — .next/static/css/app/layout.css

 - Grid / layout patterns: components use responsive flex/grid + Tailwind defaults; `PixelTransition` contains a literal `w-[300px] max-w-full` card example — src/components/PixelTransition.tsx

 Source files: `.next/static/css/app/layout.css`, `src/app/globals.css`, `src/components/*`.

 ---

 **4. Borders, radius, and elevation**

 Sources: `src/app/globals.css`, component files, compiled CSS `.next/static/css/app/layout.css`

 - Radius tokens:
   - `--radius: 0.625rem` (10px) — src/app/globals.css
   - `--radius-sm: calc(var(--radius) - 4px)` (≈6px) — src/app/globals.css
   - `--radius-md: calc(var(--radius) - 2px)` (≈8px) — src/app/globals.css
   - `--radius-lg: var(--radius)` (10px) — src/app/globals.css
   - `--radius-xl: calc(var(--radius) + 4px)` (≈14px) — src/app/globals.css

 - Borders & widths: standard Tailwind `border` (1px) used; example `border-2` used in `PixelTransition` — src/components/PixelTransition.tsx

 - Box-shadows / elevation:
   - `.shadow-xs` → `0 1px 2px 0 rgba(0 0 0 / 0.05)` — .next/static/css/app/layout.css
   - `.shadow-sm`, `.shadow-md`, `.shadow-lg`, `.shadow-xl` present with expected Tailwind values in compiled CSS — .next/static/css/app/layout.css
   - Inline explicit: `box-shadow: 0 4px 10px -4px rgba(15,23,42,0.15)` — src/components/NeumorphButton.tsx
   - Hover inset shadows on `NeumorphButton` (see file for hover values) — src/components/NeumorphButton.tsx

 Source files: `src/app/globals.css`, `.next/static/css/app/layout.css`, `src/components/NeumorphButton.tsx`.

 ---

 **5. Component-level extraction**

 Component: Primary button
 Default: inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-md text-sm font-medium transition-all disabled:pointer-events-none disabled:opacity-50 [&_svg]:pointer-events-none [&_svg:not([class*='size-'])]:size-4 shrink-0 [&_svg]:shrink-0 outline-none focus-visible:border-ring focus-visible:ring-ring/50 focus-visible:ring-[3px] aria-invalid:ring-destructive/20 dark:aria-invalid:ring-destructive/40 aria-invalid:border-destructive bg-primary text-primary-foreground hover:bg-primary/90 h-9 px-4 py-2 has-[>svg]:px-3
 Source: `src/components/ui/button.tsx`

 Component: Secondary button (variant `secondary`)
 Default: inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-md text-sm font-medium transition-all disabled:pointer-events-none disabled:opacity-50 [&_svg]:pointer-events-none [&_svg:not([class*='size-'])]:size-4 shrink-0 [&_svg]:shrink-0 outline-none focus-visible:border-ring focus-visible:ring-ring/50 focus-visible:ring-[3px] aria-invalid:ring-destructive/20 dark:aria-invalid:ring-destructive/40 aria-invalid:border-destructive bg-secondary text-secondary-foreground hover:bg-secondary/80 h-9 px-4 py-2 has-[>svg]:px-3
 Source: `src/components/ui/button.tsx`

 Component: Ghost button (variant `ghost`)
 Default: inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-md text-sm font-medium transition-all disabled:pointer-events-none disabled:opacity-50 [&_svg]:pointer-events-none [&_svg:not([class*='size-'])]:size-4 shrink-0 [&_svg]:shrink-0 outline-none focus-visible:border-ring focus-visible:ring-ring/50 focus-visible:ring-[3px] aria-invalid:ring-destructive/20 dark:aria-invalid:ring-destructive/40 aria-invalid:border-destructive hover:bg-accent hover:text-accent-foreground dark:hover:bg-accent/50 h-9 px-4 py-2 has-[>svg]:px-3
 Source: `src/components/ui/button.tsx`

 Component: Input field (example / default classes)
 Default: bg-white dark:bg-neutral-800 border-neutral-200 dark:border-neutral-700 text-neutral-900 dark:text-neutral-100 rounded-xl
 Source: `src/components/ResumeVisitor.tsx` (SignIn `appearance.elements.formFieldInput`)

 Component: Card / Panel (representative)
 Default: shadow-2xl border border-neutral-200 dark:border-neutral-800 rounded-3xl bg-[#d9d9d9] dark:bg-[#0d0d0d] w-full max-w-sm p-6 overflow-x-hidden
 Source: `src/components/ResumeVisitor.tsx` (SignIn `appearance.elements.card`)

 Component: Badge / Pill
 Default: px-2 sm:px-3 py-0.5 sm:py-1 bg-neutral-100 dark:bg-neutral-900 text-neutral-800 dark:text-neutral-200 rounded-full text-xs whitespace-nowrap
 Source: `src/components/BlogContent.tsx`, `src/components/ProjectCard.tsx`

 Component: Dropdown / Select (Radix)
 Default: bg-popover text-popover-foreground ... rounded-md border p-1 shadow-md (full class in `src/components/ui/dropdown-menu.tsx`)
 Item: focus:bg-accent focus:text-accent-foreground relative flex cursor-default items-center gap-2 rounded-sm px-2 py-1.5 text-sm ...
 Source: `src/components/ui/dropdown-menu.tsx`

 Component: Tooltip / Popover
 Default: bg-foreground text-background animate-in fade-in-0 zoom-in-95 ... z-50 w-fit origin-(--radix-tooltip-content-transform-origin) rounded-md px-3 py-1.5 text-xs text-balance
 Arrow: bg-foreground fill-foreground size-2.5 translate-y-[calc(-50%_-_2px)] rotate-45 rounded-[2px]
 Source: `src/components/ui/tooltip.tsx`

 Component: Loader / Skeleton (examples)
 Default loader class (`loader` in globals.css): font-size: 40px; -webkit-text-stroke: 1px #000; background: radial-gradient(...); animation: l9 2s linear infinite — src/app/globals.css
 Spinner example: `w-6 h-6 border-2 border-neutral-400 border-t-transparent rounded-full animate-spin` — src/components/ResumeVisitor.tsx

 ---

 **6. Iconography**

 - Icon library: `lucide` / `lucide-react` — `components.json`, many components
 - Typical sizes: `size-4` utility (maps to `calc(var(--spacing) * 4)`), explicit `w-4 h-4`, `w-5 h-5`, `text-base`, `text-[16px]` — `.next/static/css/app/layout.css`, `src/components/*`
 - Color conventions: icons follow surrounding text color utilities (`text-neutral-600`, `dark:text-neutral-400`, `text-black/75`, etc.) — `src/components/*`

 Source files: `components.json`, `.next/static/css/app/layout.css`, `src/components/*`

 ---

 **7. Motion / animation**

 - Transition & easing literals:
   - `transition-all duration-150 ease-out` — `src/components/NeumorphButton.tsx`
   - `animate-fadeIn` (0.3s cubic-bezier(0.4,0,0.2,1)) and `animate-fade-up` (0.4s ease-out) — `src/app/globals.css`
   - Shiny text: `shiny-text` keyframes and `--animate-shiny-text: shiny-text 8s infinite` — `src/app/globals.css`
   - Marquee animations: `--animate-marquee: marquee var(--duration) infinite linear` — `src/app/globals.css`

 - Component patterns:
   - `NeumorphButton` hover translate + inset-shadow — src/components/NeumorphButton.tsx
   - `PixelTransition` uses GSAP; default `gridSize=7`, `pixelColor=currentColor`, `animationStepDuration=0.3s` — src/components/PixelTransition.tsx
   - `ShimmeringText` per-char motion with default `duration=1s` — src/components/shimmering-text.tsx
   - `BackgroundBeams` animates SVG gradients with durations ~10–20s and `easeInOut` repeat — src/components/ui/background-beams.tsx
   - Theme toggle uses `startViewTransition` when available — src/components/theme-toggle.tsx

 Source files: `src/app/globals.css`, `src/components/*`.

 ---

 **8. Custom Tailwind config additions**

 - No `tailwind.config.*` file found at repository root. Tailwind is enabled via PostCSS plugin `@tailwindcss/postcss` in `postcss.config.mjs` — postcss.config.mjs
 - `components.json` indicates `css: "src/app/globals.css"`, `cssVariables: true`, `baseColor: "zinc"` (shadcn integration) — components.json
 - Compiled CSS ( `.next/static/css/app/layout.css` ) shows many CSS custom properties (colors, spacing, container sizes, text size tokens). Because there is no `tailwind.config.*` file, there is no verbatim `theme.extend` block to dump.

 ---

 Fit notes

 - Directly portable pieces for a dense research UI: color tokens, typography pairing & font registration, button/input class patterns, radius and shadow scales.
 - Heavier portfolio-specific effects to use sparingly: `BackgroundBeams` gradients (`#18CCFC`, `#6344F5`, `#AE48FF`), `PixelTransition` GSAP pixelation, `ShimmeringText` per-character shimmer, `GradualBlur` large backdrop filters. Sources: their respective files cited above.

 ---

 If you'd like, I can now:
 - enumerate every distinct `text-*` class used across `src/components/` and list file locations, or
 - produce a machine-readable tokens file (CSS variables → JSON) for direct consumption.

 Sources referenced inline: `src/app/globals.css`, `src/app/layout.tsx`, `components.json`, `postcss.config.mjs`, `.next/static/css/app/layout.css`, `src/components/*` (specific files cited above).
