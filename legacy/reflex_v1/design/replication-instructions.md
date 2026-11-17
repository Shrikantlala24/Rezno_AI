**Quick replication steps**

1. Copy `design-tokens.css` into your new project and import it before your Tailwind-generated CSS (so variables are available to utilities):

   - In a Next.js `app` project, import in `src/app/globals.css` or `src/app/layout.tsx` head.

2. Add the suggested `tailwind.config.js` (this repo contains `tailwind.config.js`), then install Tailwind and build as usual.

3. Use token values directly in components:
   - Colors: use `bg-[var(--background)]` or map Tailwind color names (the suggested config maps `primary` -> `var(--primary)` so you can use `bg-primary`).
   - Radii: use `rounded-lg` etc. — the config maps `lg/md` to CSS vars.
   - Spacing: utilities still use Tailwind spacing scale; use `p-4` etc. or add custom spacing mapping to `tailwind.config.js` if desired.

4. For font files: copy `src/fonts/*` and register with `next/font/local` or `@font-face` as in `src/app/layout.tsx`.

5. For interactive/motion behavior:
   - Copy `src/components/PixelTransition.tsx`, `src/components/ui/background-beams.tsx`, `src/components/shimmering-text.tsx`, `src/components/NeumorphButton.tsx`, and `src/components/GradualBlur.css` as optional effects. Keep them isolated and use sparingly in a dense UI.

6. To reproduce the exact components' class strings, consult `design-system-extraction.md` in the repo — it contains verbatim class-lists used by primitive components (buttons, dropdowns, tooltips, etc.).

7. Optional: Use `design-tokens.json` to programmatically seed a tokens system (CSS-in-JS, Figma tokens, or a design token pipeline).
