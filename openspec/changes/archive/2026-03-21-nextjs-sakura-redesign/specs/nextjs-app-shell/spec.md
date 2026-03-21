## ADDED Requirements

### Requirement: Next.js 14 App Router project with Tailwind + shadcn/ui + Framer Motion
The system SHALL provide a Next.js 14 project under `web/` directory using App Router, configured with Tailwind CSS, shadcn/ui components, and Framer Motion. The project SHALL coexist with the existing Python backend in the same monorepo without mutual dependencies.

#### Scenario: Project initialization and dev server
- **WHEN** developer runs `cd web && npm install && npm run dev`
- **THEN** Next.js dev server starts successfully at `localhost:3000` with Tailwind styles, shadcn/ui components, and Framer Motion all functional

#### Scenario: No additional UI frameworks
- **WHEN** inspecting `package.json` dependencies
- **THEN** there SHALL be no UI frameworks other than shadcn/ui (no Material UI, Ant Design, Chakra, etc.)

### Requirement: Global layout with sakura theme
The system SHALL provide a root `layout.tsx` with sakura-themed color palette (sakura/warm/stone scales), display fonts (Playfair Display + Noto Serif SC for headings, Inter + Noto Sans SC for body), and a responsive Navbar component.

#### Scenario: Font loading
- **WHEN** any page loads
- **THEN** headings render in Playfair Display / Noto Serif SC and body text renders in Inter / Noto Sans SC

#### Scenario: Theme colors available
- **WHEN** using Tailwind classes like `bg-sakura-100` or `text-warm-400`
- **THEN** the correct custom colors from the design system are applied

### Requirement: Data loading from JSON files
The system SHALL load sakura data from `../data/sakura/` JSON files at build time (SSG). A `DATA_DIR` environment variable SHALL allow overriding the data directory path.

#### Scenario: Build-time data loading
- **WHEN** running `npm run build`
- **THEN** pages are statically generated with data from JSON files (weathernews_all_spots.json, sakura_rush_scores.json, etc.)

#### Scenario: Custom data directory
- **WHEN** `DATA_DIR=/custom/path npm run build` is executed
- **THEN** data is loaded from `/custom/path` instead of the default relative path
