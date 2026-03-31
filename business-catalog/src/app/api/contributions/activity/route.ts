import { NextRequest, NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";

export async function GET(request: NextRequest) {
  const entityType = request.nextUrl.searchParams.get("entityType");
  const entityKey = request.nextUrl.searchParams.get("entityKey");

  if (!entityType || !entityKey) {
    return NextResponse.json({ error: "entityType and entityKey are required" }, { status: 400 });
  }

  const [flags, suggestions, annotations, discussions] = await Promise.all([
    prisma.flag.count({ where: { entityType, entityKey } }),
    prisma.suggestion.count({ where: { entityType, entityKey } }),
    prisma.annotation.count({ where: { entityType, entityKey } }),
    prisma.discussion.count({ where: { entityType, entityKey } }),
  ]);

  return NextResponse.json({
    flags,
    suggestions,
    annotations,
    discussions,
    total: flags + suggestions + annotations + discussions,
  });
}
