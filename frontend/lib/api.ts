import axios from 'axios';

export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// ── JRE Analysis Endpoint Types ─────────────────────────────────────────────
export interface ChartRequestPayload {
  date: string;
  time: string;
  latitude: number;
  longitude: number;
  altitude: number;
  timezone: string;
  utc_offset: number;
  ayanamsha: 'lahiri' | 'raman' | 'kp' | 'pushya' | 'tropical';
  node_type: 'mean' | 'true';
  house_system: 'equal' | 'placidus' | 'koch' | 'whole_sign' | 'alcabitius';
  transit_orb_tolerance: number;
  shadbala_threshold: number;
  divisional_focus: 'D1' | 'D9' | 'D10' | 'D60';
  dasha_depth: 'MD' | 'MD_AD' | 'MD_AD_PD' | 'MD_AD_PD_SD';
}

export interface VargaPosition {
  sign: string;
  degree: number;
  house: number;
}

export interface PlanetPosition {
  name: string;
  longitude: number;
  d1: VargaPosition;
  d3?: VargaPosition;
  d9: VargaPosition;
  d10?: VargaPosition;
  d60?: VargaPosition;
  nakshatra: string;
  pada: number;
}

export interface CoreAlignment {
  ascendant_sign: string;
  moon_nakshatra: string;
}

export interface ActiveDasha {
  mahadasha: string;
  antardasha: string;
  pratyantardasha: string;
  start_date: string;
  end_date: string;
}

export interface JREAnalysisResponse {
  core_alignment: CoreAlignment;
  planets: PlanetPosition[];
  active_dasha: ActiveDasha;
  synthesis_markdown: string;
}

export interface EvaluationResponse {
  evaluation_id: string;
  subject: string;
  lagna: string;
  moon_nakshatra: string;
  yogas: YogaResult[];
  yoga_count: number;
  formed_count: number;
  processing_time_ms: number;
  engine_version: string;
  disclaimer: string;
  lagna_confidence: string;
  unknown_tob: boolean;
  skipped_yogas: string[];
  elemental_balance: Record<string, number>;
  modality_balance: Record<string, number>;
  dignity_map: Record<string, string>;
  aspect_matrix: AspectResult[];
  planet_details: Record<string, PlanetDetail>;
  birth_data_display: Record<string, string>;
  // Phase 2: Prediction Engine data
  parivartana_yogas: ParivartanaYoga[];
  parivartana_synthesis: ParivartanaSynthesis;
  deep_dasha: DeepDashaResult;
  aspect_matrix_full: AspectMatrixEntry[];
}

export interface AspectResult {
  source: string;
  target: string;
  type: string;
  angle_deg: number;
  source_house: number;
  target_house: number;
}

export interface ParivartanaYoga {
  planet_a: string;
  sign_a: string;
  planet_b: string;
  sign_b: string;
  exchange_type: string;
  house_a: number;
  house_b: number;
  strength: number;
  neecha_bhanga: boolean;
  narrative: string;
}

export interface ParivartanaSynthesis {
  rasi_analysis?: string;
  nakshatra_analysis?: string;
  inter_aspect_modifications?: string;
  final_synthesis?: string;
}

export interface AspectMatrixEntry {
  aspect_category: 'HOUSE_ASPECT' | 'PLANET_ASPECT';
  aspecter: string;
  aspected: string;
  aspect_type: string;
  orb_degrees: number;
  orb_quality: string;
  strength: number;
  is_conjunction: boolean;
  narrative: string;
  // Enriched by backend with house information
  source_planet?: string;
  target_planet?: string;
  source_house?: number;
  target_house?: number;
}

export interface AspectPlanetSummary {
  planet: string;
  total_aspects: number;
  strongest_aspecter: string;
  strongest_strength: number;
  aspects: AspectMatrixEntry[];
}

export interface AspectMatrixResult {
  all_aspects: AspectMatrixEntry[];
  planet_summaries: AspectPlanetSummary[];
  total_aspects: number;
  exact_aspects: number;
}

export interface DashaPeriod {
  lord: string;
  level: string;
  start_utc: string;
  end_utc: string;
  duration_years: number;
  fraction_of_parent: number;
}

