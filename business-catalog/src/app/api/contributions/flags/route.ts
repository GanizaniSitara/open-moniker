import { NextRequest, NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";

export async function GET(request: NextRequest) {
  const entityType = request.nextUrl.searchParams.get("entityType");
  const entityKey = request.nextUrl.searchParams.get("entityKey");

  if (!entityType || !entityKey) {
    return NextResponse.json({ error: "entityType and entityKey are required" }, { status: 400 });
  }

  const flags = await prisma.flag.findMany({
    where: { entityType, entityKey },
    orderBy: { createdAt: "desc" },
  });

  return NextResponse.json(flags);
}

export async function POST(request: NextRequest) {
  const body = await request.json();
  const { entityType, entityKey, flagType, comment, author } = body;

  if (!entityType || !entityKey || !flagType || !author) {
    return NextResponse.json({ error: "entityType, entityKey, flagType, and author are required" }, { status: 400 });
  }

  const flag = await prisma.flag.create({
    data: { entityType, entityKey, flagType, comment: comment || null, author },
  });

  return NextResponse.json(flag, { status: 201 });
}
