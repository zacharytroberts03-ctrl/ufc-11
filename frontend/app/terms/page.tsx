import Link from "next/link";

export const metadata = {
  title: "Terms of Service — FightZ",
  description: "Terms of Service for FightZ fight analyzer",
};

export default function TermsPage() {
  const updated = "May 5, 2026";
  return (
    <article className="max-w-3xl mx-auto py-8 sm:py-12 text-white/90 leading-relaxed">
      <Link
        href="/"
        className="inline-flex items-center gap-2 text-ufc-muted hover:text-white text-sm font-semibold mb-8 py-2 -mx-2 px-2 min-h-[44px] transition-colors"
      >
        ← Back to Fight Card
      </Link>

      <h1 className="text-3xl sm:text-4xl font-black text-white mb-2">Terms of Service</h1>
      <p className="text-sm text-ufc-muted mb-10">Last updated: {updated}</p>

      {/* Strong, hard-to-miss disclaimer up top — App Store reviewers expect this for betting/sports content */}
      <div className="rounded-lg border-2 border-ufc-red bg-ufc-red/10 p-4 sm:p-5 mb-10">
        <h2 className="text-base sm:text-lg font-black text-white mb-2 uppercase tracking-wider">
          Important — Read Before Using
        </h2>
        <p className="text-sm sm:text-base text-white/95">
          FightZ provides fight analysis and informational commentary for{" "}
          <strong>entertainment and educational purposes only</strong>. Nothing on
          the Service constitutes professional gambling, financial, or
          investment advice. We do not place bets on your behalf and we are not
          affiliated with the UFC, any sportsbook, any athlete, or any betting
          operator. You must be of legal gambling age in your jurisdiction to
          act on any information here, and you alone are responsible for your
          choices.
        </p>
      </div>

      <div className="space-y-6 text-sm sm:text-base">
        <section>
          <h2 className="text-xl font-bold text-white mb-2">1. Acceptance of Terms</h2>
          <p>
            By accessing or using FightZ (the &quot;Service&quot;), including the
            website at{" "}
            <a href="https://fightz.app" className="text-ufc-red underline">fightz.app</a>{" "}
            and any associated mobile applications, you agree to be bound by
            these Terms of Service (&quot;Terms&quot;). If you do not agree, do
            not use the Service.
          </p>
        </section>

        <section>
          <h2 className="text-xl font-bold text-white mb-2">2. Eligibility</h2>
          <p>
            You must be at least 18 years old (or the legal age of majority and
            legal gambling age in your jurisdiction, whichever is greater) to
            use the Service. Some jurisdictions require users to be 21 or older
            to participate in any sports-betting-related activity. By using the
            Service, you represent that you meet these requirements.
          </p>
        </section>

        <section>
          <h2 className="text-xl font-bold text-white mb-2">3. Nature of the Service</h2>
          <p className="mb-3">
            The Service provides:
          </p>
          <ul className="list-disc pl-6 space-y-2">
            <li>Public fighter statistics scraped from third-party sources.</li>
            <li>
              AI-generated fight analysis, predicted outcomes, and probability
              estimates produced by automated language models.
            </li>
            <li>
              Calculated equivalent moneyline odds based on those probability
              estimates. These odds are computed by us and are not pulled from,
              endorsed by, or affiliated with any sportsbook.
            </li>
          </ul>
          <p className="mt-3">
            All content is provided <strong>as-is</strong> and may contain
            errors, omissions, or biases inherent to the data sources and
            algorithms used. The Service is not professional handicapping
            advice.
          </p>
        </section>

        <section>
          <h2 className="text-xl font-bold text-white mb-2">4. No Guarantees</h2>
          <p>
            We make no representations or warranties about the accuracy,
            completeness, reliability, or suitability of any content on the
            Service. Past performance of any prediction is not indicative of
            future results. Outcomes of mixed-martial-arts contests are
            unpredictable and any betting activity carries real risk of
            financial loss.
          </p>
        </section>

        <section>
          <h2 className="text-xl font-bold text-white mb-2">5. Acceptable Use</h2>
          <p className="mb-3">You agree not to:</p>
          <ul className="list-disc pl-6 space-y-2">
            <li>Use the Service for any unlawful purpose.</li>
            <li>
              Attempt to scrape, copy, or republish the Service&apos;s content in
              bulk without written permission.
            </li>
            <li>
              Use automated systems to access the Service in a manner that
              imposes an unreasonable load on our infrastructure.
            </li>
            <li>
              Reverse-engineer, decompile, or attempt to derive the source code
              of any component of the Service except where permitted by law.
            </li>
            <li>
              Misrepresent the Service&apos;s output as professional gambling
              advice or as the work of any third party.
            </li>
          </ul>
        </section>

        <section>
          <h2 className="text-xl font-bold text-white mb-2">6. Intellectual Property</h2>
          <p>
            The original content, design, and code of the Service are owned by
            FightZ and protected by applicable copyright and trademark laws.
            Fighter names, statistics, and event names are property of their
            respective owners and are used for informational purposes only.
            FightZ is not affiliated with, endorsed by, or sponsored by Zuffa LLC
            or the Ultimate Fighting Championship.
          </p>
        </section>

        <section>
          <h2 className="text-xl font-bold text-white mb-2">7. Subscriptions and Purchases</h2>
          <p>
            Some features of the Service may, in the future, be available only
            through paid subscriptions purchased via in-app purchase. If
            offered, subscriptions auto-renew unless cancelled at least 24 hours
            before the end of the current billing period. Manage or cancel
            subscriptions through your device&apos;s App Store account
            settings. We do not directly process payments; all transactions are
            handled by the relevant App Store provider (Apple App Store or
            Google Play).
          </p>
        </section>

        <section>
          <h2 className="text-xl font-bold text-white mb-2">8. Disclaimer of Warranties</h2>
          <p>
            THE SERVICE IS PROVIDED &quot;AS IS&quot; AND &quot;AS
            AVAILABLE&quot; WITHOUT WARRANTIES OF ANY KIND, EXPRESS OR IMPLIED,
            INCLUDING BUT NOT LIMITED TO IMPLIED WARRANTIES OF MERCHANTABILITY,
            FITNESS FOR A PARTICULAR PURPOSE, OR NON-INFRINGEMENT. WE DO NOT
            WARRANT THAT THE SERVICE WILL BE UNINTERRUPTED, ERROR-FREE, OR
            ACCURATE.
          </p>
        </section>

        <section>
          <h2 className="text-xl font-bold text-white mb-2">9. Limitation of Liability</h2>
          <p>
            TO THE MAXIMUM EXTENT PERMITTED BY LAW, FightZ AND ITS OPERATORS
            SHALL NOT BE LIABLE FOR ANY INDIRECT, INCIDENTAL, SPECIAL,
            CONSEQUENTIAL, OR PUNITIVE DAMAGES, INCLUDING BUT NOT LIMITED TO
            LOSS OF PROFITS, GAMBLING LOSSES, OR LOSS OF DATA, ARISING OUT OF OR
            IN CONNECTION WITH YOUR USE OF THE SERVICE. YOU EXPRESSLY ASSUME ALL
            RISK ASSOCIATED WITH ACTING ON ANY INFORMATION PROVIDED BY THE
            SERVICE.
          </p>
        </section>

        <section>
          <h2 className="text-xl font-bold text-white mb-2">10. Responsible Gambling</h2>
          <p>
            If you or someone you know is struggling with problem gambling, help
            is available. In the United States, contact the National Council on
            Problem Gambling at 1-800-GAMBLER or visit{" "}
            <a
              href="https://www.ncpgambling.org/"
              target="_blank"
              rel="noopener noreferrer"
              className="text-ufc-red underline"
            >
              ncpgambling.org
            </a>
            .
          </p>
        </section>

        <section>
          <h2 className="text-xl font-bold text-white mb-2">11. Termination</h2>
          <p>
            We reserve the right to suspend or terminate access to the Service
            at our discretion, without notice, for any conduct that we believe
            violates these Terms or is harmful to other users, the Service, or
            third parties.
          </p>
        </section>

        <section>
          <h2 className="text-xl font-bold text-white mb-2">12. Changes to These Terms</h2>
          <p>
            We may update these Terms from time to time. The &quot;Last
            updated&quot; date reflects the most recent version. Continued use
            of the Service after changes constitutes acceptance of the new
            Terms.
          </p>
        </section>

        <section>
          <h2 className="text-xl font-bold text-white mb-2">13. Governing Law</h2>
          <p>
            These Terms are governed by the laws of the State of Florida,
            United States, without regard to its conflict-of-laws principles.
            Disputes will be resolved in the state or federal courts located in
            Brevard County, Florida.
          </p>
        </section>

        <section>
          <h2 className="text-xl font-bold text-white mb-2">14. Contact</h2>
          <p>
            Questions about these Terms can be sent to{" "}
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