export interface SookshmaPeriod {
  lord: string;
  start_utc: string;
  end_utc: string;
  duration_years: number;
  parent_pd_lord: string;
  parent_md_lord: string;
}

export interface DeepDashaResult {
  md: DashaPeriod;
  ad: DashaPeriod;
  pd: DashaPeriod;
  sd: SookshmaPeriod;
  ad_timeline: DashaPeriod[];
  pd_timeline: DashaPeriod[];
  sd_timeline: SookshmaPeriod[];
  activation_multiplier: number;
}

export interface PlanetDetail {
  sign: string;
  element: string;
  modality: string;
  dignity: string;
  degree_in_sign: number;
}

export interface YogaResult {
  yoga_name: string;
  category: string;
  status: string;
  static_strength: number;
  dynamic_strength: number | null;
  domains: string[];
  involved_planets: string[];
  cancellation_reason: string | null;
  chain_impact: number | null;
  dasha_multiplier: number | null;
  transit_multiplier: number | null;
  dasha_activation?: {
    past: { lord: string; level: string; start: string; end: string; duration_years: number }[];
    present: { lord: string; level: string; start: string; end: string; duration_years: number }[];
    future: { lord: string; level: string; start: string; end: string; duration_years: number }[];
    narrative: string;
    total_activation_periods: number;
  } | null;
}

export interface FeedbackEntry {
  evaluation_id: string;
  expert_id: string;
  domain: string;
  expert_agreement: boolean;
  expert_disagreement: boolean;
  missing_yoga: boolean;
  false_positive: boolean;
  false_negative: boolean;
  timing_issue: boolean;
  interpretation_issue: boolean;
  astronomical_issue: boolean;
  other: boolean;
  free_text: string;
}

export interface FixtureListResponse {
  count: number;
  fixtures: string[];
}

export interface ReportResponse {
  format: string;
  subject: string;
  evaluation_id: string;
  content: string;
  disclaimer: string;
}

