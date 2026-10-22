import HeatMap from "@/components/HeatMap";

export default function HeatmapPage() {
  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold">Risk Heatmap</h1>
        <p className="text-gray-500 text-sm mt-1">
          Geographic distribution of counterfeit drug risk across regions
        </p>
      </div>
      <HeatMap fullScreen />
    </div>
  );
}
