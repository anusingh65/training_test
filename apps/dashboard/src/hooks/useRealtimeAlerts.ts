"use client";

import { useEffect, useState } from "react";
import { supabase } from "@/lib/supabase";
import { isMockMode, MOCK_ALERTS } from "@/lib/mock-data";

interface Alert {
  id: string;
  drug_id: string;
  reason: string;
  description: string;
  severity: string;
  status: string;
  location: string;
  created_at: string;
}

export function useRealtimeAlerts() {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (isMockMode()) {
      setAlerts(MOCK_ALERTS as Alert[]);
      setLoading(false);
      return;
    }

    supabase
      .from("flagged_reports")
      .select("*")
      .order("created_at", { ascending: false })
      .limit(50)
      .then(({ data }) => {
        if (data) setAlerts(data);
        setLoading(false);
      });

    const channel = supabase
      .channel("flagged_reports_changes")
      .on(
        "postgres_changes",
        { event: "INSERT", schema: "public", table: "flagged_reports" },
        (payload: any) => {
          setAlerts((prev) => [payload.new as Alert, ...prev]);
        }
      )
      .on(
        "postgres_changes",
        { event: "UPDATE", schema: "public", table: "flagged_reports" },
        (payload: any) => {
          setAlerts((prev) =>
            prev.map((a) =>
              a.id === (payload.new as Alert).id ? (payload.new as Alert) : a
            )
          );
        }
      )
      .subscribe();

    return () => {
      supabase.removeChannel(channel);
    };
  }, []);

  return { alerts, loading };
}
