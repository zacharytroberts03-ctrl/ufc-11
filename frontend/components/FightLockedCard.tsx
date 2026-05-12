"use client";

import Link from "next/link";

interface Props {
  fighter1: string;
  fighter2: string;
  weightClass?: string;
}

/** Inline paywall card shown on a fight detail page when the user is signed in
 *  but lacks the `pro` entitlement (and the fight isn't free_tier). Shows just
 *  enough teaser to remind users what they're missing, plus a primary CTA into
 *  /paywall. The /fight/... middleware already enforces sign-in, so this card
 *  only renders for signed-in non-subscribers. */
export default function FightLockedCard({ fighter1, fighter2, weightClass }: Props) {
  return (
    <div
      className="rounded-xl p-8 sm:p-12 my-8 shadow-2xl text-center"
      style={{
        background: "linear-gradient(135deg, #1a1a1a 0%, #0d0d0d 100%)",
        border: "2px solid #dc0000",
      }}
    >
      <div className="text-6xl mb-4">🔒</div>
      <h2 className="text-2xl sm:text-3xl font-black text-white mb-2">
        Unlock the full breakdown
      </h2>
      <p className="text-base sm:text-lg text-ufc-muted mb-1">
        {fighter1} <span className="text-ufc-red">vs</span> {fighter2}
      </p>
      {weightClass && weightClass !== "N/A" && (
        <p className="text-xs uppercase tracking-widest text-ufc-muted mb-6">
          {weightClass}
        </p>
      )}
      <ul className="text-sm sm:text-base text-ufc-text inline-block text-left max-w-md mx-auto mb-6 space-y-2">
        <li>• 10-agent specialist breakdowns per fighter</li>
        <li>• Decagon ratings across striking, wrestling, grappling, submissions</li>
        <li>• Calculated moneyline odds and our Favorite Fighter pick</li>
        <li>• Head-to-head fight-flow analysis + last-5 fight history</li>
      </ul>
      <div className="flex flex-col sm:flex-row gap-3 justify-center items-center mt-6">
        <Link
          href="/paywall"
          className="inline-block bg-ufc-red hover:bg-ufc-red-dark text-white font-black text-base sm:text-lg px-8 py-4 rounded-xl transition-colors min-h-[56px] flex items-center justify-center"
        >
          Start 7-Day Free Trial
        </Link>
        <Link
          href="/"
          className="inline-block text-ufc-muted hover:text-white text-sm font-semibold underline-offset-4 hover:underline transition-colors min-h-[44px] flex items-center justify-center"
        >
          Back to card
        </Link>
      </div>
      <p className="text-[11px] text-ufc-muted mt-6 leading-relaxed max-w-sm mx-auto">
        Then $7.99/mo or $74.99/yr. Cancel anytime. Look for green tiles on the
        homepage — those fights are free for all signed-in users.
      </p>
    </div>
  );
}
