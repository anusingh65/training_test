import DrugTable from "@/components/DrugTable";

export default function DrugsPage() {
  return (
    <div>
      <div className="mb-8">
        <h1 className="text-2xl font-bold">Drug Registry</h1>
        <p className="text-gray-500 text-sm mt-1">
          All registered pharmaceuticals in the supply chain
        </p>
      </div>
      <DrugTable />
    </div>
  );
}
