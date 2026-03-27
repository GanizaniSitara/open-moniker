import { NextRequest, NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";

export async function GET(request: NextRequest) {
  const entityType = request.nextUrl.searchParams.get("entityType");
  const entityKey = request.nextUrl.searchParams.get("entityKey");

  if (!entityType || !entityKey) {
    return NextResponse.json({ error: "entityType and entityKey are required" }, { status: 400 });
  }

  const [helpful, notHelpful] = await Promise.all([
    prisma.helpfulVote.count({ where: { entityType, entityKey, helpful: true } }),
    prisma.helpfulVote.count({ where: { entityType, entityKey, helpful: false } }),
  ]);

  return NextResponse.json({ helpful, notHelpful, total: helpful + notHelpful });
}

export async function POST(request: NextRequest) {
  const body = await request.json();
  const { entityType, entityKey, helpful, comment, author } = body;

  if (!entityType || !entityKey || typeof helpful !== "boolean") {
    return NextResponse.json({ error: "entityType, entityKey, and helpful are required" }, { status: 400 });
  }

  const vote = await prisma.helpfulVote.create({
    data: {
      entityType,
      entityKey,
      helpful,
      comment: comment || null,
      author: author || null,
    },
  });

  return NextResponse.json(vote, { status: 201 });
}
