"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { Capacitor } from "@capacitor/core";
import { isNativeIOS, purchasePackageById, restorePurchases } from "@/lib/native";

export default function PaywallPage() {
  const router = useRouter();
  const [plan, setPlan] = useState<"annual" | "monthly">("annual");
  const [purchasing, setPurchasing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubscribe = async () => {
    setError(null);
    // Native iOS: trigger Apple's StoreKit purchase flow via RevenueCat.
    if (isNativeIOS()) {
      setPurchasing(true);
      const packageId = plan === "annual" ? "$rc_annual" : "$rc_monthly";
      const result = await purchasePackageById(packageId);
      setPurchasing(false);
      if (result.success && result.hasPro) {
        // Purchase complete — back to where they came from.
        router.push("/");
        return;
      }
      if (result.error && result.error !== "cancelled") {
        setError(result.error);
      }
      return;
    }

    // Web browser: Apple requires IAP for digital subscriptions, so we can't
    // sell on the web. Direct users to the iOS app.
    //
    // TEMPORARY DIAGNOSTIC (remove after we confirm native detection works).
    // If this alert fires inside the iOS app, screenshot it and send back so
    // we can see which detection clause failed.
    const ua = typeof window !== "undefined" ? window.navigator.userAgent : "(no window)";
    const isNative = Capacitor.isNativePlatform();
    const platform = Capacitor.getPlatform();
    const hasFightZMarker = ua.includes("FightZ-iOS");
    alert(
      "Subscriptions require the FightZ iOS app.\n\n" +
        "--- DEBUG (temporary) ---\n" +
        `Capacitor.isNativePlatform: ${isNative}\n` +
        `Capacitor.getPlatform: ${platform}\n` +
        `UA contains FightZ-iOS: ${hasFightZMarker}\n\n` +
        `UA: ${ua.slice(0, 200)}`
    );
  };

  const handleRestore = async () => {
    if (!isNativeIOS()) return;
    setError(null);
    setPurchasing(true);
    const result = await restorePurchases();
    setPurchasing(false);
    if (result.success && result.hasPro) {
      router.push("/");
    } else if (result.error) {
      setError(result.error);
    } else {
      setError("No prior purchases found.");
    }
  };

  return (
    <div className="max-w-2xl mx-auto py-8 sm:py-12">
      <div className="text-center mb-8">
        <h1 className="text-3xl sm:text-4xl font-black text-white mb-3">
          Unlock the full FightZ experience
        </h1>
        <p className="text-ufc-muted text-sm sm:text-base max-w-xl mx-auto">
          Specialist-agent fight analysis, 10-axis fighter ratings, head-to-head
          breakdowns, and calculated odds for every fight on every UFC card.
          Start with a 7-day free trial.
        </p>
      </div>

      {/* Pricing toggle */}
      <div className="flex justify-center mb-6">
        <div className="inline-flex rounded-full border border-ufc-border p-1 bg-black/40">
          <button
            onClick={() => setPlan("annual")}
            className={`text-sm font-bold px-5 py-2 rounded-full transition-colors min-h-[44px] ${
              plan === "annual"
                ? "bg-ufc-red text-white"
                : "text-ufc-muted hover:text-white"
            }`}
          >
            Annual
          </button>
          <button
            onClick={() => setPlan("monthly")}
            className={`text-sm font-bold px-5 py-2 rounded-full transition-colors min-h-[44px] ${
              plan === "monthly"
                ? "bg-ufc-red text-white"
                : "text-ufc-muted hover:text-white"
            }`}
          >
            Monthly
          </button>
        </div>
      </div>

      {/* Plan card */}
      <div
        className="rounded-2xl p-6 sm:p-8 mb-6 shadow-2xl"
        style={{
          background: "linear-gradient(135deg, #1a1a1a 0%, #0d0d0d 100%)",
          border: "2px solid #dc0000",
        }}
      >
        {plan === "annual" ? (
          <div className="text-center">
            <div className="inline-block bg-ufc-red text-white text-[10px] font-black tracking-widest uppercase px-3 py-1 rounded-full mb-3">
              Save 22%
            </div>
            <div className="text-5xl sm:text-6xl font-black text-white mb-1">
              $74.99
              <span className="text-lg sm:text-xl text-ufc-muted font-bold ml-1">
                /year
              </span>
            </div>
            <div className="text-sm text-ufc-muted mb-6">
              Billed annually after your 7-day free trial. Works out to ~$6.25/mo.
            </div>
          </div>
        ) : (
          <div className="text-center">
            <div className="text-5xl sm:text-6xl font-black text-white mb-1">
              $7.99
              <span className="text-lg sm:text-xl text-ufc-muted font-bold ml-1">
                /month
              </span>
            </div>
            <div className="text-sm text-ufc-muted mb-6">
              Billed monthly after your 7-day free trial. Cancel anytime.
            </div>
          </div>
        )}

        <button
          onClick={handleSubscribe}
          disabled={purchasing}
          className="w-full bg-ufc-red hover:bg-ufc-red-dark disabled:opacity-60 disabled:cursor-not-allowed text-white font-black text-base sm:text-lg py-4 rounded-xl transition-colors min-h-[56px]"
        >
          {purchasing ? "Processing..." : "Start 7-Day Free Trial"}
        </button>

        {error && (
          <div className="mt-3 px-3 py-2 rounded bg-ufc-red/15 border border-ufc-red/40 text-ufc-red text-xs text-center">
            {error}
          </div>
        )}

        <p className="text-[11px] text-ufc-muted text-center mt-3 leading-relaxed">
          Free for 7 days, then{" "}
          {plan === "annual" ? "$74.99 billed annually" : "$7.99 billed monthly"}.
          Cancel anytime in your Apple ID settings before the trial ends to avoid
          charges. Subscription auto-renews unless cancelled at least 24 hours
          before the end of the current period.
        </p>

        {/* Apple requires apps with IAP to offer a "Restore Purchases" path.
            Shown only inside the iOS app — useless in the web browser. */}
        {isNativeIOS() && (
          <button
            onClick={handleRestore}
            disabled={purchasing}
            className="block w-full text-center text-xs text-ufc-muted hover:text-white underline-offset-4 hover:underline mt-3 py-2 min-h-[44px] transition-colors"
          >
            Restore previous purchases
          </button>
        )}
      </div>

      {/* Feature list */}
      <div className="rounded-xl bg-black/40 border border-ufc-border p-5 sm:p-6 mb-8">
        <h2 className="text-sm font-black tracking-widest text-ufc-red uppercase mb-4">
          What&apos;s included
        </h2>
        <ul className="space-y-3 text-sm sm:text-base text-white/90">
          <li className="flex gap-3">
            <span className="text-ufc-red font-black">✓</span>
            <span>
              <strong className="text-white">Specialist agent reports</strong> —
              10 expert agents (5 offense + 5 defense) score every fighter
              across striking, wrestling, takedowns, grappling, and submissions.
            </span>
          </li>
          <li className="flex gap-3">
            <span className="text-ufc-red font-black">✓</span>
            <span>
              <strong className="text-white">10-axis fighter decagons</strong>{" "}
              — instantly compare two fighters across every domain on a single
              chart.
            </span>
          </li>
          <li className="flex gap-3">
            <span className="text-ufc-red font-black">✓</span>
            <span>
              <strong className="text-white">Head-to-head breakdowns</strong> —
              fight-flow predictions and the most likely paths to victory for
              each fighter.
            </span>
          </li>
          <li className="flex gap-3">
            <span className="text-ufc-red font-black">✓</span>
            <span>
              <strong className="text-white">Calculated odds</strong> — our
              independent moneyline odds for the favorite, useful as a benchmark
              against any sportsbook&apos;s line.
            </span>
          </li>
          <li className="flex gap-3">
            <span className="text-ufc-red font-black">✓</span>
            <span>
              <strong className="text-white">Refreshed three times a week</strong>{" "}
              — fresh analysis Monday, Wednesday, and Friday so you always have
              the latest read going into fight night.
            </span>
          </li>
        </ul>
      </div>

      <p className="text-center text-xs text-ufc-muted">
        <Link href="/terms" className="hover:text-white underline">
          Terms
        </Link>{" "}
        ·{" "}
        <Link href="/privacy" className="hover:text-white underline">
          Privacy
        </Link>{" "}
        ·{" "}
        <Link href="/" className="hover:text-white underline">
          Back to fight card
        </Link>
      </p>
    </div>
  );
}
