"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Search } from "lucide-react";
import { supabase } from "@/lib/supabase";
import { isMockMode, MOCK_DRUGS } from "@/lib/mock-data";
import VerificationBadge from "./VerificationBadge";

interface Drug {
  id: string;
  drug_id: string;
  batch_id: string;
  name: string;
  manufacturer: string;
  status: string;
  flagged: boolean;
  created_at: string;
}

export default function DrugTable() {
  const [drugs, setDrugs] = useState<Drug[]>([]);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (isMockMode()) {
      let data = [...MOCK_DRUGS] as Drug[];
      if (statusFilter !== "all") {
        data = data.filter((d) => d.status === statusFilter);
      }
      setDrugs(data);
      setLoading(false);
      return;
    }

    async function fetchDrugs() {
      let query = supabase
        .from("drugs")
        .select("*")
        .order("created_at", { ascending: false });

      if (statusFilter !== "all") {
        query = query.eq("status", statusFilter);
      }

      const { data } = await query;
      setDrugs(data || []);
      setLoading(false);
    }
    fetchDrugs();
  }, [statusFilter]);

  const filtered = drugs.filter(
    (d) =>
      d.name.toLowerCase().includes(search.toLowerCase()) ||
      d.drug_id.toLowerCase().includes(search.toLowerCase()) ||
      d.batch_id.toLowerCase().includes(search.toLowerCase()) ||
      d.manufacturer.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div>
      <div className="flex gap-4 mb-6">
        <div className="relative flex-1">
          <Search
            size={16}
            className="absolute left-3 top-1/2 -translate-y-1/2 text-text-tertiary"
          />
          <input
            type="text"
            placeholder="Search drugs, batches, manufacturers..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-10 pr-4 py-2.5 bg-white border border-border rounded-md text-sm text-foreground placeholder-text-tertiary focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-colors"
          />
        </div>
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="bg-white border border-border rounded-md px-4 py-2.5 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary"
        >
          <option value="all">All Status</option>
          <option value="verified">Verified</option>
          <option value="suspicious">Suspicious</option>
          <option value="counterfeit">Counterfeit</option>
          <option value="pending">Pending</option>
        </select>
      </div>

      <div className="bg-white border border-border rounded-lg shadow-card overflow-hidden">
        <table className="w-full">
          <thead>
            <tr className="border-b border-border text-left text-xs text-text-secondary uppercase tracking-wider bg-gray-50/50">
              <th className="px-6 py-4 font-medium">Drug ID</th>
              <th className="px-6 py-4 font-medium">Name</th>
              <th className="px-6 py-4 font-medium">Batch</th>
              <th className="px-6 py-4 font-medium">Manufacturer</th>
              <th className="px-6 py-4 font-medium">Status</th>
              <th className="px-6 py-4 font-medium">Flagged</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {loading ? (
              Array.from({ length: 5 }).map((_, i) => (
                <tr key={i}>
                  {Array.from({ length: 6 }).map((_, j) => (
                    <td key={j} className="px-6 py-4">
                      <div className="h-4 bg-gray-100 rounded animate-pulse w-24" />
                    </td>
                  ))}
                </tr>
              ))
            ) : filtered.length === 0 ? (
              <tr>
                <td colSpan={6} className="px-6 py-12 text-center text-text-secondary">
                  No drugs found
                </td>
              </tr>
            ) : (
              filtered.map((drug) => (
                <tr
                  key={drug.id}
                  className="hover:bg-gray-50 transition-colors cursor-pointer"
                >
                  <td className="px-6 py-4">
                    <Link
                      href={`/dashboard/drugs/${drug.drug_id}`}
                      className="text-primary hover:underline font-mono text-sm"
                    >
                      {drug.drug_id}
                    </Link>
                  </td>
                  <td className="px-6 py-4 text-sm font-medium text-foreground">{drug.name}</td>
                  <td className="px-6 py-4 text-sm font-mono text-text-secondary">
                    {drug.batch_id}
                  </td>
                  <td className="px-6 py-4 text-sm text-text-secondary">{drug.manufacturer}</td>
                  <td className="px-6 py-4">
                    <VerificationBadge status={drug.status} />
                  </td>
                  <td className="px-6 py-4">
                    {drug.flagged && (
                      <span className="text-xs bg-danger-light text-danger border border-danger/20 px-2 py-1 rounded-full font-medium">
                        Flagged
                      </span>
                    )}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
      <p className="text-xs text-text-tertiary mt-3 text-right">
        Showing {filtered.length} of {drugs.length} drugs
      </p>
    </div>
  );
}
