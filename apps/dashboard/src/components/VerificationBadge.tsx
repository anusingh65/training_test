const statusStyles: Record<string, string> = {
  verified: "bg-success-light text-success border border-success/20",
  approved: "bg-success-light text-success border border-success/20",
  suspicious: "bg-warning-light text-warning border border-warning/20",
  counterfeit: "bg-danger-light text-danger border border-danger/20",
  rejected: "bg-danger-light text-danger border border-danger/20",
  pending: "bg-gray-100 text-text-secondary border border-gray-200",
};

export default function VerificationBadge({ status }: { status: string }) {
  return (
    <span
      className={`text-xs px-2.5 py-1 rounded-full font-medium capitalize ${
        statusStyles[status] || statusStyles.pending
      }`}
    >
      {status}
    </span>
  );
}
