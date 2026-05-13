"use client";

import { useUser } from "@clerk/nextjs";
import { useEffect } from "react";
import { initRevenueCat, isNativeIOS } from "@/lib/native";

/**
 * Initialize RevenueCat once Clerk has loaded the user's identity. Runs only
 * inside the native iOS Capacitor wrapper — no-ops in the web browser.
 *
 * When a Clerk user signs in, RevenueCat's appUserID is updated to match so
 * that any iOS purchase is tracked against the same identifier the web paywall
 * gate (lib/access.ts) looks up server-side.
 */
export default function RevenueCatBoot() {
  const { isLoaded, user } = useUser();

  useEffect(() => {
    if (!isNativeIOS() || !isLoaded) return;
    initRevenueCat(user?.id ?? null).catch((e) =>
      console.error("[RevenueCatBoot] init failed", e)
    );
  }, [isLoaded, user?.id]);

  return null;
}
