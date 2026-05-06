import { SignUp } from "@clerk/nextjs";
import Link from "next/link";

export const metadata = {
  title: "Sign Up — FightZ",
};

export default function SignUpPage() {
  return (
    <div className="min-h-[70vh] flex flex-col items-center justify-center py-8">
      <div className="text-center mb-6 max-w-md">
        <h1 className="text-2xl sm:text-3xl font-black text-white mb-2">
          Create your FightZ account
        </h1>
        <p className="text-sm text-ufc-muted">
          Sign up to unlock fight analysis, fighter ratings, and calculated odds.
          <span className="block mt-1">
            <span className="text-ufc-red font-semibold">7-day free trial</span>{" "}
            — no charge until day 8, cancel anytime.
          </span>
        </p>
      </div>

      <SignUp
        appearance={{
          elements: {
            card: "shadow-2xl border border-ufc-red/40",
          },
        }}
      />

      <p className="text-xs text-ufc-muted mt-6 max-w-md text-center">
        By signing up you agree to our{" "}
        <Link href="/terms" className="text-ufc-red underline">
          Terms of Service
        </Link>{" "}
        and{" "}
        <Link href="/privacy" className="text-ufc-red underline">
          Privacy Policy
        </Link>
        .
      </p>
    </div>
  );
}
