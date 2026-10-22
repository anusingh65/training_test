import { NextRequest, NextResponse } from "next/server";
import crypto from "crypto";
import { createServiceClient } from "@/lib/supabase";

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const { name, batchId, manufacturer, manufactureDate, expiryDate } = body;

    if (!name || !batchId || !manufacturer || !manufactureDate || !expiryDate) {
      return NextResponse.json({ error: "Missing required fields" }, { status: 400 });
    }

    // Generate drug ID
    const drugId = `DRG-${Date.now().toString(36).toUpperCase()}`;

    // Compute metadata hash
    const payload = `${drugId}|${batchId}|${manufactureDate}|${expiryDate}|${manufacturer}`;
    const metadataHash = crypto.createHash("sha256").update(payload).digest("hex");

    // Create metadata for IPFS
    const metadata = {
      drugId,
      name,
      batchId,
      manufacturer,
      manufactureDate,
      expiryDate,
      metadataHash,
      registeredAt: new Date().toISOString(),
    };

    // Upload to IPFS via Pinata (if configured)
    let ipfsCid: string | null = null;
    const pinataJwt = process.env.PINATA_JWT;

    if (pinataJwt) {
      try {
        const pinataRes = await fetch("https://api.pinata.cloud/pinning/pinJSONToIPFS", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${pinataJwt}`,
          },
          body: JSON.stringify({
            pinataContent: metadata,
            pinataMetadata: { name: `medichain-${drugId}` },
          }),
        });

        if (pinataRes.ok) {
          const pinataData = await pinataRes.json();
          ipfsCid = pinataData.IpfsHash;
        }
      } catch {
        console.warn("IPFS upload failed, continuing without IPFS");
      }
    }

    // Insert into Supabase
    const supabase = createServiceClient();
    const { error: dbError } = await supabase.from("drugs").insert({
      drug_id: drugId,
      batch_id: batchId,
      name,
      manufacturer,
      manufacture_date: manufactureDate,
      expiry_date: expiryDate,
      metadata_hash: metadataHash,
      qr_hash: metadataHash,
      ipfs_cid: ipfsCid,
      status: "verified",
    });

    if (dbError) {
      return NextResponse.json({ error: dbError.message }, { status: 500 });
    }

    // Insert initial custody event
    await supabase.from("custody_events").insert({
      drug_id: drugId,
      to_entity: manufacturer,
      event_type: "manufactured",
      location: "",
      timestamp: new Date().toISOString(),
    });

    return NextResponse.json({
      drugId,
      hash: metadataHash,
      ipfsCid,
    });
  } catch {
    return NextResponse.json({ error: "Registration failed" }, { status: 500 });
  }
}
