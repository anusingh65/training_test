import AlertFeed from "@/components/AlertFeed";
import PageHeader from "@/components/PageHeader";

export default function AlertsPage() {
  return (
    <div>
      <PageHeader
        title="Alert Center"
        description="Flagged reports and suspicious activity monitoring"
        breadcrumbs={[
          { label: "Dashboard", href: "/dashboard" },
          { label: "Alerts" },
        ]}
      />
      <div className="max-w-3xl">
        <AlertFeed />
      </div>
    </div>
  );
}
