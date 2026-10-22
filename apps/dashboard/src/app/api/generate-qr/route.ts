import { NextRequest, NextResponse } from "next/server";
import crypto from "crypto";

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const { drugId, batchId, mfgDate, expiryDate, manufacturer } = body;

    if (!drugId || !batchId || !mfgDate || !expiryDate || !manufacturer) {
      return NextResponse.json({ error: "Missing required fields" }, { status: 400 });
    }

    const payload = `${drugId}|${batchId}|${mfgDate}|${expiryDate}|${manufacturer}`;
    const hash = crypto.createHash("sha256").update(payload).digest("hex");
    const qrData = `medichain://${payload}|${hash}`;

    return NextResponse.json({ hash, qrData });
  } catch {
    return NextResponse.json({ error: "Failed to generate QR" }, { status: 500 });
  }
}
