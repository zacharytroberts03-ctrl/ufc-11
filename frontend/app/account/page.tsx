import { auth, currentUser } from "@clerk/nextjs/server";
import { redirect } from "next/navigation";
import Link from "next/link";

export const metadata = {
  title: "Account — FightZ",
};

export default async function AccountPage() {
  const { userId } = await auth();
  if (!userId) {
    redirect("/sign-in");
  }
  const user = await currentUser();
  const email = user?.primaryEmailAddress?.emailAddress ?? "—";
  const memberSince = user?.createdAt
    ? new Date(user.createdAt).toLocaleDateString()
    : "—";

  // Subscription state is stubbed until RevenueCat is wired in Phase 4.
  // Until then, all signed-in users are treated as on the free trial so
  // they can preview the gated content.
  const subscriptionStatus = {
    tier: "Free Trial",
    renewsOn: "—",
    note:
      "Live subscription status will appear here once App Store In-App Purchase is connected.",
  };

  return (
    <div className="max-w-2xl mx-auto py-8 sm:py-12">
      <h1 className="text-3xl sm:text-4xl font-black text-white mb-8">
        Your account
      </h1>

      {/* Profile */}
      <section
        className="rounded-xl p-5 sm:p-6 mb-6 shadow-lg"
        style={{
          background: "linear-gradient(135deg, #1a1a1a 0%, #0d0d0d 100%)",
          border: "1px solid #2a2a2a",
        }}
      >
        <h2 className="text-xs font-black tracking-widest text-ufc-red uppercase mb-3">
          Profile
        </h2>
        <dl className="space-y-2 text-sm">
          <div className="flex justify-between gap-4">
            <dt className="text-ufc-muted">Email</dt>
            <dd className="text-white font-semibold truncate">{email}</dd>
          </div>
          <div className="flex justify-between gap-4">
            <dt className="text-ufc-muted">Member since</dt>
            <dd className="text-white font-semibold">{memberSince}</dd>
          </div>
        </dl>
      </section>

      {/* Subscription */}
      <section
        className="rounded-xl p-5 sm:p-6 mb-6 shadow-lg"
        style={{
          background: "linear-gradient(135deg, #1a1a1a 0%, #0d0d0d 100%)",
          border: "1px solid #2a2a2a",
        }}
      >
        <h2 className="text-xs font-black tracking-widest text-ufc-red uppercase mb-3">
          Subscription
        </h2>
        <dl className="space-y-2 text-sm mb-4">
          <div className="flex justify-between gap-4">
            <dt className="text-ufc-muted">Plan</dt>
            <dd className="text-white font-semibold">{subscriptionStatus.tier}</dd>
          </div>
          <div className="flex justify-between gap-4">
            <dt className="text-ufc-muted">Renews on</dt>
            <dd className="text-white font-semibold">{subscriptionStatus.renewsOn}</dd>
          </div>
        </dl>
        <p className="text-[11px] text-ufc-muted leading-relaxed border-l-2 border-ufc-border pl-3 mb-4">
          {subscriptionStatus.note}
        </p>
        <Link
          href="/paywall"
          className="inline-flex items-center justify-center bg-ufc-red hover:bg-ufc-red-dark text-white font-bold text-sm py-3 px-5 rounded-lg transition-colors min-h-[44px]"
        >
          Manage subscription
        </Link>
      </section>

      {/* Restore + manage links */}
      <section
        className="rounded-xl p-5 sm:p-6 mb-6 shadow-lg"
        style={{
          background: "linear-gradient(135deg, #1a1a1a 0%, #0d0d0d 100%)",
          border: "1px solid #2a2a2a",
        }}
      >
        <h2 className="text-xs font-black tracking-widest text-ufc-red uppercase mb-3">
          Billing
        </h2>
        <p className="text-sm text-ufc-muted mb-3">
          Subscriptions are managed by your App Store account. Once the in-app
          subscription is live, you can cancel or change your plan from your
          device&apos;s Settings → Apple ID → Subscriptions.
        </p>
        <a
          href="https://apps.apple.com/account/subscriptions"
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center text-sm font-semibold text-ufc-red hover:text-white transition-colors min-h-[44px]"
        >
          Open Apple Subscription Settings →
        </a>
      </section>

      <p className="text-center text-xs text-ufc-muted">
        Need help? Email{" "}
        <a
          href="mailto:zacharytroberts03@gmail.com"
          className="text-ufc-red underline"
        >
          zacharytroberts03@gmail.com
        </a>
      </p>
    </div>
  );
}
