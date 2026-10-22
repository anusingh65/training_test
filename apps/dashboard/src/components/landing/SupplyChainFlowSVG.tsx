"use client";

import { motion } from "framer-motion";

const waypoints = [
  { x: 80, y: 120, label: "Manufacture", icon: "factory" },
  { x: 280, y: 80, label: "Quality Check", icon: "check" },
  { x: 480, y: 120, label: "Distribution", icon: "truck" },
  { x: 680, y: 80, label: "Pharmacy", icon: "store" },
  { x: 880, y: 120, label: "Patient", icon: "patient" },
];

const pathD = "M80,120 C180,120 180,80 280,80 C380,80 380,120 480,120 C580,120 580,80 680,80 C780,80 780,120 880,120";

function WaypointIcon({ type, x, y }: { type: string; x: number; y: number }) {
  const offset = { x: x - 12, y: y - 12 };
  switch (type) {
    case "factory":
      return (
        <g transform={`translate(${offset.x}, ${offset.y})`}>
          <rect x="2" y="10" width="20" height="14" rx="2" fill="none" stroke="currentColor" strokeWidth="1.5" />
          <rect x="7" y="14" width="5" height="5" fill="none" stroke="currentColor" strokeWidth="1" />
          <line x1="17" y1="3" x2="17" y2="10" stroke="currentColor" strokeWidth="1.5" />
          <rect x="14" y="3" width="6" height="4" fill="none" stroke="currentColor" strokeWidth="1" />
        </g>
      );
    case "check":
      return (
        <g transform={`translate(${offset.x}, ${offset.y})`}>
          <circle cx="12" cy="12" r="10" fill="none" stroke="currentColor" strokeWidth="1.5" />
          <path d="M7 12 L10 15 L17 8" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
        </g>
      );
    case "truck":
      return (
        <g transform={`translate(${offset.x}, ${offset.y})`}>
          <rect x="1" y="8" width="14" height="10" rx="1" fill="none" stroke="currentColor" strokeWidth="1.5" />
          <path d="M15,12 L20,12 L22,16 L22,18 L15,18 Z" fill="none" stroke="currentColor" strokeWidth="1.5" />
          <circle cx="7" cy="20" r="2" fill="none" stroke="currentColor" strokeWidth="1.5" />
          <circle cx="19" cy="20" r="2" fill="none" stroke="currentColor" strokeWidth="1.5" />
        </g>
      );
    case "store":
      return (
        <g transform={`translate(${offset.x}, ${offset.y})`}>
          <path d="M2 10 L12 3 L22 10" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
          <rect x="4" y="10" width="16" height="12" fill="none" stroke="currentColor" strokeWidth="1.5" />
          <rect x="9" y="14" width="6" height="8" fill="none" stroke="currentColor" strokeWidth="1" />
        </g>
      );
    case "patient":
      return (
        <g transform={`translate(${offset.x}, ${offset.y})`}>
          <circle cx="12" cy="7" r="5" fill="none" stroke="currentColor" strokeWidth="1.5" />
          <path d="M3 22 C3 15 21 15 21 22" fill="none" stroke="currentColor" strokeWidth="1.5" />
        </g>
      );
    default:
      return null;
  }
}

export default function SupplyChainFlowSVG() {
  return (
    <div className="w-full overflow-hidden">
      <svg viewBox="0 0 960 240" fill="none" xmlns="http://www.w3.org/2000/svg" className="w-full h-auto">
        <defs>
          <linearGradient id="pathGrad" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#3D7A6B" />
            <stop offset="50%" stopColor="#C49A6C" />
            <stop offset="100%" stopColor="#2D6A4F" />
          </linearGradient>
          <filter id="dotGlow">
            <feGaussianBlur stdDeviation="4" result="coloredBlur" />
            <feMerge>
              <feMergeNode in="coloredBlur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>

        {/* Background path (faded) */}
        <path d={pathD} stroke="#CABFAC" strokeWidth="2" fill="none" strokeDasharray="8 4" />

        {/* Animated path draw */}
        <motion.path
          d={pathD}
          stroke="url(#pathGrad)"
          strokeWidth="2.5"
          fill="none"
          strokeLinecap="round"
          initial={{ pathLength: 0 }}
          animate={{ pathLength: 1 }}
          transition={{ duration: 3, ease: "easeInOut" }}
        />

        {/* Traveling dot */}
        <motion.circle
          r="6"
          fill="#3D7A6B"
          filter="url(#dotGlow)"
          initial={{ offsetDistance: "0%" }}
          animate={{ offsetDistance: "100%" }}
          transition={{
            duration: 5,
            repeat: Infinity,
            ease: "easeInOut",
            repeatDelay: 1,
          }}
          style={{
            offsetPath: `path("${pathD}")`,
          }}
        />

        {/* Waypoints */}
        {waypoints.map((wp, i) => (
          <motion.g
            key={wp.label}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.5 + i * 0.3, duration: 0.6 }}
          >
            {/* Node circle */}
            <circle cx={wp.x} cy={wp.y} r="24" fill="#FFFFFF" stroke="#CABFAC" strokeWidth="1.5" />

            {/* Icon */}
            <g style={{ color: i === 4 ? "#2D6A4F" : i === 1 ? "#2D6A4F" : "#3A3F5F" }}>
              <WaypointIcon type={wp.icon} x={wp.x} y={wp.y} />
            </g>

            {/* Step number */}
            <circle cx={wp.x + 18} cy={wp.y - 18} r="8" fill="#3D7A6B" />
            <text x={wp.x + 18} y={wp.y - 14} textAnchor="middle" fill="white" fontSize="9" fontWeight="bold" fontFamily="Inter, sans-serif">
              {i + 1}
            </text>

            {/* Label */}
            <text x={wp.x} y={wp.y + 44} textAnchor="middle" fill="#6B6560" fontSize="11" fontFamily="Inter, sans-serif">
              {wp.label}
            </text>
          </motion.g>
        ))}
      </svg>
    </div>
  );
}
