"use client";

import { useState, useRef } from "react";
import { api } from "@/lib/api";

interface VerifyResult {
  confidence: number;
  prediction: string;
  embedding_hash: string;
  on_chain_match?: boolean;
  on_chain_content_hash?: string;
  medicine_id?: number;
  processing_time_ms: number;
}

export default function VerifyPage() {
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [medicineId, setMedicineId] = useState("");
  const [result, setResult] = useState<VerifyResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);

  const onFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    if (!f) return;
    setFile(f);
    setPreview(URL.createObjectURL(f));
    setResult(null);
  };

  const verify = () => {
    if (!file) return;
    setLoading(true);
    setError("");
    const params: Record<string, string> = {};
    if (medicineId) params.medicine_id = medicineId;
    api
      .postFile("/api/verify-image", file, params)
      .then(setResult)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  };

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Pill Image Verification</h1>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-surface rounded-xl p-5 border border-white/5">
          <h2 className="font-semibold mb-4">Upload Pill Image</h2>

          <div
            onClick={() => inputRef.current?.click()}
            className="border-2 border-dashed border-white/10 rounded-xl p-8 text-center cursor-pointer hover:border-accent/40 transition-colors mb-4"
          >
            {preview ? (
              <img
                src={preview}
                alt="Preview"
                className="max-h-64 mx-auto rounded-lg"
              />
            ) : (
              <div className="text-muted">
                <div className="text-4xl mb-2">+</div>
                <div>Click to upload pill image</div>
                <div className="text-xs mt-1">JPEG, PNG, WebP, BMP, TIFF</div>
              </div>
            )}
          </div>
          <input
            ref={inputRef}
            type="file"
            accept="image/*"
            onChange={onFileChange}
            className="hidden"
          />

          <div className="mb-4">
            <label className="text-xs text-muted block mb-1">Medicine ID (optional)</label>
            <input
              type="text"
              value={medicineId}
              onChange={(e) => setMedicineId(e.target.value)}
              placeholder="On-chain medicine ID for hash verification"
              className="w-full bg-primary border border-white/10 rounded px-3 py-2 text-sm"
            />
          </div>

          <button
            onClick={verify}
            disabled={!file || loading}
            className="w-full bg-accent text-white py-2 rounded font-semibold text-sm disabled:opacity-50"
          >
            {loading ? "Verifying..." : "Verify Image"}
          </button>
        </div>

        <div>
          {error && (
            <div className="bg-red-500/10 border border-red-500/30 text-red-400 rounded-lg p-3 mb-4 text-sm">
              {error}
            </div>
          )}

          {result && (
            <div className="bg-surface rounded-xl p-5 border border-white/5">
              <div className="flex items-center gap-3 mb-4">
                <div
                  className={`w-4 h-4 rounded-full ${
                    result.prediction === "authentic"
                      ? "bg-green-500"
                      : result.prediction === "suspicious"
                      ? "bg-yellow-500"
                      : "bg-red-500"
                  }`}
                />
                <h2 className="font-semibold text-lg uppercase">
                  {result.prediction}
                </h2>
              </div>

              <div className="grid grid-cols-2 gap-4 mb-4">
                <div className="bg-primary rounded-lg p-3 border border-white/5">
                  <div className="text-xs text-muted">Confidence</div>
                  <div className="text-2xl font-bold">
                    {(result.confidence * 100).toFixed(1)}%
                  </div>
                </div>
                <div className="bg-primary rounded-lg p-3 border border-white/5">
                  <div className="text-xs text-muted">Prediction</div>
                  <div
                    className={`text-2xl font-bold ${
                      result.prediction === "authentic"
                        ? "text-green-400"
                        : result.prediction === "suspicious"
                        ? "text-yellow-400"
                        : "text-red-400"
                    }`}
                  >
                    {result.prediction}
                  </div>
                </div>
              </div>

              {result.embedding_hash && (
                <div className="bg-primary rounded-lg p-3 border border-white/5 mb-4">
                  <div className="text-xs text-muted mb-1">Embedding Hash</div>
                  <div className="font-mono text-xs break-all">{result.embedding_hash}</div>
                </div>
              )}

              {result.on_chain_match !== undefined && (
                <div className="bg-primary rounded-lg p-3 border border-white/5 mb-4">
                  <div className="text-xs text-muted">On-Chain Match</div>
                  <div
                    className={`font-bold ${
                      result.on_chain_match ? "text-green-400" : "text-red-400"
                    }`}
                  >
                    {result.on_chain_match ? "MATCH" : "MISMATCH"}
                  </div>
                </div>
              )}

              <div className="text-xs text-muted">
                Processing: {result.processing_time_ms}ms
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
