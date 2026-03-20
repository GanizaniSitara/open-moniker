import { NextRequest, NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";

export async function GET(request: NextRequest) {
  const entityType = request.nextUrl.searchParams.get("entityType");
  const entityKey = request.nextUrl.searchParams.get("entityKey");

  if (!entityType || !entityKey) {
    return NextResponse.json({ error: "entityType and entityKey are required" }, { status: 400 });
  }

  const discussions = await prisma.discussion.findMany({
    where: { entityType, entityKey },
    include: { _count: { select: { replies: true } } },
    orderBy: { updatedAt: "desc" },
  });

  const result = discussions.map((d) => ({
    id: d.id,
    entityType: d.entityType,
    entityKey: d.entityKey,
    title: d.title,
    author: d.author,
    replyCount: d._count.replies,
    createdAt: d.createdAt,
    updatedAt: d.updatedAt,
  }));

  return NextResponse.json(result);
}

export async function POST(request: NextRequest) {
  const body = await request.json();
  const { entityType, entityKey, title, author } = body;

  if (!entityType || !entityKey || !title || !author) {
    return NextResponse.json(
      { error: "entityType, entityKey, title, and author are required" },
      { status: 400 }
    );
  }

  const discussion = await prisma.discussion.create({
    data: { entityType, entityKey, title, author },
  });

  return NextResponse.json({ ...discussion, replyCount: 0 }, { status: 201 });
}
