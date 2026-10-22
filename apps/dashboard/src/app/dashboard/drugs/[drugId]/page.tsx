"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { supabase } from "@/lib/supabase";
import { isMockMode, MOCK_DRUGS, MOCK_CUSTODY_EVENTS } from "@/lib/mock-data";
import VerificationBadge from "@/components/VerificationBadge";
import SupplyChainTimeline from "@/components/SupplyChainTimeline";

interface Drug {
  drug_id: string;
  batch_id: string;
  name: string;
  manufacturer: string;
  manufacture_date: string;
  expiry_date: string;
  status: string;
  flagged: boolean;
  ipfs_cid: string | null;
  blockchain_tx_hash: string | null;
  metadata_hash: string;
}

interface CustodyEvent {
  id: string;
  from_entity: string | null;
  to_entity: string;
  event_type: string;
  location: string;
  timestamp: string;
  blockchain_tx_hash?: string;
}

export default function DrugDetailPage() {
  const params = useParams();
  const drugId = params.drugId as string;
  const [drug, setDrug] = useState<Drug | null>(null);
  const [events, setEvents] = useState<CustodyEvent[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (isMockMode()) {
      const found = MOCK_DRUGS.find((d) => d.drug_id === drugId) as any;
      if (found) setDrug(found);
      setEvents((MOCK_CUSTODY_EVENTS[drugId] || []) as CustodyEvent[]);
      setLoading(false);
      return;
    }

    async function fetchData() {
      const [drugRes, eventsRes] = await Promise.all([
        supabase.from("drugs").select("*").eq("drug_id", drugId).single(),
        supabase
          .from("custody_events")
          .select("*")
          .eq("drug_id", drugId)
          .order("timestamp", { ascending: true }),
      ]);

      if (drugRes.data) setDrug(drugRes.data);
      if (eventsRes.data) setEvents(eventsRes.data);
      setLoading(false);
    }
    fetchData();
  }, [drugId]);

  if (loading) {
    return (
      <div className="space-y-4">
        <div className="h-8 bg-border rounded animate-pulse w-64" />
        <div className="h-64 bg-card border border-border rounded-xl animate-pulse" />
      </div>
    );
  }

  if (!drug) {
    return (
      <div className="flex flex-col items-center justify-center h-64 text-gray-500">
        <p className="text-lg">Drug not found</p>
        <p className="text-sm mt-2">ID: {drugId}</p>
      </div>
    );
  }

  return (
    <div>
      <div className="flex items-center gap-4 mb-6">
        <h1 className="text-2xl font-bold">{drug.name}</h1>
        <VerificationBadge status={drug.status} />
        {drug.flagged && (
          <span className="text-xs bg-counterfeit/10 text-counterfeit px-3 py-1 rounded-full font-medium">
            Flagged
          </span>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 bg-card border border-border rounded-xl p-6">
          <h2 className="text-lg font-semibold mb-4">Drug Information</h2>
          <div className="grid grid-cols-2 gap-y-5 gap-x-8 text-sm">
            <InfoField label="Drug ID" value={drug.drug_id} mono />
            <InfoField label="Batch ID" value={drug.batch_id} mono />
            <InfoField label="Manufacturer" value={drug.manufacturer} />
            <InfoField label="Manufacture Date" value={drug.manufacture_date} />
            <InfoField label="Expiry Date" value={drug.expiry_date} />
            <InfoField label="Metadata Hash" value={drug.metadata_hash} mono truncate />
            {drug.ipfs_cid && (
              <div>
                <p className="text-gray-500 text-xs mb-1">IPFS CID</p>
                <a
                  href={`https://gateway.pinata.cloud/ipfs/${drug.ipfs_cid}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-primary hover:underline font-mono text-xs"
                >
                  {drug.ipfs_cid}
                </a>
              </div>
            )}
            {drug.blockchain_tx_hash && (
              <div>
                <p className="text-gray-500 text-xs mb-1">Blockchain TX</p>
                <a
                  href={`https://amoy.polygonscan.com/tx/${drug.blockchain_tx_hash}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-primary hover:underline font-mono text-xs"
                >
                  {drug.blockchain_tx_hash.slice(0, 16)}...
                </a>
              </div>
            )}
          </div>
        </div>

        <div className="bg-card border border-border rounded-xl p-6">
          <h2 className="text-lg font-semibold mb-4">Supply Chain</h2>
          {events.length > 0 ? (
            <SupplyChainTimeline events={events} />
          ) : (
            <p className="text-gray-500 text-sm text-center py-8">
              No custody events recorded
            </p>
          )}
        </div>
      </div>
    </div>
  );
}

function InfoField({
  label,
  value,
  mono,
  truncate,
}: {
  label: string;
  value: string;
  mono?: boolean;
  truncate?: boolean;
}) {
  return (
    <div>
      <p className="text-gray-500 text-xs mb-1">{label}</p>
      <p
        className={`${mono ? "font-mono text-xs" : ""} ${
          truncate ? "truncate" : ""
        }`}
      >
        {value}
      </p>
    </div>
  );
}
