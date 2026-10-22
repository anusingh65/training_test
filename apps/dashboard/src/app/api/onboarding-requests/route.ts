import { NextRequest, NextResponse } from "next/server";
import { createServiceClient } from "@/lib/supabase";

const VALID_STATUSES = ["approved", "rejected", "suspicious"];

export async function PATCH(req: NextRequest) {
  try {
    const body = await req.json();
    const { requestId, status, admin_notes } = body;

    if (!requestId || !status) {
      return NextResponse.json(
        { error: "Missing requestId or status" },
        { status: 400 }
      );
    }

    if (!VALID_STATUSES.includes(status)) {
      return NextResponse.json(
        { error: `Invalid status. Must be one of: ${VALID_STATUSES.join(", ")}` },
        { status: 400 }
      );
    }

    const supabase = createServiceClient();

    const { error } = await supabase
      .from("onboarding_requests")
      .update({
        status,
        admin_notes: admin_notes || null,
        reviewed_by: "admin@medichain.io",
        reviewed_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      })
      .eq("id", requestId);

    if (error) {
      return NextResponse.json({ error: error.message }, { status: 500 });
    }

    return NextResponse.json({ success: true });
  } catch {
    return NextResponse.json(
      { error: "Failed to update onboarding request" },
      { status: 500 }
    );
  }
}