export const api = {
  evaluateCustom: (data: {
    date: string;
    time: string;
    latitude: number;
    longitude: number;
    timezone: string;
    language?: string;
  }, apiKey: string) =>
    axios.post<EvaluationResponse>(`${API_BASE_URL}/api/v1/evaluate/custom`, data, {
      headers: { 'X-API-Key': apiKey },
    }),

  evaluateFixture: (data: { fixture_id: string }, apiKey: string) =>
    axios.post<EvaluationResponse>(`${API_BASE_URL}/api/v1/evaluate/fixture`, data, {
      headers: { 'X-API-Key': apiKey },
    }),

  getFixtures: (apiKey: string) =>
    axios.get<FixtureListResponse>(`${API_BASE_URL}/api/v1/fixtures`, {
      headers: { 'X-API-Key': apiKey },
    }),

  getReport: (fixtureId: string, format: 'markdown' | 'html', apiKey: string) =>
    axios.post<ReportResponse>(
      `${API_BASE_URL}/api/v1/report/fixture?format=${format}`,
      { fixture_id: fixtureId },
      { headers: { 'X-API-Key': apiKey } }
    ),

  submitFeedback: (data: FeedbackEntry, apiKey: string) =>
    axios.post<{ status: string; message: string; evaluation_id: string; entry_count: number }>(
      `${API_BASE_URL}/api/v1/feedback`,
      data,
      { headers: { 'X-API-Key': apiKey } }
    ),

  downloadPdfCustom: (data: {
    date: string;
    time: string;
    latitude: number;
    longitude: number;
    timezone: string;
  }, apiKey: string) =>
    axios.post(
      `${API_BASE_URL}/api/v1/report/custom/pdf`,
      data,
      {
        headers: { 'X-API-Key': apiKey },
        responseType: 'blob',
      }
    ),

  downloadPdfFixture: (fixtureId: string, apiKey: string) =>
    axios.post(
      `${API_BASE_URL}/api/v1/report/fixture/pdf`,
      { fixture_id: fixtureId },
      {
        headers: { 'X-API-Key': apiKey },
        responseType: 'blob',
      }
    ),

  downloadJatakamBook: (fixtureId: string, apiKey: string, format: 'pdf' | 'html' = 'pdf') =>
    axios.post(
      `${API_BASE_URL}/api/v1/report/jatakam-book?format=${format}`,
      { fixture_id: fixtureId },
      {
        headers: { 'X-API-Key': apiKey },
        responseType: 'blob',
      }
    ),

  // ── Advanced Charts API ─────────────────────────────────────────────────
  getShadbala: (fixtureId: string, apiKey: string) =>
    axios.get<ShadbalaResponse>(`${API_BASE_URL}/api/v1/advanced/shadbala`, {
      params: { fixture_id: fixtureId },
      headers: { 'X-API-Key': apiKey },
    }),

  getShadbalaByBirthData: (birthData: { date: string; time: string; latitude: number; longitude: number; timezone: string }, apiKey: string) =>
    axios.get<ShadbalaResponse>(`${API_BASE_URL}/api/v1/advanced/shadbala`, {
      params: birthData,
      headers: { 'X-API-Key': apiKey },
    }),

  getAshtakavarga: (fixtureId: string, apiKey: string) =>
    axios.get<AshtakavargaResponse>(`${API_BASE_URL}/api/v1/advanced/ashtakavarga`, {
      params: { fixture_id: fixtureId },
      headers: { 'X-API-Key': apiKey },
    }),

  getAshtakavargaByBirthData: (birthData: { date: string; time: string; latitude: number; longitude: number; timezone: string }, apiKey: string) =>
    axios.get<AshtakavargaResponse>(`${API_BASE_URL}/api/v1/advanced/ashtakavarga`, {
      params: birthData,
      headers: { 'X-API-Key': apiKey },
    }),

  getDivisionalChart: (fixtureId: string, division: string, apiKey: string) =>
    axios.get<DivisionalChartResponse>(`${API_BASE_URL}/api/v1/advanced/divisional`, {
      params: { fixture_id: fixtureId, division },
      headers: { 'X-API-Key': apiKey },
    }),

  getDivisionalChartByBirthData: (birthData: { date: string; time: string; latitude: number; longitude: number; timezone: string }, division: string, apiKey: string) =>
    axios.get<DivisionalChartResponse>(`${API_BASE_URL}/api/v1/advanced/divisional`, {
      params: { ...birthData, division },
      headers: { 'X-API-Key': apiKey },
    }),

  getRemedies: (fixtureId: string, apiKey: string) =>
    axios.get<RemedyResponse>(`${API_BASE_URL}/api/v1/advanced/remedies`, {
      params: { fixture_id: fixtureId },
      headers: { 'X-API-Key': apiKey },
    }),

  getRemediesByBirthData: (birthData: { date: string; time: string; latitude: number; longitude: number; timezone: string }, apiKey: string) =>
    axios.get<RemedyResponse>(`${API_BASE_URL}/api/v1/advanced/remedies`, {
      params: birthData,
      headers: { 'X-API-Key': apiKey },
    }),

  // ── Aspects API ───────────────────────────────────────────────────────
  getAspects: (fixtureId: string, apiKey: string) =>
    axios.get<AspectMatrixResult>(`${API_BASE_URL}/api/v1/advanced/aspects`, {
      params: { fixture_id: fixtureId },
      headers: { 'X-API-Key': apiKey },
    }),

  getAspectsByBirthData: (birthData: { date: string; time: string; latitude: number; longitude: number; timezone: string }, apiKey: string) =>
    axios.get<AspectMatrixResult>(`${API_BASE_URL}/api/v1/advanced/aspects`, {
      params: birthData,
      headers: { 'X-API-Key': apiKey },
    }),

  // ── Compatibility API ───────────────────────────────────────────────────
  calculateCompatibility: (data: { person_a: { nakshatra: string }; person_b: { nakshatra: string } }, apiKey: string) =>
    axios.post<CompatibilityResponse>(`${API_BASE_URL}/api/v1/compatibility/match`, data, {
      headers: { 'X-API-Key': apiKey },
    }),

  // ── Predictions API ───────────────────────────────────────────────────
  getGocharTransits: (fixtureId: string, apiKey: string) =>
    axios.get<GocharTransitResult>(`${API_BASE_URL}/api/v1/predictions/gochar-transit`, {
      params: { fixture_id: fixtureId },
      headers: { 'X-API-Key': apiKey },
    }),

  getGocharTransitsByBirthData: (birthData: { date: string; time: string; latitude: number; longitude: number; timezone: string }, apiKey: string) =>
    axios.get<GocharTransitResult>(`${API_BASE_URL}/api/v1/predictions/gochar-transit`, {
      params: birthData,
      headers: { 'X-API-Key': apiKey },
    }),

  // ── Gochar Aspects API ───────────────────────────────────────────────
  getGocharAspects: (fixtureId: string, apiKey: string) =>
    axios.get<AspectMatrixResult>(`${API_BASE_URL}/api/v1/advanced/gochar-aspects`, {
      params: { fixture_id: fixtureId },
      headers: { 'X-API-Key': apiKey },
    }),

  getGocharAspectsByBirthData: (birthData: { date: string; time: string; latitude: number; longitude: number; timezone: string }, apiKey: string) =>
    axios.get<AspectMatrixResult>(`${API_BASE_URL}/api/v1/advanced/gochar-aspects`, {
      params: birthData,
      headers: { 'X-API-Key': apiKey },
    }),

  getRelationshipAnalysis: (fixtureId: string, apiKey: string) =>
    axios.get<RelationshipAnalysisResult>(`${API_BASE_URL}/api/v1/predictions/relationship`, {
      params: { fixture_id: fixtureId },
      headers: { 'X-API-Key': apiKey },
    }),

  getRelationshipAnalysisByBirthData: (birthData: { date: string; time: string; latitude: number; longitude: number; timezone: string }, apiKey: string) =>
    axios.get<RelationshipAnalysisResult>(`${API_BASE_URL}/api/v1/predictions/relationship`, {
      params: birthData,
      headers: { 'X-API-Key': apiKey },
    }),

  // ── Deep Dasha API ─────────────────────────────────────────────────────
  getDeepDasha: (fixtureId: string, apiKey: string) =>
    axios.get<DeepDashaResult>(`${API_BASE_URL}/api/v1/advanced/dasha`, {
      params: { fixture_id: fixtureId },
      headers: { 'X-API-Key': apiKey },
    }),

  getDeepDashaByBirthData: (birthData: { date: string; time: string; latitude: number; longitude: number; timezone: string }, apiKey: string) =>
    axios.get<DeepDashaResult>(`${API_BASE_URL}/api/v1/advanced/dasha`, {
      params: birthData,
      headers: { 'X-API-Key': apiKey },
    }),

  // ── Planetary States API ───────────────────────────────────────────────
  getPlanetaryStates: (apiKey: string) =>
    axios.get<Record<string, PlanetaryStateInfo>>(`${API_BASE_URL}/api/v1/advanced/planetary-states`, {
      headers: { 'X-API-Key': apiKey },
    }),

  getPlanetaryStatesByBirthData: (birthData: { date: string; time: string; latitude: number; longitude: number; timezone: string }, apiKey: string) =>
    axios.get<Record<string, PlanetaryStateInfo>>(`${API_BASE_URL}/api/v1/advanced/planetary-states`, {
      params: birthData,
      headers: { 'X-API-Key': apiKey },
    }),

  // ── Nakshatra Exchange API ──────────────────────────────────────────────
  getNakshatraExchanges: (fixtureId: string, apiKey: string) =>
    axios.get<NakshatraExchangeResult>(`${API_BASE_URL}/api/v1/advanced/nakshatra-exchanges`, {
      params: { fixture_id: fixtureId },
      headers: { 'X-API-Key': apiKey },
    }),

  getNakshatraExchangesByBirthData: (birthData: { date: string; time: string; latitude: number; longitude: number; timezone: string }, apiKey: string) =>
    axios.get<NakshatraExchangeResult>(`${API_BASE_URL}/api/v1/advanced/nakshatra-exchanges`, {
      params: birthData,
      headers: { 'X-API-Key': apiKey },
    }),

  // ── Day-by-Day Transit API ──────────────────────────────────────────────
  getDayByDayTransits: (fixtureId: string, days?: number, apiKey: string = '') =>
    axios.get<DailyTransitAspect[]>(`${API_BASE_URL}/api/v1/predictions/day-by-day-transit`, {
      params: { fixture_id: fixtureId, ...(days ? { days } : {}) },
      headers: { 'X-API-Key': apiKey },
    }),

  getDayByDayTransitsByBirthData: (birthData: { date: string; time: string; latitude: number; longitude: number; timezone: string }, days: number = 14, apiKey: string = '') =>
    axios.get<DailyTransitAspect[]>(`${API_BASE_URL}/api/v1/predictions/day-by-day-transit`, {
      params: { ...birthData, days },
      headers: { 'X-API-Key': apiKey },
    }),

  // ── JRE Analysis Endpoint ─────────────────────────────────────────────
  analyzeChart: (payload: ChartRequestPayload) =>
    axios.post<JREAnalysisResponse>(`${API_BASE_URL}/api/v1/analyze`, payload),

  // ── Numerology API ─────────────────────────────────────────────────────
  calculateNumerology: (data: { birth_date: string; full_name: string }, apiKey: string) =>
    axios.post<NumerologyResponse>(`${API_BASE_URL}/api/v1/integrations/numerology`, data, {
      headers: { 'X-API-Key': apiKey },
    }),

  healthCheck: () =>
    axios.get<{ status: string; version: string }>(`${API_BASE_URL}/api/v1/health`),
};

