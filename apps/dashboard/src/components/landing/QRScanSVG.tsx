"use client";

import { motion } from "framer-motion";

export default function QRScanSVG({ size = 200 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 200 200" fill="none" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <linearGradient id="scanLine" x1="0%" y1="0%" x2="100%" y2="0%">
          <stop offset="0%" stopColor="#3D7A6B" stopOpacity="0" />
          <stop offset="50%" stopColor="#3D7A6B" stopOpacity="1" />
          <stop offset="100%" stopColor="#3D7A6B" stopOpacity="0" />
        </linearGradient>
        <filter id="scanGlow">
          <feGaussianBlur stdDeviation="3" result="coloredBlur" />
          <feMerge>
            <feMergeNode in="coloredBlur" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
      </defs>

      {/* Phone outline */}
      <motion.rect
        x="40" y="15" width="120" height="170" rx="16"
        fill="#FFFFFF"
        stroke="#3D7A6B"
        strokeWidth="2"
        initial={{ pathLength: 0, opacity: 0 }}
        animate={{ pathLength: 1, opacity: 1 }}
        transition={{ duration: 1.5 }}
      />

      {/* Screen area */}
      <rect x="50" y="35" width="100" height="130" rx="4" fill="#F5F4F1" />

      {/* Notch */}
      <rect x="82" y="20" width="36" height="6" rx="3" fill="#CABFAC" />

      {/* QR Code pattern */}
      <motion.g
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 1 }}
      >
        {/* Top-left finder */}
        <rect x="60" y="48" width="22" height="22" rx="2" fill="none" stroke="#6B6560" strokeWidth="2" />
        <rect x="64" y="52" width="14" height="14" rx="1" fill="none" stroke="#6B6560" strokeWidth="1" />
        <rect x="68" y="56" width="6" height="6" fill="#6B6560" />

        {/* Top-right finder */}
        <rect x="118" y="48" width="22" height="22" rx="2" fill="none" stroke="#6B6560" strokeWidth="2" />
        <rect x="122" y="52" width="14" height="14" rx="1" fill="none" stroke="#6B6560" strokeWidth="1" />
        <rect x="126" y="56" width="6" height="6" fill="#6B6560" />

        {/* Bottom-left finder */}
        <rect x="60" y="108" width="22" height="22" rx="2" fill="none" stroke="#6B6560" strokeWidth="2" />
        <rect x="64" y="112" width="14" height="14" rx="1" fill="none" stroke="#6B6560" strokeWidth="1" />
        <rect x="68" y="116" width="6" height="6" fill="#6B6560" />

        {/* Data modules - scattered small squares */}
        {[
          [90, 50], [96, 50], [102, 50], [108, 50],
          [90, 56], [102, 56], [108, 56],
          [86, 62], [96, 62], [108, 62],
          [90, 68], [96, 68], [102, 68],
          [60, 78], [66, 78], [72, 78], [86, 78], [96, 78], [108, 78], [120, 78], [132, 78],
          [60, 84], [78, 84], [90, 84], [102, 84], [114, 84], [126, 84],
          [66, 90], [78, 90], [96, 90], [108, 90], [120, 90], [132, 90],
          [60, 96], [72, 96], [86, 96], [96, 96], [108, 96], [126, 96],
          [66, 102], [78, 102], [90, 102], [102, 102], [120, 102],
          [90, 108], [96, 108], [102, 108], [108, 108],
          [90, 114], [108, 114], [120, 114], [132, 114],
          [90, 120], [96, 120], [108, 120], [126, 120],
          [90, 126], [102, 126], [114, 126], [132, 126],
        ].map(([x, y], i) => (
          <rect key={i} x={x} y={y} width="4" height="4" fill="#6B6560" />
        ))}
      </motion.g>

      {/* Scan line - sweeps repeatedly */}
      <motion.rect
        x="52"
        width="96"
        height="3"
        fill="url(#scanLine)"
        filter="url(#scanGlow)"
        rx="1"
        initial={{ y: 38, opacity: 0 }}
        animate={{
          y: [38, 158, 38],
          opacity: [0, 1, 1, 1, 0],
        }}
        transition={{
          duration: 3,
          repeat: Infinity,
          ease: "easeInOut",
          repeatDelay: 0.5,
        }}
      />

      {/* Corner brackets (scan frame) */}
      <motion.g
        stroke="#3D7A6B"
        strokeWidth="2.5"
        strokeLinecap="round"
        initial={{ opacity: 0 }}
        animate={{ opacity: [0.4, 0.8, 0.4] }}
        transition={{ duration: 2, repeat: Infinity }}
      >
        {/* Top-left */}
        <path d="M56 50 L56 42 L64 42" fill="none" />
        {/* Top-right */}
        <path d="M144 42 L136 42 M144 42 L144 50" fill="none" />
        {/* Bottom-left */}
        <path d="M56 148 L56 156 L64 156" fill="none" />
        {/* Bottom-right */}
        <path d="M136 156 L144 156 L144 148" fill="none" />
      </motion.g>

      {/* Success badge that appears */}
      <motion.g
        initial={{ opacity: 0, scale: 0 }}
        animate={{ opacity: [0, 0, 1, 1, 0], scale: [0, 0, 1, 1, 0] }}
        transition={{ duration: 4, delay: 2, repeat: Infinity, repeatDelay: 1 }}
      >
        <circle cx="145" cy="155" r="16" fill="#2D6A4F" />
        <path d="M137 155 L142 160 L153 149" fill="none" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
      </motion.g>
    </svg>
  );
}
