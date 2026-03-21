## ADDED Requirements

### Requirement: Sakura color palette in Tailwind
The Tailwind config SHALL extend the default palette with sakura (pink gradient), warm (orange gradient), and stone (neutral) color scales. All custom colors MUST be available as Tailwind utility classes.

#### Scenario: Custom color classes work
- **WHEN** using `className="bg-sakura-100 text-warm-400 border-sakura-200"`
- **THEN** the correct custom colors are applied matching the design system hex values

### Requirement: Typography scale with display and body fonts
The system SHALL configure two font families: `font-display` (Playfair Display + Noto Serif SC) for headings and `font-sans` (Inter + Noto Sans SC) for body text. A `font-mono` (JetBrains Mono) SHALL be available for data/numbers.

#### Scenario: Heading font rendering
- **WHEN** an element has `className="font-display text-3xl"`
- **THEN** it renders in Playfair Display (Latin) / Noto Serif SC (CJK) at 1.875rem

### Requirement: Reusable GlassmorphCard component
The system SHALL provide a `GlassmorphCard` component with backdrop-blur, semi-transparent background, and subtle border. It SHALL accept `variant` prop for light/dark themes.

#### Scenario: Light glassmorphism card
- **WHEN** rendering `<GlassmorphCard variant="light">content</GlassmorphCard>`
- **THEN** a card with `bg-white/80 backdrop-blur-xl border-white/20` styling is displayed

#### Scenario: Dark glassmorphism card
- **WHEN** rendering `<GlassmorphCard variant="dark">content</GlassmorphCard>`
- **THEN** a card with `bg-black/60 backdrop-blur-xl border-white/10` styling is displayed

### Requirement: Framer Motion animation presets
The system SHALL export reusable animation presets: `fadeInUp`, `fadeInDown`, `scaleIn`, `staggerContainer`, `slideInLeft`, `slideInRight`. All presets SHALL use consistent easing curves.

#### Scenario: Stagger animation on card grid
- **WHEN** wrapping cards in `<motion.div variants={staggerContainer}>`
- **THEN** cards animate in sequence with 80ms delay between each

### Requirement: SakuraParticles ambient animation
The system SHALL provide a `SakuraParticles` component that renders CSS-animated falling sakura petals as ambient background decoration. It SHALL be lightweight (CSS-only, no canvas/WebGL).

#### Scenario: Particles on landing page
- **WHEN** `<SakuraParticles />` is rendered
- **THEN** sakura petal shapes drift downward with varying speeds, sizes, and rotation

### Requirement: Consistent card hover effects
All interactive cards SHALL have consistent hover effects: slight upward translate (-2px), shadow increase, and 200ms transition duration.

#### Scenario: Card hover interaction
- **WHEN** user hovers over a SpotCard or AdvantageCard
- **THEN** the card lifts 2px with increased shadow, transitioning over 200ms
