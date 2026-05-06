import { clerkMiddleware, createRouteMatcher } from "@clerk/nextjs/server";
import { NextResponse } from "next/server";

// Routes anyone (signed in or not) can hit. Everything else requires sign-in
// per Option B gating: homepage browseable, fight detail prompts sign-up.
const isPublicRoute = createRouteMatcher([
  "/",
  "/sign-in(.*)",
  "/sign-up(.*)",
  "/privacy",
  "/terms",
]);

export default clerkMiddleware(async (auth, req) => {
  if (isPublicRoute(req)) return;

  const { userId } = await auth();
  if (!userId) {
    // Send anonymous users to sign-up (not sign-in) per the chosen flow:
    // we want to convert browsers into accounts, not just authenticate
    // existing users. Preserve where they were headed so they can continue
    // after creating an account.
    const signUpUrl = new URL("/sign-up", req.url);
    signUpUrl.searchParams.set("redirect_url", req.nextUrl.pathname);
    return NextResponse.redirect(signUpUrl);
  }
});

export const config = {
  matcher: [
    // Run on every page except Next.js internals and static asset paths.
    "/((?!_next|api/static|fighter_photos|data|.*\\..*).*)",
    "/(api|trpc)(.*)",
  ],
};
