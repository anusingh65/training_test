import Sidebar from "@/components/Sidebar";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="flex min-h-screen bg-background dashboard-shell">
      <Sidebar />
      <main className="ml-64 flex-1">
        <div className="max-w-[1440px] p-6 lg:p-8">{children}</div>
      </main>
    </div>
  );
}
