import { SignIn } from "@clerk/nextjs";

export const metadata = {
  title: "Sign In — FightZ",
};

export default function SignInPage() {
  return (
    <div className="min-h-[60vh] flex items-center justify-center py-8">
      <SignIn
        appearance={{
          variables: {
            colorPrimary: "#dc0000",
            colorBackground: "#1a1a1a",
            colorText: "#ffffff",
            colorTextSecondary: "#999999",
            colorInputBackground: "#0d0d0d",
            colorInputText: "#ffffff",
          },
          elements: {
            card: "shadow-2xl border border-ufc-red/40",
          },
        }}
      />
    </div>
  );
}
