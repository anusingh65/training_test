"use client";

import { motion } from "framer-motion";

export default function DNAHelixSVG({ size = 200 }: { size?: number }) {
  const steps = 16;
  const helixHeight = 180;
  const centerX = 100;
  const amplitude = 35;

  const points = Array.from({ length: steps }, (_, i) => {
    const t = i / (steps - 1);
    const y = 10 + t * helixHeight;
    const phase = t * Math.PI * 3;
    const x1 = centerX + amplitude * Math.sin(phase);
    const x2 = centerX - amplitude * Math.sin(phase);
    return { y, x1, x2, t };
  });

  return (
    <svg width={size} height={size} viewBox="0 0 200 200" fill="none" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <linearGradient id="strand1" x1="0%" y1="0%" x2="0%" y2="100%">
          <stop offset="0%" stopColor="#3D7A6B" />
          <stop offset="100%" stopColor="#C49A6C" />
        </linearGradient>
        <linearGradient id="strand2" x1="0%" y1="0%" x2="0%" y2="100%">
          <stop offset="0%" stopColor="#C49A6C" />
          <stop offset="100%" stopColor="#3D7A6B" />
        </linearGradient>
      </defs>

      {/* Connecting rungs */}
      {points.map((p, i) => (
        <motion.line
          key={`rung-${i}`}
          x1={p.x1} y1={p.y}
          x2={p.x2} y2={p.y}
          stroke="#CABFAC"
          strokeWidth="1"
          initial={{ pathLength: 0, opacity: 0 }}
          animate={{ pathLength: 1, opacity: 0.6 }}
          transition={{ delay: 0.5 + i * 0.1, duration: 0.3 }}
        />
      ))}

      {/* Strand 1 */}
      <motion.path
        d={`M${points.map((p) => `${p.x1},${p.y}`).join(" L")}`}
        fill="none"
        stroke="url(#strand1)"
        strokeWidth="2.5"
        strokeLinecap="round"
        initial={{ pathLength: 0 }}
        animate={{ pathLength: 1 }}
        transition={{ duration: 2, ease: "easeInOut" }}
      />

      {/* Strand 2 */}
      <motion.path
        d={`M${points.map((p) => `${p.x2},${p.y}`).join(" L")}`}
        fill="none"
        stroke="url(#strand2)"
        strokeWidth="2.5"
        strokeLinecap="round"
        initial={{ pathLength: 0 }}
        animate={{ pathLength: 1 }}
        transition={{ duration: 2, ease: "easeInOut", delay: 0.3 }}
      />

      {/* Nodes on strands */}
      {points.map((p, i) => (
        <motion.g key={`nodes-${i}`}>
          <motion.circle
            cx={p.x1} cy={p.y} r="3"
            fill="#3D7A6B"
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ delay: 0.8 + i * 0.1, type: "spring" }}
          />
          <motion.circle
            cx={p.x2} cy={p.y} r="3"
            fill="#C49A6C"
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ delay: 1 + i * 0.1, type: "spring" }}
          />
        </motion.g>
      ))}

      {/* Scanning highlight that moves up and down */}
      <motion.rect
        x="55" width="90" height="6" rx="3"
        fill="#3D7A6B"
        opacity="0.1"
        animate={{ y: [10, 185, 10] }}
        transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
      />
    </svg>
  );
}
