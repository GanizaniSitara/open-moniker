import { NextRequest, NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";

export async function GET(
  _request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;

  const discussion = await prisma.discussion.findUnique({
    where: { id },
    include: {
      replies: { orderBy: { createdAt: "asc" } },
    },
  });

  if (!discussion) {
    return NextResponse.json({ error: "Discussion not found" }, { status: 404 });
  }

  return NextResponse.json(discussion);
}
