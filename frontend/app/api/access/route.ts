/**
 * GET /api/access?f1=<fighter1>&f2=<fighter2>
 *
 * Resolves whether the currently signed-in Clerk user can view the full
 * analysis for the given fight. Used by the fight detail page to decide
 * between rendering content or the locked-paywall card.
 *
 * Returns: { hasAccess: boolean, reason: "admin" | "free_tier" | "subscriber" | "locked" | "anonymous" }
 */

import { NextResponse } from "next/server";
import { auth, currentUser } from "@clerk/nextjs/server";
import { checkFightAccess } from "@/lib/access";
import type { Fight, CardData } from "@/lib/types";

function slug(s: string): string {
  return (
    s
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/^-+|-+$/g, "") || "unknown"
  );
}

function fightKey(f1: string, f2: string): string {
  const [a, b] = [slug(f1), slug(f2)].sort();
  return `${a}__${b}`;
}

async function lookupFight(req: Request, f1: string, f2: string): Promise<Fight | null> {
  const url = new URL("/data/card.json", req.url);
  try {
    const res = await fetch(url, { cache: "no-store" });
    if (!res.ok) return null;
    const card: CardData = await res.json();
    const target = fightKey(f1, f2);
    for (const fight of [...card.main_card, ...card.prelims]) {
      if (fightKey(fight.fighter1, fight.fighter2) === target) {
        return fight;
      }
    }
    return null;
  } catch {
    return null;
  }
}

export async function GET(req: Request) {
  const { searchParams } = new URL(req.url);
  const f1 = searchParams.get("f1");
  const f2 = searchParams.get("f2");
  if (!f1 || !f2) {
    return NextResponse.json(
      { error: "Missing f1 or f2 query parameter" },
      { status: 400 }
    );
  }

  const { userId } = await auth();
  const user = userId ? await currentUser() : null;
  const fight = await lookupFight(req, f1, f2);

  const result = await checkFightAccess({
    userId,
    publicMetadata: user?.publicMetadata as { role?: string } | null,
    fight,
  });

  return NextResponse.json(result);
}