// ── Advanced Chart Response Types ─────────────────────────────────────────
export interface PlanetStrength {
  planet: string;
  sthana_bala: number;
  dig_bala: number;
  kala_bala: number;
  chesta_bala: number;
  naisargika_bala: number;
  drik_bala: number;
  total_rupas: number;
  total_virupas: number;
  is_strong: boolean;
}

export interface ShadbalaResponse {
  planets: Record<string, PlanetStrength>;
  average_strength: number;
  strongest_planet: string;
  weakest_planet: string;
}

export interface BAVData {
  planet: string;
  bindus: Record<string, number>;
  total_bindus: number;
}

export interface AshtakavargaResponse {
  bav: Record<string, BAVData>;
  sav: Record<string, number>;
  strongest_house: number;
  weakest_house: number;
  average_sav: number;
}

export interface DivisionalPlanetData {
  planet: string;
  natal_longitude: number;
  divisional_longitude: number;
  rashi: string;
  rashi_name: string;
  degree_in_sign: number;
  house: number;
}

export interface DivisionalChartResponse {
  division: number;
  name: string;
  description: string;
  lagna: string;
  lagna_name: string;
  vargottama_planets: string[];
  planets: Record<string, DivisionalPlanetData>;
}

// ── Remedies Response Types ───────────────────────────────────────────────
export interface RemedyMantra {
  moola_mantra: string;
  gayatri: string;
  count: number;
  best_day: string;
  best_time: string;
  duration_weeks?: number;
}

