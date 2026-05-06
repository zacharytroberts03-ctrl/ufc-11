import Link from "next/link";

export const metadata = {
  title: "Privacy Policy — UFC Z",
  description: "Privacy Policy for UFC Z fight analyzer",
};

export default function PrivacyPage() {
  const updated = "May 5, 2026";
  return (
    <article className="max-w-3xl mx-auto py-8 sm:py-12 text-white/90 leading-relaxed">
      <Link
        href="/"
        className="inline-flex items-center gap-2 text-ufc-muted hover:text-white text-sm font-semibold mb-8 py-2 -mx-2 px-2 min-h-[44px] transition-colors"
      >
        ← Back to Fight Card
      </Link>

      <h1 className="text-3xl sm:text-4xl font-black text-white mb-2">Privacy Policy</h1>
      <p className="text-sm text-ufc-muted mb-10">Last updated: {updated}</p>

      <div className="space-y-6 text-sm sm:text-base">
        <section>
          <h2 className="text-xl font-bold text-white mb-2">1. Overview</h2>
          <p>
            UFC Z (&quot;we,&quot; &quot;our,&quot; or &quot;the Service&quot;) provides UFC fight analysis,
            statistical breakdowns, and AI-generated betting commentary at{" "}
            <a href="https://www.ufc-z.com" className="text-ufc-red underline">www.ufc-z.com</a>{" "}
            and any associated mobile applications. This Privacy Policy explains what
            information we collect, how we use it, and your choices.
          </p>
        </section>

        <section>
          <h2 className="text-xl font-bold text-white mb-2">2. Information We Collect</h2>
          <p className="mb-3">
            We aim to collect as little personal information as possible. Specifically:
          </p>
          <ul className="list-disc pl-6 space-y-2">
            <li>
              <strong className="text-white">Public fighter statistics.</strong> All
              fighter data shown on the Service is sourced from publicly available
              records (UFC official statistics, Tapology, public sports-betting
              odds APIs). It is not personal information about you.
            </li>
            <li>
              <strong className="text-white">Server logs.</strong> Our hosting
              provider (Vercel) automatically logs standard web request data such
              as IP address, user-agent string, and request timestamps for
              security and operational purposes. We do not associate these logs
              with individual users.
            </li>
            <li>
              <strong className="text-white">No accounts at this time.</strong>{" "}
              We do not currently require sign-up. We do not collect names,
              email addresses, payment information, or other personally
              identifiable information directly.
            </li>
            <li>
              <strong className="text-white">Cookies.</strong> The Service may use
              minimal session cookies for normal site functionality. We do not
              currently run advertising trackers or third-party analytics that
              identify individuals.
            </li>
          </ul>
        </section>

        <section>
          <h2 className="text-xl font-bold text-white mb-2">3. How We Use Information</h2>
          <p className="mb-3">We use the limited data we collect only to:</p>
          <ul className="list-disc pl-6 space-y-2">
            <li>Operate, maintain, and secure the Service.</li>
            <li>Diagnose technical issues and prevent abuse.</li>
            <li>Improve the accuracy of our fight analysis features.</li>
          </ul>
          <p className="mt-3">
            We do not sell, rent, or share personal information with third parties
            for marketing purposes.
          </p>
        </section>

        <section>
          <h2 className="text-xl font-bold text-white mb-2">4. Third-Party Services</h2>
          <p className="mb-3">
            The Service relies on the following third-party providers, each of
            which has its own privacy practices:
          </p>
          <ul className="list-disc pl-6 space-y-2">
            <li>
              <strong className="text-white">Vercel</strong> — hosting and content
              delivery.
            </li>
            <li>
              <strong className="text-white">Cloudflare</strong> — DNS resolution
              and domain management.
            </li>
            <li>
              <strong className="text-white">Anthropic</strong> — AI model
              provider used to generate fight analysis text. No user-identifying
              information is sent to Anthropic.
            </li>
            <li>
              <strong className="text-white">UFCStats, Tapology, The Odds API</strong>
              {" "}— public data sources for fighter statistics and betting lines.
            </li>
          </ul>
        </section>

        <section>
          <h2 className="text-xl font-bold text-white mb-2">5. Children&apos;s Privacy</h2>
          <p>
            The Service is not directed at children under 13 (or the equivalent
            minimum age in your jurisdiction). We do not knowingly collect
            information from children. The Service&apos;s subject matter (sports
            betting analysis) is intended for adults of legal gambling age in
            their jurisdiction.
          </p>
        </section>

        <section>
          <h2 className="text-xl font-bold text-white mb-2">6. Your Rights</h2>
          <p>
            Because we do not collect personally identifiable information directly,
            most data-subject rights (access, correction, deletion) are limited in
            scope. If you believe we hold information about you and wish to
            inquire, you may contact us at the email address listed below.
          </p>
        </section>

        <section>
          <h2 className="text-xl font-bold text-white mb-2">7. Data Retention</h2>
          <p>
            Server logs are retained for the period required by our hosting
            provider for operational and security purposes. We do not maintain
            user-specific records beyond what is necessary to operate the Service.
          </p>
        </section>

        <section>
          <h2 className="text-xl font-bold text-white mb-2">8. Changes to This Policy</h2>
          <p>
            We may update this Privacy Policy from time to time. The &quot;Last
            updated&quot; date at the top of this page reflects the most recent
            version. Material changes will be communicated through the Service.
          </p>
        </section>

        <section>
          <h2 className="text-xl font-bold text-white mb-2">9. Contact</h2>
          <p>
            Questions or concerns about this Privacy Policy can be sent to{" "}
            <a
              href="mailto:zacharytroberts03@gmail.com"
              className="text-ufc-red underline"
            >
              zacharytroberts03@gmail.com
            </a>
            .
          </p>
        </section>
      </div>
    </article>
  );
}
