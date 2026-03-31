import { NextRequest, NextResponse } from "next/server";
import { fetchTree } from "@/lib/api-client";

export async function GET(request: NextRequest) {
  try {
    const depthParam = request.nextUrl.searchParams.get("depth");
    const depth = depthParam != null ? Number(depthParam) : undefined;
    const tree = await fetchTree(depth);
    return NextResponse.json(tree);
  } catch {
    return NextResponse.json([], { status: 502 });
  }
}
