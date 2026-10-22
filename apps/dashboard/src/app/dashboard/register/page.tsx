"use client";

import { useState } from "react";
import { PlusCircle, CheckCircle2, Loader2 } from "lucide-react";
import QRGenerator from "@/components/QRGenerator";
import { isMockMode } from "@/lib/mock-data";

export default function RegisterDrugPage() {
  const [form, setForm] = useState({
    name: "",
    batchId: "",
    manufacturer: "",
    manufactureDate: "",
    expiryDate: "",
  });
  const [result, setResult] = useState<{
    drugId: string;
    hash: string;
    txHash?: string;
    ipfsCid?: string;
  } | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError("");

    if (isMockMode()) {
      await new Promise((r) => setTimeout(r, 1500));
      const mockId = `DRUG-${Date.now().toString(36).toUpperCase()}`;
      const payload = `${mockId}|${form.batchId}|${form.manufactureDate}|${form.expiryDate}|${form.manufacturer}`;
      const encoder = new TextEncoder();
      const data = encoder.encode(payload);
      const hashBuffer = await crypto.subtle.digest("SHA-256", data);
      const hashArray = Array.from(new Uint8Array(hashBuffer));
      const hash = hashArray.map((b) => b.toString(16).padStart(2, "0")).join("");
      setResult({
        drugId: mockId,
        hash,
        txHash: `0x${hash.slice(0, 64)}`,
        ipfsCid: `Qm${hash.slice(0, 44)}`,
      });
      setLoading(false);
      return;
    }

    try {
      const res = await fetch("/api/register-drug", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(form),
      });

      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.error || "Registration failed");
      }

      const data = await res.json();
      setResult(data);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Registration failed");
    } finally {
      setLoading(false);
    }
  }

  const inputClass = "w-full px-4 py-2.5 bg-background border border-border rounded-lg text-sm text-white focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary/30 transition-all placeholder:text-gray-600";

  return (
    <div className="max-w-2xl">
      <div className="mb-8">
        <h1 className="text-2xl font-bold">Register New Drug</h1>
        <p className="text-gray-500 text-sm mt-1">
          Add a pharmaceutical to the blockchain-verified supply chain
          {isMockMode() && (
            <span className="ml-2 text-xs bg-primary/10 text-primary px-2 py-0.5 rounded-full">
              Demo Mode
            </span>
          )}
        </p>
      </div>

      <form onSubmit={handleSubmit} className="bg-card border border-border rounded-xl p-6 space-y-5 animate-fade-in">
        <div>
          <label className="block text-sm text-gray-400 mb-1.5 font-medium">Drug Name</label>
          <input
            type="text"
            required
            value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value })}
            className={inputClass}
            placeholder="e.g. Amoxicillin 500mg"
          />
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm text-gray-400 mb-1.5 font-medium">Batch ID</label>
            <input
              type="text"
              required
              value={form.batchId}
              onChange={(e) => setForm({ ...form, batchId: e.target.value })}
              className={inputClass}
              placeholder="e.g. BAT-2024-001"
            />
          </div>
          <div>
            <label className="block text-sm text-gray-400 mb-1.5 font-medium">Manufacturer</label>
            <input
              type="text"
              required
              value={form.manufacturer}
              onChange={(e) => setForm({ ...form, manufacturer: e.target.value })}
              className={inputClass}
              placeholder="e.g. Sun Pharmaceuticals"
            />
          </div>
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm text-gray-400 mb-1.5 font-medium">Manufacture Date</label>
            <input
              type="date"
              required
              value={form.manufactureDate}
              onChange={(e) => setForm({ ...form, manufactureDate: e.target.value })}
              className={inputClass}
            />
          </div>
          <div>
            <label className="block text-sm text-gray-400 mb-1.5 font-medium">Expiry Date</label>
            <input
              type="date"
              required
              value={form.expiryDate}
              onChange={(e) => setForm({ ...form, expiryDate: e.target.value })}
              className={inputClass}
            />
          </div>
        </div>

        {error && (
          <div className="bg-counterfeit/10 border border-counterfeit/20 text-counterfeit text-sm rounded-lg px-4 py-3">
            {error}
          </div>
        )}

        <button
          type="submit"
          disabled={loading}
          className="w-full py-3 bg-primary text-white rounded-lg font-medium hover:bg-primary/90 transition-all disabled:opacity-50 flex items-center justify-center gap-2"
        >
          {loading ? (
            <>
              <Loader2 size={16} className="animate-spin" />
              Registering on Blockchain...
            </>
          ) : (
            <>
              <PlusCircle size={16} />
              Register Drug
            </>
          )}
        </button>
      </form>

      {result && (
        <div className="mt-6 bg-card border border-verified/30 rounded-xl p-6 animate-fade-in">
          <div className="flex items-center gap-2 mb-4">
            <CheckCircle2 size={20} className="text-verified" />
            <h2 className="text-lg font-semibold text-verified">Drug Registered Successfully</h2>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-3 text-sm">
              <div className="bg-background/50 rounded-lg p-3 space-y-2">
                <p>
                  <span className="text-gray-500 text-xs uppercase tracking-wider">Drug ID</span>
                  <br />
                  <span className="font-mono text-primary">{result.drugId}</span>
                </p>
                <p>
                  <span className="text-gray-500 text-xs uppercase tracking-wider">SHA-256 Hash</span>
                  <br />
                  <span className="font-mono text-xs text-gray-300 break-all">{result.hash}</span>
                </p>
                {result.txHash && (
                  <p>
                    <span className="text-gray-500 text-xs uppercase tracking-wider">Transaction</span>
                    <br />
                    <a
                      href={`https://amoy.polygonscan.com/tx/${result.txHash}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-primary hover:underline font-mono text-xs"
                    >
                      {result.txHash.slice(0, 20)}...
                    </a>
                  </p>
                )}
                {result.ipfsCid && (
                  <p>
                    <span className="text-gray-500 text-xs uppercase tracking-wider">IPFS CID</span>
                    <br />
                    <span className="font-mono text-xs text-gray-300">{result.ipfsCid}</span>
                  </p>
                )}
              </div>
            </div>
            <div className="flex justify-center items-start">
              <QRGenerator
                drugId={result.drugId}
                batchId={form.batchId}
                mfgDate={form.manufactureDate}
                expiryDate={form.expiryDate}
                manufacturer={form.manufacturer}
                hash={result.hash}
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
