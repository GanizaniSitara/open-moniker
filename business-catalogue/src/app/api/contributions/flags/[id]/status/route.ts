import { NextRequest, NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";

export async function PATCH(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;
  const body = await request.json();
  const { status, resolvedBy } = body;

  if (!status) {
    return NextResponse.json({ error: "status is required" }, { status: 400 });
  }

  const flag = await prisma.flag.update({
    where: { id },
    data: {
      status,
      resolvedBy: resolvedBy || null,
      resolvedAt: ["resolved", "dismissed"].includes(status) ? new Date() : null,
    },
  });

  return NextResponse.json(flag);
}
