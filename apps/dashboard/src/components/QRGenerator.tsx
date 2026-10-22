"use client";

import { QRCodeSVG } from "qrcode.react";

interface QRGeneratorProps {
  drugId: string;
  batchId: string;
  mfgDate: string;
  expiryDate: string;
  manufacturer: string;
  hash: string;
}

export default function QRGenerator({
  drugId,
  batchId,
  mfgDate,
  expiryDate,
  manufacturer,
  hash,
}: QRGeneratorProps) {
  const qrPayload = `medichain://${drugId}|${batchId}|${mfgDate}|${expiryDate}|${manufacturer}|${hash}`;

  return (
    <div className="flex flex-col items-center gap-4 p-6 bg-white rounded-xl">
      <QRCodeSVG value={qrPayload} size={200} level="H" />
      <p className="text-xs text-gray-600 max-w-[200px] text-center break-all font-mono">
        {qrPayload}
      </p>
    </div>
  );
}
