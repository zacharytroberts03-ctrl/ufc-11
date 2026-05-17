import type { CapacitorConfig } from "@capacitor/cli";

/**
 * Capacitor wraps the fightz.app website in a native iOS shell so the app can
 * be distributed via the App Store. The wrapper loads the live site at runtime
 * (server.url) rather than bundling the web assets — fights update naturally
 * whenever the refresh cron pushes new JSON, no app-store update needed.
 *
 * In-app purchases (the FightZ Pro subscription) flow through the RevenueCat
 * Capacitor plugin (@revenuecat/purchases-capacitor) which calls Apple's native
 * StoreKit. See frontend/lib/native.ts for the bridge.
 *
 * Bundle ID `com.fightz.app` MUST match the App ID registered in the Apple
 * Developer portal and the Bundle ID set on the FightZ app in App Store Connect.
 */
const config: CapacitorConfig = {
  appId: "com.fightz.app",
  appName: "FightZ",
  // webDir is required by Capacitor config even when we use a remote URL.
  // Points at the Next.js production build output as a defensive fallback.
  webDir: ".next",
  server: {
    url: "https://fightz.app",
    cleartext: false,
  },
  ios: {
    contentInset: "always",
    // Marker the iOS shell appends to navigator.userAgent. lib/native.ts
    // isNativeIOS() looks for it as a fallback when Capacitor's bridge JS
    // hasn't injected window.Capacitor (CSP issues, race conditions, or
    // @capacitor/core version drift between the deployed JS and the native
    // shell). UA detection doesn't depend on the bridge.
    appendUserAgent: "FightZ-iOS",
  },
};

export default config;
