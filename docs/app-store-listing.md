# App Store Listing — FightZ

Draft saved 2026-05-07. Use this when filling out App Store Connect at submission time.

## App Name (max 30 chars)

**FightZ** *(6 chars)*

## Subtitle (max 30 chars)

**UFC Analysis & Calculated Odds** *(30 chars exactly)*

## Promotional Text (max 170 chars — editable anytime without resubmission)

> Fresh fight analysis, fighter ratings, and our own calculated odds — three times a week, every UFC card. Start your 7-day free trial today.

## Keywords (max 100 chars, comma-separated, NO spaces)

```
mma,picks,predictions,odds,betting,moneyline,fighter,octagon,combat,sports,handicap,cage
```

*(95 chars — leaves room to add 1–2 more once we see what's missing in App Store Search Ads later.)*

## Description (max 4000 chars — current draft ~1900 chars)

```
FightZ — UFC fight analysis built like a coach's corner.

Get a deeper read on every fight with FightZ. We send 10 specialist analysts at every fighter — five looking at offense (striking, wrestling, takedowns, grappling, submissions) and five looking at defense — and synthesize their reports into a clear pick with calculated odds you can shop against any sportsbook line.

What you get with FightZ:

• 10-agent specialist breakdowns — each fighter gets scored across all five MMA domains, on offense AND defense, by an analyst tuned to that domain alone.

• Decagon ratings at a glance — see exactly where each fighter is strongest and where their opponent can exploit them, on a single chart.

• Head-to-head breakdown — fight-flow read, key exchanges, paths to victory for each fighter.

• Most likely fight endings — ranked outcomes from "wins by KO Round 2" to "decision goes to scorecards."

• The Favorite Fighter pick — our pick, our calculated win probability, and our independent moneyline odds. We don't pull from any sportsbook — these are odds we computed ourselves so you can spot when a sportsbook line is or isn't value.

• Updated three times a week — fresh analysis every Monday, Wednesday, and Friday so you have the latest read going into fight night.

• Every fight on every UFC card — main events, championship fights, prelims. Not just the big names.

Try it free for 7 days.

Start your free 7-day trial — no charge until day 8. After the trial, FightZ is $7.99/month or $74.99/year (saves you 22%). Cancel anytime in your Apple ID settings.

Important:

FightZ is for entertainment and educational purposes only. We are not affiliated with the UFC, Zuffa LLC, or any sportsbook. Nothing on FightZ is professional gambling or financial advice — outcomes of MMA fights are unpredictable and any betting carries risk. You must be 18+ (21+ in some jurisdictions) and meet your local legal gambling age. If you or someone you know has a gambling problem, call 1-800-GAMBLER or visit ncpgambling.org.
```

## Categories

- **Primary:** Sports
- **Secondary:** Lifestyle (or Entertainment, depending on App Store options)

## App Privacy questionnaire (Apple Connect)

Based on current data flow:
- **Data Linked to You:** Email Address (used for account creation via Clerk)
- **Data Not Linked to You:** Diagnostics (server logs)
- **Data Used to Track You:** None
- **Third parties:** Clerk (auth), Vercel (hosting), Anthropic (AI analysis — no user data sent), RevenueCat (subscription management once wired)

## Submission notes — what to verify before tapping Submit

- [ ] Privacy Policy URL: `https://fightz.app/privacy`
- [ ] Terms of Service URL: `https://fightz.app/terms`
- [ ] Support URL: `https://fightz.app/` (or `mailto:zacharytroberts03@gmail.com`)
- [ ] Demo account credentials for review team (create a test Clerk account: `apple-review@fightz.app` with password) — Apple reviewers will use this to access gated content
- [ ] All 5–10 screenshots staged (6.7" iPhone)
- [ ] App icon at `frontend/public/icon-1024.png`
- [x] Domain swap from `ufc-z.com` to clean domain done — `fightz.app` registered + live 2026-05-11
- [ ] RevenueCat fully wired and IAP products created in App Store Connect
- [ ] Test purchase flow in TestFlight before submission
