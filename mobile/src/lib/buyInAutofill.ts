/**
 * Buy-in autofill calculation helpers.
 *
 * These are pure functions with no React dependencies so they can be
 * unit-tested independently of the component.
 *
 * Rounding contract (from PHASE2_PRODUCT_SPEC.md Feature 5):
 *   cash  → chips : Math.floor(cash / rate)   — never give more chips than paid for
 *   chips → cash  : chips * rate              — straightforward multiply, no rounding
 */

/**
 * Calculate the chips amount from a cash amount.
 *
 * @param cash          Cash value entered by the dealer (must be > 0)
 * @param chipCashRate  Rate: how much cash one chip is worth (must be > 0)
 * @returns             Whole number of chips (floored)
 */
export function cashToChips(cash: number, chipCashRate: number): number {
  return Math.floor(cash / chipCashRate);
}

/**
 * Calculate the cash amount from a chips amount.
 *
 * @param chips         Chip count entered by the dealer (must be >= 0)
 * @param chipCashRate  Rate: how much cash one chip is worth (must be > 0)
 * @returns             Cash amount (not rounded — multiply is exact for typical rates)
 */
export function chipsToCash(chips: number, chipCashRate: number): number {
  return chips * chipCashRate;
}
