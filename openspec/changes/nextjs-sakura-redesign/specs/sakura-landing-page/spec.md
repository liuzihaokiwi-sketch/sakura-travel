## ADDED Requirements

### Requirement: Hero section with data authority messaging
The landing page SHALL display a full-width hero section with a real sakura background image, dark overlay, and prominent headline emphasizing data fusion authority ("4大权威数据源融合"). The hero SHALL include a primary CTA button linking to the custom service page.

#### Scenario: Hero visual impact
- **WHEN** user opens the landing page at `/`
- **THEN** a full-viewport hero with sakura background, glassmorphism title overlay, and animated entrance (Framer Motion fade-in) is displayed

### Requirement: Data authority statistics display
The page SHALL display key data metrics in a visually impactful grid: 4 data sources (JMA/JMC/Weathernews/Local Official), 58 JMA-observed cities, 240+ sakura spots, daily 3x updates, 200万+ Weathernews user reports, 10-year historical accuracy analysis, and 0-100 confidence scoring.

#### Scenario: Statistics grid rendering
- **WHEN** user scrolls to the data authority section
- **THEN** animated counter numbers appear with source labels, each with Framer Motion stagger entrance

### Requirement: Custom service CTA banner
The page SHALL include a prominent CTA banner section linking to `/custom` with messaging about free trial ("免费体验1天攻略"), WeChat contact info, and trust indicators.

#### Scenario: CTA banner visibility
- **WHEN** user views the landing page
- **THEN** a warm-gradient CTA banner is visible without scrolling on desktop, and within first scroll on mobile

### Requirement: Floating global CTA
All pages SHALL display a floating CTA button (bottom-right on desktop, bottom-center on mobile) that links to the custom service page or copies the WeChat ID.

#### Scenario: Floating CTA on all pages
- **WHEN** user is on any page (/, /rush, /custom, /city/*)
- **THEN** a floating CTA button with pulse animation is visible and functional
