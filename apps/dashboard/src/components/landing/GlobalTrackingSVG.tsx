"use client";

import { motion } from "framer-motion";

const cities = [
  { x: 100, y: 75, name: "Mumbai", risk: "high" },
  { x: 130, y: 60, name: "Delhi", risk: "low" },
  { x: 115, y: 90, name: "Hyderabad", risk: "medium" },
  { x: 140, y: 85, name: "Chennai", risk: "low" },
  { x: 90, y: 95, name: "Bangalore", risk: "medium" },
  { x: 125, y: 50, name: "Lucknow", risk: "high" },
  { x: 145, y: 70, name: "Kolkata", risk: "low" },
  { x: 80, y: 80, name: "Pune", risk: "low" },
];

const riskColors: Record<string, string> = {
  high: "#9B2C2C",
  medium: "#B08D3B",
  low: "#2D6A4F",
};

const connectionArcs = [
  [0, 1], [0, 2], [0, 4], [1, 5], [1, 6], [2, 3], [2, 4], [3, 6], [5, 6], [4, 7], [0, 7],
];

export default function GlobalTrackingSVG({ size = 200 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 200 200" fill="none" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <radialGradient id="mapGlow" cx="50%" cy="50%" r="50%">
          <stop offset="0%" stopColor="#C49A6C" stopOpacity="0.1" />
          <stop offset="100%" stopColor="#C49A6C" stopOpacity="0" />
        </radialGradient>
        <filter id="cityGlow">
          <feGaussianBlur stdDeviation="2" result="coloredBlur" />
          <feMerge>
            <feMergeNode in="coloredBlur" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
      </defs>

      {/* Background */}
      <circle cx="100" cy="100" r="90" fill="url(#mapGlow)" />
      <motion.circle
        cx="100" cy="100" r="85"
        fill="none"
        stroke="#CABFAC"
        strokeWidth="1"
        strokeDasharray="4 3"
        initial={{ pathLength: 0 }}
        animate={{ pathLength: 1 }}
        transition={{ duration: 2 }}
      />

      {/* Simplified India outline */}
      <motion.path
        d="M108,30 C120,32 130,38 135,45 C138,50 142,55 145,62 C148,68 150,75 148,82 C146,88 142,92 140,98 C138,104 137,108 132,115 C128,120 125,125 120,130 C118,132 116,140 112,148 C110,152 108,158 105,162 C102,165 98,160 95,155 C92,150 88,140 85,132 C82,126 78,120 75,115 C72,108 68,100 65,92 C62,84 62,76 65,68 C68,60 72,52 78,46 C84,40 90,35 98,32 C102,30 105,29 108,30Z"
        fill="none"
        stroke="#3D7A6B"
        strokeWidth="1"
        strokeOpacity="0.3"
        initial={{ pathLength: 0 }}
        animate={{ pathLength: 1 }}
        transition={{ duration: 2.5, ease: "easeInOut" }}
      />

      {/* Connection arcs */}
      {connectionArcs.map(([from, to], i) => {
        const c1 = cities[from];
        const c2 = cities[to];
        const mx = (c1.x + c2.x) / 2;
        const my = (c1.y + c2.y) / 2 - 8;
        return (
          <motion.path
            key={`arc-${i}`}
            d={`M${c1.x},${c1.y} Q${mx},${my} ${c2.x},${c2.y}`}
            fill="none"
            stroke="#CABFAC"
            strokeWidth="0.8"
            initial={{ pathLength: 0 }}
            animate={{ pathLength: 1 }}
            transition={{ duration: 1, delay: 1 + i * 0.1 }}
          />
        );
      })}

      {/* Cities */}
      {cities.map((city, i) => (
        <motion.g key={city.name}>
          {/* Pulse ring */}
          <motion.circle
            cx={city.x} cy={city.y}
            r="8"
            fill="none"
            stroke={riskColors[city.risk]}
            strokeWidth="0.5"
            initial={{ opacity: 0, scale: 0.5 }}
            animate={{ opacity: [0, 0.4, 0], scale: [0.5, 1.5, 0.5] }}
            transition={{ duration: 3, delay: 2 + i * 0.4, repeat: Infinity }}
          />
          {/* City dot */}
          <motion.circle
            cx={city.x} cy={city.y} r="3"
            fill={riskColors[city.risk]}
            filter="url(#cityGlow)"
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ delay: 1 + i * 0.15, type: "spring" }}
          />
        </motion.g>
      ))}

      {/* Legend */}
      <motion.g
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 3 }}
      >
        <circle cx="55" cy="180" r="3" fill="#2D6A4F" />
        <text x="62" y="183" fill="#6B6560" fontSize="8" fontFamily="Inter, sans-serif">Low</text>
        <circle cx="90" cy="180" r="3" fill="#B08D3B" />
        <text x="97" y="183" fill="#6B6560" fontSize="8" fontFamily="Inter, sans-serif">Medium</text>
        <circle cx="135" cy="180" r="3" fill="#9B2C2C" />
        <text x="142" y="183" fill="#6B6560" fontSize="8" fontFamily="Inter, sans-serif">High</text>
      </motion.g>
    </svg>
  );
}
