import { NextRequest, NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";

export async function GET(request: NextRequest) {
  const entityType = request.nextUrl.searchParams.get("entityType");
  const entityKey = request.nextUrl.searchParams.get("entityKey");

  if (!entityType || !entityKey) {
    return NextResponse.json({ error: "entityType and entityKey are required" }, { status: 400 });
  }

  const suggestions = await prisma.suggestion.findMany({
    where: { entityType, entityKey },
    orderBy: { createdAt: "desc" },
  });

  return NextResponse.json(suggestions);
}

export async function POST(request: NextRequest) {
  const body = await request.json();
  const { entityType, entityKey, fieldName, currentValue, proposedValue, reason, author } = body;

  if (!entityType || !entityKey || !fieldName || !proposedValue || !author) {
    return NextResponse.json(
      { error: "entityType, entityKey, fieldName, proposedValue, and author are required" },
      { status: 400 }
    );
  }

  const suggestion = await prisma.suggestion.create({
    data: {
      entityType,
      entityKey,
      fieldName,
      currentValue: currentValue || null,
      proposedValue,
      reason: reason || null,
      author,
    },
  });

  return NextResponse.json(suggestion, { status: 201 });
}
