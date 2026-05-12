/**
 * Server-side access check for paid fight content.
 *
 * Returns access info for the currently signed-in Clerk user against a specific
 * fight. Used by /api/access and by Server Components that need to decide
 * whether to render full content or a locked teaser.
 *
 * Access truth table:
 *   user is admin (Clerk publicMetadata.role === "admin")  → "admin"
 *   fight has free_tier flag                                → "free_tier"
 *   user has RevenueCat `pro` entitlement                   → "subscriber"
 *   otherwise                                               → "locked"
 *
 * The RevenueCat check uses the server-only REVENUECAT_SECRET_KEY (V1 REST API).
 * In our model the Clerk user.id IS the RevenueCat app_user_id — the iOS app
 * (Capacitor, Step 7) calls Purchases.logIn(clerkUserId) right after sign-in so
 * subscriptions are tracked against that same identifier.
 */

import type { Fight } from "./types";

const REVENUECAT_API_BASE = "https://api.revenuecat.com/v1";

export type AccessReason = "admin" | "free_tier" | "subscriber" | "locked" | "anonymous";

export interface AccessResult {
  hasAccess: boolean;
  reason: AccessReason;
}

/** Calls the RevenueCat V1 subscriber endpoint and returns true if the user
 *  currently has an active `pro` entitlement. Network failures return false —
 *  better to fail closed (show paywall) than to leak content. */
async function hasRevenueCatProEntitlement(userId: string): Promise<boolean> {
  const secret = process.env.REVENUECAT_SECRET_KEY;
  if (!secret) {
    // No secret configured (e.g. during local dev without the env var).
    // Fail closed so we don't silently grant access in production if the
    // env var ever goes missing.
    return false;
  }

  try {
    const res = await fetch(
      `${REVENUECAT_API_BASE}/subscribers/${encodeURIComponent(userId)}`,
      {
        method: "GET",
        headers: {
          Authorization: `Bearer ${secret}`,
          Accept: "application/json",
        },
        // Don't cache — entitlement status can flip mid-session (e.g. user
        // cancels in iOS Settings).
        cache: "no-store",
      }
    );

    if (res.status === 404) {
      // RevenueCat 404 = no subscriber record exists for that user yet
      // (they've never purchased on any platform). Treat as no access.
      return false;
    }
    if (!res.ok) return false;

    const data = await res.json();
    const proEntitlement = data?.subscriber?.entitlements?.pro;
    if (!proEntitlement) return false;

    // expires_date null = lifetime; otherwise must be in the future.
    const expiresDate = proEntitlement.expires_date;
    if (expiresDate === null || expiresDate === undefined) return true;
    return new Date(expiresDate).getTime() > Date.now();
  } catch {
    return false;
  }
}

interface CheckArgs {
  /** Clerk user.id; null if anonymous. */
  userId: string | null;
  /** Clerk publicMetadata for the user — read by the caller via auth() / currentUser(). */
  publicMetadata?: { role?: string } | null;
  /** The Fight tile data — needs the free_tier flag to short-circuit on free fights. */
  fight: Pick<Fight, "free_tier"> | null | undefined;
}

/** Resolve access for a (user, fight) pair. */
export async function checkFightAccess({
  userId,
  publicMetadata,
  fight,
}: CheckArgs): Promise<AccessResult> {
  // Free-tier fights are open to any signed-in user (still need an account
  // per the sign-up wall, but no subscription required).
  if (fight?.free_tier) {
    return userId
      ? { hasAccess: true, reason: "free_tier" }
      : { hasAccess: false, reason: "anonymous" };
  }

  if (!userId) {
    return { hasAccess: false, reason: "anonymous" };
  }

  // Admin role bypass — for the project owner and Apple App Store reviewers.
  if (publicMetadata?.role === "admin") {
    return { hasAccess: true, reason: "admin" };
  }

  // RevenueCat entitlement check.
  const isSubscriber = await hasRevenueCatProEntitlement(userId);
  if (isSubscriber) {
    return { hasAccess: true, reason: "subscriber" };
  }

  return { hasAccess: false, reason: "locked" };
}
