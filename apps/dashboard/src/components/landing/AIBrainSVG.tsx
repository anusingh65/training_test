"use client";

import { motion } from "framer-motion";

const brainNodes = [
  { x: 100, y: 40 },
  { x: 60, y: 65 },
  { x: 140, y: 65 },
  { x: 35, y: 100 },
  { x: 80, y: 95 },
  { x: 120, y: 95 },
  { x: 165, y: 100 },
  { x: 50, y: 130 },
  { x: 100, y: 125 },
  { x: 150, y: 130 },
  { x: 70, y: 160 },
  { x: 130, y: 160 },
];

const brainEdges = [
  [0, 1], [0, 2], [0, 4], [0, 5],
  [1, 3], [1, 4], [1, 7],
  [2, 5], [2, 6], [2, 9],
  [3, 4], [3, 7],
  [4, 5], [4, 7], [4, 8],
  [5, 6], [5, 8], [5, 9],
  [6, 9],
  [7, 8], [7, 10],
  [8, 10], [8, 11],
  [9, 11],
  [10, 11],
];

export default function AIBrainSVG({ size = 200 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 200 200" fill="none" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <radialGradient id="brainGlow" cx="50%" cy="50%" r="50%">
          <stop offset="0%" stopColor="#C49A6C" stopOpacity="0.15" />
          <stop offset="100%" stopColor="#C49A6C" stopOpacity="0" />
        </radialGradient>
        <filter id="nodeGlow">
          <feGaussianBlur stdDeviation="3" result="coloredBlur" />
          <feMerge>
            <feMergeNode in="coloredBlur" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
      </defs>

      {/* Background glow */}
      <circle cx="100" cy="100" r="90" fill="url(#brainGlow)" />

      {/* Brain outline */}
      <motion.path
        d="M100 25 C60 25 30 55 30 90 C30 110 40 125 55 135 C55 155 70 175 100 175 C130 175 145 155 145 135 C160 125 170 110 170 90 C170 55 140 25 100 25Z"
        fill="none"
        stroke="#CABFAC"
        strokeWidth="1.5"
        initial={{ pathLength: 0 }}
        animate={{ pathLength: 1 }}
        transition={{ duration: 2, ease: "easeInOut" }}
      />

      {/* Neural network edges */}
      {brainEdges.map(([from, to], i) => {
        const n1 = brainNodes[from];
        const n2 = brainNodes[to];
        return (
          <g key={`edge-${i}`}>
            <line x1={n1.x} y1={n1.y} x2={n2.x} y2={n2.y} stroke="#CABFAC" strokeWidth="0.8" />
            {/* Signal pulse along edge */}
            <motion.circle
              r="2"
              fill="#C49A6C"
              filter="url(#nodeGlow)"
              initial={{ opacity: 0 }}
              animate={{
                cx: [n1.x, n2.x],
                cy: [n1.y, n2.y],
                opacity: [0, 0.8, 0],
              }}
              transition={{
                duration: 1.5,
                delay: 2 + i * 0.15,
                repeat: Infinity,
                repeatDelay: 4 + Math.random() * 3,
                ease: "easeInOut",
              }}
            />
          </g>
        );
      })}

      {/* Neural network nodes */}
      {brainNodes.map((node, i) => (
        <motion.g key={`node-${i}`}>
          <motion.circle
            cx={node.x} cy={node.y} r="5"
            fill="#FFFFFF"
            stroke="#C49A6C"
            strokeWidth="1.5"
            initial={{ scale: 0, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ delay: 0.5 + i * 0.1, type: "spring" }}
          />
          {/* Node activation pulse */}
          <motion.circle
            cx={node.x} cy={node.y} r="5"
            fill="#C49A6C"
            initial={{ opacity: 0 }}
            animate={{ opacity: [0, 0.6, 0] }}
            transition={{
              duration: 1,
              delay: 3 + i * 0.3,
              repeat: Infinity,
              repeatDelay: 5 + Math.random() * 3,
            }}
          />
        </motion.g>
      ))}

      {/* Risk gauge at bottom */}
      <motion.g
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 2.5 }}
      >
        <text x="100" y="198" textAnchor="middle" fill="#6B6560" fontSize="9" fontFamily="Inter, sans-serif">
          Risk Analysis Engine
        </text>
      </motion.g>
    </svg>
  );
}
