import { clerkMiddleware, createRouteMatcher } from "@clerk/nextjs/server";

// Routes anyone (signed in or not) can hit. Everything else requires sign-in
// per Option B gating: homepage browseable, fight detail behind paywall.
const isPublicRoute = createRouteMatcher([
  "/",
  "/sign-in(.*)",
  "/sign-up(.*)",
  "/privacy",
  "/terms",
]);

export default clerkMiddleware(async (auth, req) => {
  if (!isPublicRoute(req)) {
    await auth.protect();
  }
});

export const config = {
  matcher: [
    // Run on every page except Next.js internals and static asset paths.
    "/((?!_next|api/static|fighter_photos|data|.*\\..*).*)",
    // Always run for API routes
    "/(api|trpc)(.*)",
  ],
};
