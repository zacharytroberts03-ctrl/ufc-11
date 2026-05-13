# FightZ iOS build — Mac instructions

The Capacitor wrapper around `fightz.app` is fully configured in the repo. This
doc covers the Mac-only steps to produce a TestFlight build and submit to the
App Store.

## Prerequisites on the Mac

- macOS (any recent version; Capacitor + Xcode supported back to macOS 13)
- **Xcode 16+** installed from the Mac App Store (free, ~10 GB)
- **CocoaPods** — install with: `sudo gem install cocoapods` (or `brew install cocoapods`)
- **Node 20+** — install via [nvm](https://github.com/nvm-sh/nvm) or [Volta](https://volta.sh/), or download from nodejs.org
- The Apple Developer account approved for the team (already done 2026-05-11)

## Sign in to Xcode with your Apple ID

Open Xcode → Settings → Accounts → click `+` → Apple ID → sign in. Xcode now
knows about your team (`zacharytroberts03-ctrl`) and can manage signing certs
automatically.

## One-time: clone repo and generate iOS project

```bash
git clone https://github.com/zacharytroberts03-ctrl/ufc-11.git
cd ufc-11/frontend
npm install                 # installs Capacitor + RevenueCat plugin
npx cap add ios             # generates the ios/ folder (Mac-only command;
                            # this writes a complete Xcode project to ios/App)
npx cap sync ios            # links the JS config + plugins into the Xcode project
```

After `cap add ios`, you have a real Xcode project at `frontend/ios/App/`. The
Capacitor wrapper at runtime loads `https://fightz.app` (configured in
`capacitor.config.ts → server.url`), so the iOS app is essentially a native
shell around the live website.

## Open in Xcode and configure signing

```bash
npx cap open ios
```

This opens `frontend/ios/App/App.xcworkspace` in Xcode. In the Xcode UI:

1. Click the **`App`** target in the left navigator → **Signing & Capabilities** tab
2. **Team:** select your Apple Developer team from the dropdown
3. **Bundle Identifier:** confirm it shows `com.fightz.app` (matches the App ID
   you registered in the Apple Developer portal)
4. Make sure **"Automatically manage signing"** is checked
5. Click **`+ Capability`** at the top and add **`In-App Purchase`** if it's
   not already listed (required for RevenueCat to talk to StoreKit)

## Build for the simulator (smoke test)

In Xcode top bar:
1. Pick a simulator device (e.g. **iPhone 15 Pro Max**) from the device dropdown
2. Hit **▶** (Cmd+R)

The simulator boots, the FightZ wrapper launches, and you should see the live
fightz.app homepage. Click around — sign-in, fight pages, paywall — to confirm
the wrapper works.

**Note:** in the simulator you cannot test actual purchases (Apple's
StoreKit sandbox requires a real device or specific StoreKit test config).
Subscriptions will be tested via TestFlight on your iPhone.

## Build for TestFlight

1. Xcode top bar → device dropdown → select **`Any iOS Device (arm64)`**
2. Menu → **Product → Archive**
3. Wait ~1–3 minutes for the archive to build
4. When the **Organizer** window pops up showing the archive:
   - Click **`Distribute App`**
   - Select **`App Store Connect`** → **`Upload`** → Next through the dialogs
   - Xcode signs the archive, uploads to App Store Connect (3–10 min)
5. The build appears in App Store Connect under **TestFlight** within 5–30 min

## Add yourself as a TestFlight tester

In App Store Connect:
1. Apps → FightZ → **TestFlight** tab
2. **Internal Testing** → click `+ New Group` → name it `Dev` → add yourself
   as a tester
3. Once the build finishes processing, attach it to the Dev group
4. You'll get an email with a TestFlight invite — accept on your iPhone
5. Open the **TestFlight** app on iPhone → install FightZ → run it

## Test the purchase flow on TestFlight

TestFlight builds run against Apple's **sandbox** purchase environment, which
charges nothing. To test:

1. On your iPhone: **Settings → App Store → Sandbox Account**
2. Sign in with a sandbox tester account (create one in App Store Connect →
   Users and Access → Sandbox)
3. Open FightZ via TestFlight
4. Sign up / sign in with a Clerk account
5. Tap a paid fight (any non-green tile) → tap **Start 7-Day Free Trial**
6. Apple's native purchase sheet should appear with the `fightz_monthly` or
   `fightz_annual` product, $7.99 or $74.99, "7-day free trial"
7. Tap **Subscribe** → confirm with Face ID → purchase completes
8. The lock card should disappear and the fight analysis renders
9. `/api/access` will now return `{"reason": "subscriber"}` for that user

If any step fails, the most common causes (in order of likelihood):

- **Sandbox account not signed in** — re-check Settings → App Store → Sandbox
- **Products not yet visible** — App Store Connect product visibility lags
  ~30 min after first creation. Wait.
- **Bundle ID mismatch** — Xcode signing team / Bundle ID must match the App
  ID and the App Store Connect app entry. Triple-check `com.fightz.app`
  everywhere.
- **RevenueCat IAP key not configured** — verify in RevenueCat dashboard that
  the In-App Purchase Key + Issuer ID + Shared Secret are all saved for the
  iOS app.

## Iterating on web changes

The wrapper loads `https://fightz.app` at runtime, so most code changes (UI,
new fight data, paywall copy) ship via the normal Vercel deploy and are
reflected in the iOS app on next launch — **no need to rebuild the .ipa**.

The only time you need to rebuild and re-upload is when you change:
- Capacitor configuration (`capacitor.config.ts`)
- Native plugins (e.g. update `@revenuecat/purchases-capacitor`)
- iOS-specific assets (icon, splash screen)
- App version number for a new TestFlight build

For those, rerun `npx cap sync ios` on the Mac, then Archive + Distribute
again.

## Submitting for App Store review

Once TestFlight has verified the build works end-to-end:

1. App Store Connect → FightZ → **App Store** tab → **iOS App 1.0**
2. Fill in all the metadata from `docs/app-store-listing.md` (name, subtitle,
   keywords, description, App Privacy, age rating 17+ with Real Gambling
   References)
3. Attach the TestFlight build to the version (`+ Build` button)
4. Attach the two subscriptions (`fightz_monthly` + `fightz_annual`) to the
   version submission
5. Provide Apple reviewer demo credentials in **App Review Information**:
   - Username: an admin Clerk account (e.g. `apple-review@fightz.app`)
   - Password: a memorable test password
   - Notes: "Admin role bypasses the subscription paywall so reviewers can
     access all fight breakdowns without going through IAP. The free 7-day
     intro trial is also available for testing the purchase flow on a fresh
     account."
6. Submit for review. Apple typically responds in 24–48h.
