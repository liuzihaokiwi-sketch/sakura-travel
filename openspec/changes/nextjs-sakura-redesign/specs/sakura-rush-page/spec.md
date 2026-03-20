## ADDED Requirements

### Requirement: City tabs with spot ranking
The rush page at `/rush` SHALL display a tabbed interface for switching between cities (Tokyo, Kyoto, Osaka, Aichi, Hiroshima). Each tab SHALL show a ranked list of top sakura spots for that city, sorted by score.

#### Scenario: Default city tab
- **WHEN** user navigates to `/rush`
- **THEN** Tokyo tab is active by default with its top spots displayed

#### Scenario: City switching
- **WHEN** user clicks on "京都" tab
- **THEN** the spot list transitions (Framer Motion) to show Kyoto spots sorted by score

### Requirement: Spot card with bloom status
Each spot card SHALL display: spot name (Japanese + Chinese), real photo, bloom status (bud/blooming/full bloom/falling), bloom dates (half/full/fall), tree count, lightup availability, nightview badge, meisyo100 badge, and confidence score (0-100).

#### Scenario: Full bloom spot card
- **WHEN** a spot has `full` date matching current week
- **THEN** the card displays a prominent "🌸 满开中" badge with sakura-gradient background

#### Scenario: Spot with lightup
- **WHEN** a spot has `lightup: true`
- **THEN** a "🌙 夜樱" badge is displayed on the card

### Requirement: Bloom timeline visualization
Each city view SHALL include a horizontal timeline showing the bloom progression (开花 → 五分咲 → 满开 → 散り始め) with date markers for the current week highlighted.

#### Scenario: Current week highlight
- **WHEN** current date falls within a city's bloom period
- **THEN** the timeline highlights the current position with a pulsing indicator

### Requirement: Weekly rush summary
The page SHALL display a "本周冲" (Rush This Week) summary section showing which spots are at peak bloom this week, with urgency messaging.

#### Scenario: Rush spots this week
- **WHEN** multiple spots reach full bloom this week
- **THEN** a highlighted summary card shows "本周 X 个景点满开，错过等明年！"
