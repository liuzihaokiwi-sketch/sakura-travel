/**
 * web/lib/report/types.ts 鈥?鎶ュ憡娓叉煋灞?TypeScript 绫诲瀷瀹氫箟锛圠3-06锛?
 *
 * 瀵瑰簲 Python 绔細
 *   app/domains/rendering/page_view_model.py
 *   app/domains/rendering/page_planner.py
 *   app/domains/rendering/chapter_planner.py
 *   app/domains/planning/report_schema.py
 */

// 鈹€鈹€ Section Content 绫诲瀷锛團10 discriminated union锛?鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€

export interface TimelineItem {
  time: string
  name: string
  type_icon: string   // "poi" | "restaurant" | "hotel" | "transit" | "buffer"
  duration: string
  note: string
  entity_id?: string
}

export type SectionContent =
  | { type: "timeline";          items: TimelineItem[] }
  | { type: "key_reasons";       reasons: string[] }
  | { type: "stat_strip";        stats: Array<{ label: string; value: string; unit: string }> }
  | { type: "entity_card";       entity_id: string; name: string; entity_type: string; hero_image?: string; tagline: string; stats: Array<{ label: string; value: string; unit: string }> }
  | { type: "risk_card";         risk_type: string; severity: string; description: string; action?: string }
  | { type: "text_block";        text: string; items?: string[] }
  | { type: "fulfillment_list";  items: Array<{ preference_text: string; fulfillment_type: string; evidence: string; explanation: string }> }
  | { type: "toc_list";          entries: Array<{ title: string; page_number: number; chapter_id: string; page_type: string }> }

// 鈹€鈹€ View Model 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€

export interface HeadingVM {
  title: string
  subtitle?: string
  page_number?: number
}

export interface HeroVM {
  image_url?: string
  image_alt: string
  orientation: "landscape" | "portrait" | "square"
  caption?: string
}

export interface SectionVM {
  section_type: string
  heading?: string
  content: SectionContent
}

export interface FooterVM {
  page_number?: number
  chapter_title?: string
}

export interface PageViewModel {
  page_id: string
  page_type: string
  page_size: "full" | "half" | "dual-half"
  heading: HeadingVM
  hero?: HeroVM
  sections: SectionVM[]
  footer?: FooterVM
  day_index?: number
  chapter_id?: string
  stable_inputs?: Record<string, unknown>
  editable_content?: Record<string, unknown>
  internal_state?: Record<string, unknown>
  asset_slots?: Record<string, { slot_id: string; asset_id?: string; resolved?: Record<string, unknown> }>
}

// 鈹€鈹€ Page Plan 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€

export interface PageObjectRef {
  object_type: "entity" | "cluster" | "day" | "chapter" | "trip"
  object_id: string
  role?: "primary" | "secondary" | string
}

export interface PagePlan {
  page_id: string
  page_order: number
  chapter_id: string
  page_type: string
  page_size: "full" | "half" | "dual-half"
  topic_family: string
  object_refs: PageObjectRef[]
  required_slots: string[]
  optional_slots: string[]
  trigger_reason?: string
  merge_policy?: string
  overflow_policy?: string
  priority: number
  day_index?: number
}

// 鈹€鈹€ Chapter Plan 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€

export interface ChapterPlan {
  chapter_id: string
  chapter_type: "frontmatter" | "circle" | "days" | "special" | "appendix"
  title: string
  subtitle?: string
  goal?: string
  mood?: string
  covered_days: number[]
  primary_circle_id?: string
  trigger_reason?: string
  importance: "high" | "medium" | "low"
}

// 鈹€鈹€ Page Type Definition 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€

export interface PageTypeDefinition {
  page_type: string
  topic_family: string
  default_size: "full" | "half" | "dual-half"
  required_slots: string[]
  optional_slots: string[]
  visual_priority: string[]
  mergeable_with: string[]
  print_constraints: string[]
  web_constraints: string[]
  primary_promise: string
}

// 鈹€鈹€ Report Payload锛堝墠绔敤瀛楁瀛愰泦锛?鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€

export interface ReportMeta {
  trip_id: string
  destination: string
  total_days: number
  language: "zh-CN" | "en" | "ja"
  render_mode: "web" | "pdf" | "shared"
  schema_version: "v2"
}

export interface DaySlot {
  slot_index: number
  kind: "poi" | "restaurant" | "hotel" | "activity" | "transit" | "buffer"
  entity_id?: string
  title: string
  area: string
  start_time_hint?: string
  duration_mins?: number
  booking_required: boolean
}

export interface DaySection {
  day_index: number
  title: string
  primary_area: string
  secondary_area?: string
  day_goal: string
  intensity: "light" | "balanced" | "dense"
  must_keep: string
  slots: DaySlot[]
}

export interface EmotionalGoal {
  day_index: number
  mood_keyword: string
  mood_sentence: string
}

export interface PreferenceFulfillmentItem {
  preference_text: string
  fulfillment_type: "fully_met" | "partially_met" | "traded_off" | "not_applicable"
  evidence: string
  object_ref?: string
  explanation: string
}

export interface SkippedOption {
  name: string
  entity_type: string
  why_skipped: string
  would_fit_if?: string
}

export interface RiskWatchItem {
  entity_id?: string
  risk_type: string
  description: string
  action_required?: string
  day_index?: number
}

export interface ReportPayload {
  meta: ReportMeta
  days: DaySection[]
  emotional_goals: EmotionalGoal[]
  preference_fulfillment: PreferenceFulfillmentItem[]
  skipped_options: SkippedOption[]
  risk_watch_items: RiskWatchItem[]
  selection_evidence: Record<string, unknown>[]
}

// 鈹€鈹€ API Response 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€

export interface ReportApiResponse {
  meta: ReportMeta
  page_plan: PagePlan[]
  page_models: Record<string, PageViewModel>
  chapters: ChapterPlan[]
}

