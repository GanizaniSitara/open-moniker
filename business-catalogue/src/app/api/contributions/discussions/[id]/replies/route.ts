import { NextRequest, NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;
  const body = await request.json();
  const { content, author, parentReplyId } = body;

  if (!content || !author) {
    return NextResponse.json({ error: "content and author are required" }, { status: 400 });
  }

  const reply = await prisma.discussionReply.create({
    data: {
      discussionId: id,
      content,
      author,
      parentReplyId: parentReplyId || null,
    },
  });

  // Bump the discussion's updatedAt
  await prisma.discussion.update({
    where: { id },
    data: { updatedAt: new Date() },
  });

  return NextResponse.json(reply, { status: 201 });
}