export interface RemedyGemstone {
  primary_stone: string;
  alternate_stone?: string;
  weight_carat: number;
  metal: string;
  finger: string;
  day_to_wear: string;
  min_weight_carat?: number;
  certification?: string;
}

export interface RemedyTemple {
  deity: string;
  temple_name?: string;
  facing_direction: string;
  offering: string;
  prasad?: string;
}

export interface RemedyCharity {
  item_to_donate: string;
  recipient: string;
  day: string;
  quantity?: string;
  specific_donation?: string;
}

export interface RemedyColorTherapy {
  favorable_colors: string[];
  colors_to_avoid: string[];
  lucky_color?: string;
}

export interface RemedyFasting {
  day: string;
  food_to_avoid: string[];
  allowed_foods: string[];
  duration?: string;
}

export interface RemedyLifestyle {
  exercise?: string;
  meditation?: string;
  behavior?: string;
}

export interface PlanetRemedy {
  planet: string;
  affliction: string;
  severity: string;
  mantra: RemedyMantra;
  gemstone: RemedyGemstone;
  temple: RemedyTemple;
  charity: RemedyCharity;
  color_therapy: RemedyColorTherapy;
  fasting: RemedyFasting;
  lifestyle: RemedyLifestyle;
}

export interface DoshaRemedy {
  dosha: string;
  severity: string;
  description: string;
  mantra: string;
  charity: string;
  temple: string;
  remedy: string;
}

export interface RemedyResponse {
  afflicted_planets: PlanetRemedy[];
  doshas: DoshaRemedy[];
  general_remedies: {
    daily_practice?: string[];
    weekly_practice?: string[];
    monthly_practice?: string[];
  };
  overall_assessment: string;
  disclaimer: string;
}

