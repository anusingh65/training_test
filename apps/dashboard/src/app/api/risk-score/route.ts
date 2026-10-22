import { NextRequest, NextResponse } from "next/server";

const ML_API_URL = process.env.ML_API_URL || "http://localhost:8000";

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const res = await fetch(`${ML_API_URL}/predict/risk`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });

    if (!res.ok) {
      throw new Error("ML API error");
    }

    const data = await res.json();
    return NextResponse.json(data);
  } catch {
    return NextResponse.json(
      { error: "Risk scoring unavailable", risk_score: 50, risk_level: "unknown", is_anomaly: false, contributing_factors: [] },
      { status: 200 }
    );
  }
}

// GET for heatmap data proxy
export async function GET(req: NextRequest) {
  const { searchParams } = new URL(req.url);
  const type = searchParams.get("type");

  try {
    let endpoint = "/analytics/summary";
    if (type === "heatmap") endpoint = "/heatmap";

    const res = await fetch(`${ML_API_URL}${endpoint}`);
    if (!res.ok) throw new Error("ML API error");

    const data = await res.json();
    return NextResponse.json(data);
  } catch {
    return NextResponse.json({ regions: [], total_drugs: 0 });
  }
}
