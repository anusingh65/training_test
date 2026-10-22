"use client";

import { useEffect, useState } from "react";
import { supabase } from "@/lib/supabase";
import { isMockMode, MOCK_ONBOARDING_REQUESTS } from "@/lib/mock-data";

export interface OnboardingRequest {
  id: string;
  business_name: string;
  role: string;
  owner_name: string;
  email: string;
  mobile_number: string;
  address: string;
  city: string;
  state: string;
  country: string;
  latitude: number;
  longitude: number;
  license_number: string;
  license_expiry_date: string;
  public_key: string;
  wallet_address: string;
  documents: { type: string; name: string; url: string }[];
  company_registration_number: string;
  gst_number: string;
  website: string | null;
  description: string;
  status: string;
  admin_notes: string | null;
  reviewed_by: string | null;
  reviewed_at: string | null;
  created_at: string;
  updated_at: string;
}

export function useOnboardingRequests() {
  const [requests, setRequests] = useState<OnboardingRequest[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (isMockMode()) {
      setRequests(MOCK_ONBOARDING_REQUESTS as OnboardingRequest[]);
      setLoading(false);
      return;
    }

    supabase
      .from("onboarding_requests")
      .select("*")
      .order("created_at", { ascending: false })
      .then(({ data }) => {
        if (data) setRequests(data);
        setLoading(false);
      });

    const channel = supabase
      .channel("onboarding_requests_changes")
      .on(
        "postgres_changes",
        { event: "INSERT", schema: "public", table: "onboarding_requests" },
        (payload: any) => {
          setRequests((prev) => [payload.new as OnboardingRequest, ...prev]);
        }
      )
      .on(
        "postgres_changes",
        { event: "UPDATE", schema: "public", table: "onboarding_requests" },
        (payload: any) => {
          setRequests((prev) =>
            prev.map((r) =>
              r.id === (payload.new as OnboardingRequest).id
                ? (payload.new as OnboardingRequest)
                : r
            )
          );
        }
      )
      .subscribe();

    return () => {
      supabase.removeChannel(channel);
    };
  }, []);

  return { requests, loading };
}
