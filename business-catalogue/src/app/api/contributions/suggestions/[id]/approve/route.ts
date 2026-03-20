import { NextRequest, NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;
  const body = await request.json();
  const { reviewedBy, reviewComment } = body;

  const suggestion = await prisma.suggestion.update({
    where: { id },
    data: {
      status: "approved",
      reviewedBy: reviewedBy || null,
      reviewComment: reviewComment || null,
      reviewedAt: new Date(),
    },
  });

  return NextResponse.json(suggestion);
}
