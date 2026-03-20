import { NextRequest, NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";

export async function GET(request: NextRequest) {
  const entityType = request.nextUrl.searchParams.get("entityType");
  const entityKey = request.nextUrl.searchParams.get("entityKey");

  if (!entityType || !entityKey) {
    return NextResponse.json({ error: "entityType and entityKey are required" }, { status: 400 });
  }

  const annotations = await prisma.annotation.findMany({
    where: { entityType, entityKey },
    orderBy: { upvoteCount: "desc" },
  });

  return NextResponse.json(annotations);
}

export async function POST(request: NextRequest) {
  const body = await request.json();
  const { entityType, entityKey, annotationType, content, author } = body;

  if (!entityType || !entityKey || !annotationType || !content || !author) {
    return NextResponse.json(
      { error: "entityType, entityKey, annotationType, content, and author are required" },
      { status: 400 }
    );
  }

  const annotation = await prisma.annotation.create({
    data: { entityType, entityKey, annotationType, content, author },
  });

  return NextResponse.json(annotation, { status: 201 });
}
