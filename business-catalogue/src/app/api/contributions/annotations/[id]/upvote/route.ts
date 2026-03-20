import { NextRequest, NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;
  const body = await request.json();
  const { voter } = body;

  if (!voter) {
    return NextResponse.json({ error: "voter is required" }, { status: 400 });
  }

  // Upsert vote — idempotent
  const existing = await prisma.annotationVote.findUnique({
    where: { annotationId_voter: { annotationId: id, voter } },
  });

  if (!existing) {
    await prisma.$transaction([
      prisma.annotationVote.create({
        data: { annotationId: id, voter },
      }),
      prisma.annotation.update({
        where: { id },
        data: { upvoteCount: { increment: 1 } },
      }),
    ]);
  }

  return NextResponse.json({ ok: true });
}

export async function DELETE(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;
  const body = await request.json();
  const { voter } = body;

  if (!voter) {
    return NextResponse.json({ error: "voter is required" }, { status: 400 });
  }

  const existing = await prisma.annotationVote.findUnique({
    where: { annotationId_voter: { annotationId: id, voter } },
  });

  if (existing) {
    await prisma.$transaction([
      prisma.annotationVote.delete({
        where: { id: existing.id },
      }),
      prisma.annotation.update({
        where: { id },
        data: { upvoteCount: { decrement: 1 } },
      }),
    ]);
  }

  return NextResponse.json({ ok: true });
}
