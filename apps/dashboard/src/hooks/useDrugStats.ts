"use client";

import { useEffect, useState } from "react";
import { supabase } from "@/lib/supabase";
import { isMockMode, MOCK_DRUGS, MOCK_SCANS, MOCK_ALERTS } from "@/lib/mock-data";

interface DrugStats {
  totalDrugs: number;
  verificationRate: number;
  activeFlags: number;
  highRiskZones: number;
}

export function useDrugStats() {
  const [stats, setStats] = useState<DrugStats>({
    totalDrugs: 0,
    verificationRate: 0,
    activeFlags: 0,
    highRiskZones: 0,
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (isMockMode()) {
      const verified = MOCK_SCANS.filter((s) => s.result === "verified").length;
      const rate = Math.round((verified / MOCK_SCANS.length) * 100);
      const activeFlags = MOCK_ALERTS.filter(
        (a) => a.status === "pending" || a.status === "investigating"
      ).length;
      const riskLocations = new Set(
        MOCK_SCANS.filter((s) => s.result === "counterfeit").map((s) => s.location)
      );

      setStats({
        totalDrugs: MOCK_DRUGS.length,
        verificationRate: rate,
        activeFlags,
        highRiskZones: riskLocations.size,
      });
      setLoading(false);
      return;
    }

    async function fetchStats() {
      const [drugsRes, flagsRes, scansRes] = await Promise.all([
        supabase.from("drugs").select("id", { count: "exact", head: true }),
        supabase
          .from("flagged_reports")
          .select("id", { count: "exact", head: true })
          .in("status", ["pending", "investigating"]),
        supabase.from("verification_scans").select("result"),
      ]);

      const totalDrugs = drugsRes.count || 0;
      const activeFlags = flagsRes.count || 0;
      const scans = scansRes.data || [];
      const verified = scans.filter((s: any) => s.result === "verified").length;
      const verificationRate =
        scans.length > 0 ? Math.round((verified / scans.length) * 100) : 0;

      const { data: riskData } = await supabase
        .from("verification_scans")
        .select("location")
        .eq("result", "counterfeit");
      const uniqueLocations = new Set(
        (riskData || []).map((r: any) => r.location).filter(Boolean)
      );

      setStats({
        totalDrugs,
        verificationRate,
        activeFlags,
        highRiskZones: uniqueLocations.size,
      });
      setLoading(false);
    }

    fetchStats();
  }, []);

  return { stats, loading };
}
