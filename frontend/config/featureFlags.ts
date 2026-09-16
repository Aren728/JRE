/**
 * Feature Flags Configuration
 *
 * Manage experimental and beta features via environment variables.
 * All flags default to false/disabled unless explicitly enabled.
 *
 * Environment Variables:
 * - NEXT_PUBLIC_ENABLE_EXPERIMENTAL_VARGAS: Enable D2, D3, D7, D10, D12, D16, D24, D27, D30, D40, D45, D60 divisional charts
 * - NEXT_PUBLIC_ENABLE_ADVANCED_YOGA: Enable advanced yoga filters and modifiers
 */

export interface FeatureFlags {
  /** Enable experimental varga (divisional chart) filters and views */
  enableExperimentalVargas: boolean;
  /** Enable advanced yoga filtering and modifier pipeline UI */
  enableAdvancedYogaFilters: boolean;
  /** Enable PDF report export functionality */
  enablePdfExport: boolean;
  /** Enable beta feedback modal for expert feedback collection */
  enableBetaFeedbackModal: boolean;
}

export const featureFlags: FeatureFlags = {
  enableExperimentalVargas:
    process.env.NEXT_PUBLIC_ENABLE_EXPERIMENTAL_VARGAS === 'true',
  enableAdvancedYogaFilters:
    process.env.NEXT_PUBLIC_ENABLE_ADVANCED_YOGA === 'true',
  enablePdfExport: true,
  enableBetaFeedbackModal: true,
};

// Helper to check if a feature is enabled
export function isFeatureEnabled(flag: keyof FeatureFlags): boolean {
  return featureFlags[flag];
}


