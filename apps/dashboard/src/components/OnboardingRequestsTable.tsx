"use client";

import { useState } from "react";
import { CheckCircle, XCircle, AlertTriangle, X, ExternalLink } from "lucide-react";
import { isMockMode } from "@/lib/mock-data";
import VerificationBadge from "./VerificationBadge";
import { OnboardingRequest } from "@/hooks/useOnboardingRequests";

const roleBadgeColors: Record<string, string> = {
  pharmacy: "bg-blue-50 text-blue-700 border border-blue-200",
  distributor: "bg-purple-50 text-purple-700 border border-purple-200",
  supplier: "bg-amber-50 text-amber-700 border border-amber-200",
  manufacturer: "bg-teal-50 text-teal-700 border border-teal-200",
};

interface Props {
  requests: OnboardingRequest[];
  loading: boolean;
}

export default function OnboardingRequestsTable({ requests, loading }: Props) {
  const [selectedRequest, setSelectedRequest] = useState<OnboardingRequest | null>(null);

  async function handleAction(id: string, status: string) {
    if (isMockMode()) {
      alert(`[Mock] ${status.charAt(0).toUpperCase() + status.slice(1)} request ${id}`);
      return;
    }

    try {
      const res = await fetch("/api/onboarding-requests", {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ requestId: id, status }),
      });

      if (!res.ok) {
        const data = await res.json();
        alert(`Error: ${data.error}`);
      }
    } catch {
      alert("Failed to update request");
    }
  }

  return (
    <>
      <div className="bg-white border border-border rounded-lg shadow-card overflow-hidden">
        <table className="w-full">
          <thead>
            <tr className="border-b border-border text-left text-xs text-text-secondary uppercase tracking-wider bg-gray-50/50">
              <th className="px-6 py-4 font-medium">Business Name</th>
              <th className="px-6 py-4 font-medium">Role</th>
              <th className="px-6 py-4 font-medium">Owner</th>
              <th className="px-6 py-4 font-medium">Location</th>
              <th className="px-6 py-4 font-medium">Status</th>
              <th className="px-6 py-4 font-medium">Submitted</th>
              <th className="px-6 py-4 font-medium">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {loading ? (
              Array.from({ length: 5 }).map((_, i) => (
                <tr key={i}>
                  {Array.from({ length: 7 }).map((_, j) => (
                    <td key={j} className="px-6 py-4">
                      <div className="h-4 bg-gray-100 rounded animate-pulse w-24" />
                    </td>
                  ))}
                </tr>
              ))
            ) : requests.length === 0 ? (
              <tr>
                <td colSpan={7} className="px-6 py-12 text-center text-text-secondary">
                  No onboarding requests found
                </td>
              </tr>
            ) : (
              requests.map((req) => (
                <tr
                  key={req.id}
                  className="hover:bg-gray-50 transition-colors cursor-pointer"
                  onClick={() => setSelectedRequest(req)}
                >
                  <td className="px-6 py-4">
                    <div className="text-sm font-medium text-foreground">{req.business_name}</div>
                    <div className="text-xs text-text-tertiary font-mono mt-0.5">{req.license_number}</div>
                  </td>
                  <td className="px-6 py-4">
                    <span className={`text-xs px-2.5 py-1 rounded-full font-medium capitalize ${roleBadgeColors[req.role] || ""}`}>
                      {req.role}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-sm text-text-secondary">{req.owner_name}</td>
                  <td className="px-6 py-4 text-sm text-text-secondary">
                    {req.city}, {req.state}
                  </td>
                  <td className="px-6 py-4">
                    <VerificationBadge status={req.status} />
                  </td>
                  <td className="px-6 py-4 text-sm text-text-secondary">
                    {new Date(req.created_at).toLocaleDateString("en-IN", {
                      day: "numeric",
                      month: "short",
                      year: "numeric",
                    })}
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-1.5" onClick={(e) => e.stopPropagation()}>
                      <button
                        onClick={() => handleAction(req.id, "approved")}
                        className="p-1.5 rounded-md hover:bg-green-50 text-green-600 transition-colors"
                        title="Approve"
                      >
                        <CheckCircle size={16} />
                      </button>
                      <button
                        onClick={() => handleAction(req.id, "rejected")}
                        className="p-1.5 rounded-md hover:bg-red-50 text-red-600 transition-colors"
                        title="Reject"
                      >
                        <XCircle size={16} />
                      </button>
                      <button
                        onClick={() => handleAction(req.id, "suspicious")}
                        className="p-1.5 rounded-md hover:bg-yellow-50 text-yellow-600 transition-colors"
                        title="Mark Suspicious"
                      >
                        <AlertTriangle size={16} />
                      </button>
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
      <p className="text-xs text-text-tertiary mt-3 text-right">
        Showing {requests.length} request{requests.length !== 1 ? "s" : ""}
      </p>

      {/* Detail Modal */}
      {selectedRequest && (
        <div
          className="fixed inset-0 z-[100] flex items-center justify-center bg-black/40"
          onClick={() => setSelectedRequest(null)}
        >
          <div
            className="bg-white rounded-xl shadow-xl w-full max-w-2xl max-h-[85vh] overflow-y-auto m-4"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Modal Header */}
            <div className="flex items-center justify-between px-6 py-4 border-b border-border sticky top-0 bg-white rounded-t-xl">
              <div>
                <h2 className="text-lg font-semibold text-foreground">{selectedRequest.business_name}</h2>
                <div className="flex items-center gap-2 mt-1">
                  <span className={`text-xs px-2.5 py-0.5 rounded-full font-medium capitalize ${roleBadgeColors[selectedRequest.role] || ""}`}>
                    {selectedRequest.role}
                  </span>
                  <VerificationBadge status={selectedRequest.status} />
                </div>
              </div>
              <button
                onClick={() => setSelectedRequest(null)}
                className="p-2 rounded-lg hover:bg-gray-100 transition-colors"
              >
                <X size={18} />
              </button>
            </div>

            {/* Modal Body */}
            <div className="px-6 py-5 space-y-6">
              {/* Contact Info */}
              <Section title="Contact Information">
                <Field label="Email" value={selectedRequest.email} />
                <Field label="Phone" value={selectedRequest.mobile_number} />
                <Field label="Address" value={`${selectedRequest.address}, ${selectedRequest.city}, ${selectedRequest.state}, ${selectedRequest.country}`} />
                <Field label="GPS" value={`${selectedRequest.latitude}, ${selectedRequest.longitude}`} />
              </Section>

              {/* Business Details */}
              <Section title="Business Details">
                <Field label="Owner" value={selectedRequest.owner_name} />
                <Field label="License" value={`${selectedRequest.license_number} (expires ${selectedRequest.license_expiry_date})`} />
                <Field label="Company Reg." value={selectedRequest.company_registration_number} />
                <Field label="GST Number" value={selectedRequest.gst_number} />
                {selectedRequest.website && <Field label="Website" value={selectedRequest.website} />}
                <Field label="Description" value={selectedRequest.description} />
              </Section>

              {/* Blockchain Info */}
              <Section title="Blockchain Info">
                <Field label="Wallet Address" value={selectedRequest.wallet_address} mono />
              </Section>

              {/* Documents */}
              <Section title="Documents">
                {selectedRequest.documents && selectedRequest.documents.length > 0 ? (
                  <ul className="space-y-2">
                    {selectedRequest.documents.map((doc, i) => (
                      <li key={i} className="flex items-center gap-2 text-sm">
                        <ExternalLink size={14} className="text-primary shrink-0" />
                        <span className="text-foreground">{doc.name}</span>
                        <span className="text-text-tertiary capitalize">({doc.type.replace(/_/g, " ")})</span>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-sm text-text-tertiary">No documents uploaded</p>
                )}
              </Section>

              {/* Admin Review */}
              {(selectedRequest.admin_notes || selectedRequest.reviewed_by) && (
                <Section title="Admin Review">
                  {selectedRequest.admin_notes && <Field label="Notes" value={selectedRequest.admin_notes} />}
                  {selectedRequest.reviewed_by && <Field label="Reviewed By" value={selectedRequest.reviewed_by} />}
                  {selectedRequest.reviewed_at && (
                    <Field
                      label="Reviewed At"
                      value={new Date(selectedRequest.reviewed_at).toLocaleString("en-IN")}
                    />
                  )}
                </Section>
              )}
            </div>

            {/* Modal Footer */}
            <div className="flex items-center gap-3 px-6 py-4 border-t border-border sticky bottom-0 bg-white rounded-b-xl">
              <button
                onClick={() => {
                  handleAction(selectedRequest.id, "approved");
                  setSelectedRequest(null);
                }}
                className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white text-sm font-medium rounded-lg hover:bg-green-700 transition-colors"
              >
                <CheckCircle size={16} />
                Approve
              </button>
              <button
                onClick={() => {
                  handleAction(selectedRequest.id, "rejected");
                  setSelectedRequest(null);
                }}
                className="flex items-center gap-2 px-4 py-2 bg-red-600 text-white text-sm font-medium rounded-lg hover:bg-red-700 transition-colors"
              >
                <XCircle size={16} />
                Reject
              </button>
              <button
                onClick={() => {
                  handleAction(selectedRequest.id, "suspicious");
                  setSelectedRequest(null);
                }}
                className="flex items-center gap-2 px-4 py-2 bg-yellow-500 text-white text-sm font-medium rounded-lg hover:bg-yellow-600 transition-colors"
              >
                <AlertTriangle size={16} />
                Mark Suspicious
              </button>
              <div className="flex-1" />
              <button
                onClick={() => setSelectedRequest(null)}
                className="px-4 py-2 text-sm text-text-secondary hover:text-foreground transition-colors"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div>
      <h3 className="text-sm font-semibold text-foreground mb-3">{title}</h3>
      <div className="space-y-2">{children}</div>
    </div>
  );
}

function Field({ label, value, mono }: { label: string; value: string; mono?: boolean }) {
  return (
    <div className="flex gap-3 text-sm">
      <span className="text-text-secondary w-32 shrink-0">{label}</span>
      <span className={`text-foreground break-all ${mono ? "font-mono text-xs" : ""}`}>{value}</span>
    </div>
  );
}
