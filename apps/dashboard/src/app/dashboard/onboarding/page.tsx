"use client";

import { useMemo, useState } from "react";
import PageHeader from "@/components/PageHeader";
import OnboardingRequestsTable from "@/components/OnboardingRequestsTable";
import { useOnboardingRequests } from "@/hooks/useOnboardingRequests";

export default function OnboardingPage() {
  const { requests, loading } = useOnboardingRequests();
  const [statusFilter, setStatusFilter] = useState("all");
  const [roleFilter, setRoleFilter] = useState("all");

  const filtered = useMemo(() => {
    return requests.filter((r) => {
      if (statusFilter !== "all" && r.status !== statusFilter) return false;
      if (roleFilter !== "all" && r.role !== roleFilter) return false;
      return true;
    });
  }, [requests, statusFilter, roleFilter]);

  return (
    <>
      <PageHeader
        title="Onboarding Requests"
        description="Review and manage supply chain entity applications"
        breadcrumbs={[
          { label: "Dashboard", href: "/dashboard" },
          { label: "Onboarding Requests" },
        ]}
      />

      <div className="flex gap-4 mb-6">
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="bg-white border border-border rounded-md px-4 py-2.5 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary"
        >
          <option value="all">All Status</option>
          <option value="pending">Pending</option>
          <option value="approved">Approved</option>
          <option value="rejected">Rejected</option>
          <option value="suspicious">Suspicious</option>
        </select>
        <select
          value={roleFilter}
          onChange={(e) => setRoleFilter(e.target.value)}
          className="bg-white border border-border rounded-md px-4 py-2.5 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary"
        >
          <option value="all">All Roles</option>
          <option value="pharmacy">Pharmacy</option>
          <option value="distributor">Distributor</option>
          <option value="supplier">Supplier</option>
          <option value="manufacturer">Manufacturer</option>
        </select>
      </div>

      <OnboardingRequestsTable requests={filtered} loading={loading} />
    </>
  );
}
