import { NextRequest, NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";

export async function GET(request: NextRequest) {
  const entityType = request.nextUrl.searchParams.get("entityType");
  const entityKey = request.nextUrl.searchParams.get("entityKey");

  if (!entityType || !entityKey) {
    return NextResponse.json({ error: "entityType and entityKey are required" }, { status: 400 });
  }

  const flags = await prisma.flag.findMany({
    where: { entityType, entityKey, status: "open" },
    select: { flagType: true },
  });

  const byType: Record<string, number> = { outdated: 0, incorrect: 0, missing: 0, unclear: 0 };
  for (const f of flags) {
    byType[f.flagType] = (byType[f.flagType] || 0) + 1;
  }

  return NextResponse.json({ total: flags.length, byType });
}
