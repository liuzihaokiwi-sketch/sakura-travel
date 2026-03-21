## ADDED Requirements

### Requirement: Playwright full-page screenshot export
The system SHALL provide a script (`scripts/export-playwright.ts`) that launches Playwright, navigates to any page with `?export=true` query parameter, and captures a pixel-perfect PNG screenshot at specified dimensions.

#### Scenario: Export rush page as Xiaohongshu image
- **WHEN** running `npx tsx scripts/export-playwright.ts --url /rush --width 1080 --height 1440 --output output/rush.png`
- **THEN** a 1080×1440 PNG is saved to `output/rush.png` with the rush page content rendered without navigation bar

#### Scenario: Export mode hides navigation
- **WHEN** a page is loaded with `?export=true` query parameter
- **THEN** the Navbar and FloatingCTA components are hidden

### Requirement: Satori batch social card generation
The system SHALL provide a script (`scripts/export-satori.ts`) that generates social media cards using Satori + resvg-js without a browser. Cards are rendered from JSX templates in `components/social/`.

#### Scenario: Batch generate Xiaohongshu covers
- **WHEN** running `npx tsx scripts/export-satori.ts --template xhs-cover --output output/xhs/`
- **THEN** PNG files at 1080×1440 are generated for each city's top spots using `XhsCover.tsx` template

#### Scenario: Generate WeChat Moment cards
- **WHEN** running `npx tsx scripts/export-satori.ts --template moment --output output/moments/`
- **THEN** PNG files at 1080×1080 are generated using `MomentCard.tsx` template

### Requirement: Chinese font support in Satori
The system SHALL bundle Noto Sans SC font files in `public/fonts/` for Satori rendering. Font loading SHALL be handled by a shared utility (`lib/satori.ts`).

#### Scenario: Chinese characters render correctly
- **WHEN** Satori renders a card containing Chinese text "东京樱花满开"
- **THEN** all characters render correctly using Noto Sans SC, with no missing glyphs

### Requirement: Social card templates
The system SHALL provide at least 3 social card templates:
1. `XhsCover.tsx` — Xiaohongshu cover (1080×1440) with sakura background, title, key stats
2. `XhsContent.tsx` — Xiaohongshu content page (1080×1440) with spot rankings
3. `MomentCard.tsx` — WeChat Moment card (1080×1080) with single-spot highlight

#### Scenario: XhsCover template output
- **WHEN** XhsCover is rendered with Tokyo spot data
- **THEN** output shows sakura-themed cover with "2026 东京樱花" title, top 3 spots, and bloom dates
