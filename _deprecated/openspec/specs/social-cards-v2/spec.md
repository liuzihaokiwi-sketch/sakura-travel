## ADDED Requirements

### Requirement: Five social card templates with unified brand visual
The system SHALL provide 5 social card templates for XHS/WeChat distribution:
1. `xhs-cover` — City TOP3 ranking cover (1080×1440)
2. `xhs-spot` — Single spot spotlight with real photo (1080×1440)
3. `xhs-compare` — Multi-city bloom timeline comparison (1080×1440)
4. `wechat-moment` — Square card for WeChat Moments (1080×1080)
5. `xhs-story` — Vertical story card (1080×1920)

All templates MUST use the warm brand palette: `#fefaf6` background, `#1c1917` text, `#f7931e` accent.

#### Scenario: Generate xhs-cover for Tokyo
- **WHEN** script runs with `--template xhs-cover --city tokyo`
- **THEN** output PNG is 1080×1440, shows TOP3 Tokyo spots by score, uses warm palette, includes brand footer

#### Scenario: Generate all templates for all cities
- **WHEN** script runs with `--all`
- **THEN** outputs at least 25 PNG files (5 cities × 5 templates)

### Requirement: Real photo integration for spot cards
The system SHALL fetch and embed real photos from weathernews data into `xhs-spot` template cards. Photos MUST be fetched from the `photo` field in spot data, cached locally, and converted to base64 data URI for Satori rendering.

#### Scenario: Spot card with photo
- **WHEN** generating xhs-spot for a spot that has a `photo` URL
- **THEN** the card displays the photo as a background/hero image with a gradient overlay

#### Scenario: Spot card without photo
- **WHEN** generating xhs-spot for a spot that has no `photo` field
- **THEN** the card displays a gradient placeholder (warm palette) instead of a photo

### Requirement: XHS-optimized CTA on all cards
Every card MUST include a footer CTA section with:
- Primary: `🌸 关注我，获取每日花期更新`
- Secondary: `私信"樱花"获取完整景点推荐 ↗`
- Brand mark: `SAKURA RUSH 2026 · 6大数据源融合`

#### Scenario: Footer CTA present
- **WHEN** any card is generated
- **THEN** the bottom section contains primary CTA, secondary CTA, and brand mark text

### Requirement: Bloom stage visual encoding
Each spot on cards MUST display a color-coded bloom stage badge:
- Full bloom (満開): pink `#ec4899`
- Approaching (五分咲): green `#22c55e`
- Not yet: gray `#a8a29e`
- Falling: amber `#f59e0b`

#### Scenario: Full bloom spot display
- **WHEN** a spot has `stage = "full_bloom"` or `full` date within 7 days
- **THEN** the spot displays a pink bloom badge with "🌸 満開"

### Requirement: Score prominently displayed as "能冲指数"
Each spot card MUST display the numeric score (0-100) prominently with the label "能冲指数". The score SHALL use the accent color `#f7931e` and be at least 36px equivalent.

#### Scenario: Score display on spot card
- **WHEN** a spot has score 95
- **THEN** the card shows "95" in large orange text with "能冲指数" label beneath

### Requirement: Batch generation CLI
The `export-satori.ts` script MUST support the following CLI arguments:
- `--template <name>` — Generate specific template (one of: xhs-cover, xhs-spot, xhs-compare, wechat-moment, xhs-story)
- `--city <code>` — Generate for specific city only
- `--spot <name>` — Generate for specific spot only (xhs-spot template)
- `--all` — Generate all templates for all cities
- `--output <dir>` — Output directory (default: `output/cards/`)

#### Scenario: City-specific generation
- **WHEN** script runs with `--template xhs-cover --city kyoto`
- **THEN** only Kyoto cover card is generated, no other cities

#### Scenario: Spot-specific generation
- **WHEN** script runs with `--template xhs-spot --city tokyo --spot "上野恩賜公園"`
- **THEN** only one card for Ueno Park is generated

### Requirement: Photo caching for batch performance
When batch generating, the system MUST cache fetched photos locally to avoid re-downloading. Cache location SHALL be `output/.photo-cache/`. Cached files MUST be reused across runs.

#### Scenario: Second run uses cache
- **WHEN** script runs twice for the same city
- **THEN** the second run does not make HTTP requests for already-cached photos
