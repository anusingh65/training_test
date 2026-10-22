import { NextRequest, NextResponse } from "next/server";
import crypto from "crypto";
import { createServiceClient } from "@/lib/supabase";

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const { drugId, batchId, mfgDate, expiryDate, manufacturer, providedHash } = body;

    if (!drugId || !providedHash) {
      return NextResponse.json({ error: "Missing required fields" }, { status: 400 });
    }

    // Recompute hash
    const payload = `${drugId}|${batchId}|${mfgDate}|${expiryDate}|${manufacturer}`;
    const computedHash = crypto.createHash("sha256").update(payload).digest("hex");

    const supabase = createServiceClient();
    const { data: drug } = await supabase
      .from("drugs")
      .select("*")
      .eq("drug_id", drugId)
      .single();

    if (!drug) {
      return NextResponse.json({
        status: "counterfeit",
        message: "Drug not found in database",
        hashMatch: false,
      });
    }

    const hashMatch = computedHash === providedHash && providedHash === drug.qr_hash;

    let status: "verified" | "suspicious" | "counterfeit";
    if (hashMatch && !drug.flagged) {
      status = "verified";
    } else if (drug.flagged) {
      status = "counterfeit";
    } else {
      status = "suspicious";
    }

    return NextResponse.json({
      status,
      hashMatch,
      drug: {
        drugId: drug.drug_id,
        name: drug.name,
        manufacturer: drug.manufacturer,
        batchId: drug.batch_id,
        flagged: drug.flagged,
      },
    });
  } catch {
    return NextResponse.json({ error: "Verification failed" }, { status: 500 });
  }
}
