import { NextRequest, NextResponse } from "next/server";

export async function POST(request: NextRequest) {
  const baseUrl = process.env.API_BASE_URL
    ?? process.env.NEXT_PUBLIC_API_BASE_URL
    ?? "https://shootsignal-api-431147996077.europe-north1.run.app";
  try {
    const response = await fetch(`${baseUrl}/brief`, { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify(await request.json()), cache: "no-store" });
    return NextResponse.json(await response.json(), { status: response.status });
  } catch (error) {
    console.error("ShootSignal backend proxy failed", error);
    return NextResponse.json({ detail: "ShootSignal API is unavailable. Start the backend and add its credentials." }, { status: 503 });
  }
}
