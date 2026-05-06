import { SignIn } from "@clerk/nextjs";

export const metadata = {
  title: "Sign In — FightZ",
};

export default function SignInPage() {
  return (
    <div className="min-h-[60vh] flex items-center justify-center py-8">
      <SignIn
        appearance={{
          elements: {
            card: "shadow-2xl border border-ufc-red/40",
          },
        }}
      />
    </div>
  );
}