// ── Compatibility Response Types ──────────────────────────────────────────
export interface KootaResult {
  name: string;
  score: number;
  max_points: number;
  description: string;
}

export interface CompatibilityResponse {
  person_a_nakshatra: string;
  person_b_nakshatra: string;
  total_score: number;
  max_score: number;
  kootas: KootaResult[];
  assessment: string;
  assessment_details: string;
  has_nadi_dosha: boolean;
  has_bhakoot_dosha: boolean;
}

// ── Numerology Response Types ─────────────────────────────────────────────
export interface NumerologyNumber {
  number: number;
  meaning: string;
}

export interface NumerologyResponse {
  birth_date: string;
  full_name: string;
  life_path: NumerologyNumber;
  destiny: NumerologyNumber;
  soul_urge: NumerologyNumber;
}

// ── Planetary State Types ───────────────────────────────────────────────
export interface PlanetaryStateInfo {
  planet: string;
  longitude: number;
  speed: number;
  state: string;  // "R", "D", "C", "S", "F", "L"
  state_label: string;
  is_retrograde: boolean;
  is_combust: boolean;
  is_stationary: boolean;
  speed_class: string;
  degrees_from_sun: number;
}

// ── Nakshatra Exchange Types ─────────────────────────────────────────────
export interface NakshatraInfo {
  planet: string;
  longitude: number;
  sign: string;
  degree_in_sign: number;
  nakshatra: string;
  nakshatra_name: string;
  nakshatra_lord: string;
  pada: number;
}

export interface NakshatraExchange {
  planet_a: string;
  planet_a_nakshatra: string;
  planet_a_nakshatra_lord: string;
  planet_b: string;
  planet_b_nakshatra: string;
  planet_b_nakshatra_lord: string;
  reading: string;
  significance: string;
  strength: string;
}

export interface TransitNakshatraExchange {
  date: string;
  transit_planet: string;
  transit_nakshatra: string;
  transit_nakshatra_lord: string;
  natal_planet: string;
  natal_nakshatra: string;
  natal_nakshatra_lord: string;
  reading: string;
  strength: string;
}

export interface NakshatraExchangeResult {
  natal_nakshatras: Record<string, NakshatraInfo>;
  transit_nakshatras: Record<string, NakshatraInfo>;
  natal_exchanges: NakshatraExchange[];
  transit_exchanges: NakshatraExchange[];
  nakshatra_readings: Record<string, string>;
  transit_natal_exchanges: TransitNakshatraExchange[];
}

// ── Daily Transit Aspect Types ───────────────────────────────────────────
export interface DailyTransitAspect {
  date: string;
  transit_planet: string;
  transit_state: string;
  target_type: string;
  target: string;
  aspect_type: string;
  prediction: string;
  severity: string;
  orb_degrees: number;
}

// ── Gochar Transit Prediction Types ───────────────────────────────────────
export interface GocharTransitPrediction {
  transit_planet: string;
  transit_sign: string;
  transit_house: number;
  aspect_type: string | null;
  target_planet: string | null;
  target_sign: string | null;
  target_house: number | null;
  prediction: string;
  category: string;
  severity: string;
}

export interface GocharTransitResult {
  lagna: string;
  moon_sign: string;
  transit_positions: Record<string, { sign: string; degree: number }>;
  predictions: GocharTransitPrediction[];
  transit_to_transit_aspects: GocharTransitPrediction[];
  summary_by_planet: Record<string, GocharTransitPrediction[]>;
  overall_assessment: string;
}

// ── Relationship Analysis Types ───────────────────────────────────────────
export interface RelationshipInsight {
  category: string;
  planet: string;
  house: number | null;
  sign: string | null;
  analysis_type: string;
  title: string;
  description: string;
  classical_reference: string;
  strength_indicator: string;
  specific_combinations: string[];
}

export interface RelationshipAnalysisResult {
  lagna: string;
  venus_analysis: RelationshipInsight[];
  mars_analysis: RelationshipInsight[];
  seventh_lord_analysis: RelationshipInsight[];
  rahu_ketu_analysis: RelationshipInsight[];
  classical_combinations: RelationshipInsight[];
  overall_assessment: string;
  intimacy_profile: string;
  relationship_strength: string;
}
