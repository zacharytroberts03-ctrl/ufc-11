/**
 * Bridge between the FightZ website and the native iOS Capacitor wrapper.
 *
 * When the site runs in a regular browser, every export here either no-ops or
 * returns "not native". When it runs inside the Capacitor iOS shell, the
 * RevenueCat Capacitor plugin is available and we can trigger native StoreKit
 * purchases via Apple's IAP flow.
 *
 * Architecture choice:
 * - Clerk's user.id is the single identity. RevenueCat tracks subscriptions
 *   against that ID via Purchases.logIn(clerkUserId) on app launch.
 * - The server-side entitlement check in lib/access.ts queries RevenueCat with
 *   the same user.id, so subscriptions made on iOS are visible to the web
 *   paywall gate without extra plumbing.
 *
 * Apple in-app purchase ID for the public SDK key. The key is a "public" key
 * by design — RevenueCat distinguishes it from the server-only sk_... secret
 * and it's safe to include in the JS bundle.
 */

import { Capacitor } from "@capacitor/core";

// NEXT_PUBLIC_ prefix exposes the value to the client bundle (Capacitor needs
// it; the secret sk_... key is server-only and stays in REVENUECAT_SECRET_KEY).
const REVENUECAT_IOS_PUBLIC_KEY = process.env.NEXT_PUBLIC_REVENUECAT_IOS_KEY ?? "";

export function isNativeIOS(): boolean {
  return Capacitor.isNativePlatform() && Capacitor.getPlatform() === "ios";
}

let _configured = false;

/** Initialize the RevenueCat SDK. Idempotent — safe to call repeatedly.
 *  Pass the signed-in Clerk user.id once they sign in so RevenueCat can
 *  associate purchases with the right user across devices. */
export async function initRevenueCat(clerkUserId?: string | null): Promise<void> {
  if (!isNativeIOS()) return;
  if (!REVENUECAT_IOS_PUBLIC_KEY) {
    console.warn("[native] NEXT_PUBLIC_REVENUECAT_IOS_KEY is not set — IAP will fail");
    return;
  }

  // Dynamic import so the web bundle doesn't pull native code that throws in browser.
  const { Purchases, LOG_LEVEL } = await import("@revenuecat/purchases-capacitor");

  if (!_configured) {
    await Purchases.setLogLevel({ level: LOG_LEVEL.WARN });
    await Purchases.configure({
      apiKey: REVENUECAT_IOS_PUBLIC_KEY,
      appUserID: clerkUserId ?? null,
    });
    _configured = true;
  } else if (clerkUserId) {
    // Already configured but user just signed in — switch identity.
    await Purchases.logIn({ appUserID: clerkUserId });
  }
}

export interface PurchaseablePackage {
  identifier: string; // e.g. "$rc_monthly" or "$rc_annual"
  priceString: string; // e.g. "$7.99"
  durationLabel: string; // "Monthly" / "Annual"
}

/** Pull the current offering's packages from RevenueCat. Returns [] if not on iOS
 *  or if the offering hasn't been configured yet. */
export async function getOfferings(): Promise<PurchaseablePackage[]> {
  if (!isNativeIOS()) return [];
  const { Purchases } = await import("@revenuecat/purchases-capacitor");
  try {
    const result = await Purchases.getOfferings();
    const current = result.current;
    if (!current) return [];
    return current.availablePackages.map((p) => ({
      identifier: p.identifier,
      priceString: p.product.priceString,
      durationLabel:
        p.identifier === "$rc_annual"
          ? "Annual"
          : p.identifier === "$rc_monthly"
          ? "Monthly"
          : p.identifier,
    }));
  } catch (e) {
    console.error("[native] getOfferings failed", e);
    return [];
  }
}

export interface PurchaseResult {
  success: boolean;
  hasPro: boolean;
  error?: string;
}

/** Trigger Apple's native StoreKit purchase flow for a specific package.
 *  Returns success=true and hasPro=true when the user owns the `pro` entitlement
 *  after the purchase completes (Apple may show its own confirmation modals). */
export async function purchasePackageById(packageId: string): Promise<PurchaseResult> {
  if (!isNativeIOS()) {
    return { success: false, hasPro: false, error: "Not running in native iOS" };
  }
  const { Purchases } = await import("@revenuecat/purchases-capacitor");
  try {
    const offerings = await Purchases.getOfferings();
    const pkg = offerings.current?.availablePackages.find((p) => p.identifier === packageId);
    if (!pkg) {
      return { success: false, hasPro: false, error: `Package ${packageId} not found` };
    }
    const result = await Purchases.purchasePackage({ aPackage: pkg });
    const hasPro = Boolean(result.customerInfo?.entitlements?.active?.pro);
    return { success: true, hasPro };
  } catch (e: unknown) {
    // User-cancelled is a normal flow, not an error worth surfacing as a toast.
    const errMsg = e instanceof Error ? e.message : String(e);
    if (errMsg.toLowerCase().includes("cancel")) {
      return { success: false, hasPro: false, error: "cancelled" };
    }
    return { success: false, hasPro: false, error: errMsg };
  }
}

/** Restore any prior purchases for the current user — required by Apple
 *  (apps with IAP must offer a "Restore Purchases" button). */
export async function restorePurchases(): Promise<PurchaseResult> {
  if (!isNativeIOS()) {
    return { success: false, hasPro: false, error: "Not running in native iOS" };
  }
  const { Purchases } = await import("@revenuecat/purchases-capacitor");
  try {
    const result = await Purchases.restorePurchases();
    const hasPro = Boolean(result.customerInfo?.entitlements?.active?.pro);
    return { success: true, hasPro };
  } catch (e: unknown) {
    return { success: false, hasPro: false, error: e instanceof Error ? e.message : String(e) };
  }
}
