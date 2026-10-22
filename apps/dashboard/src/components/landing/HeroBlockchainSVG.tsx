"use client";

import { motion } from "framer-motion";

const nodes = [
  { x: 400, y: 100, label: "Manufacturer", delay: 0 },
  { x: 200, y: 200, label: "QC Lab", delay: 0.2 },
  { x: 600, y: 200, label: "Distributor", delay: 0.4 },
  { x: 100, y: 350, label: "Warehouse", delay: 0.6 },
  { x: 400, y: 320, label: "Blockchain", delay: 0.1, isCenter: true },
  { x: 700, y: 350, label: "Pharmacy", delay: 0.8 },
  { x: 250, y: 480, label: "Inspector", delay: 1.0 },
  { x: 550, y: 480, label: "Patient", delay: 1.2 },
];

const edges = [
  [0, 1], [0, 2], [0, 4],
  [1, 3], [1, 4],
  [2, 4], [2, 5],
  [3, 6], [3, 4],
  [4, 5], [4, 6], [4, 7],
  [5, 7],
  [6, 7],
];

export default function HeroBlockchainSVG() {
  return (
    <div className="relative w-full max-w-[800px] mx-auto">
      <svg viewBox="0 0 800 580" fill="none" xmlns="http://www.w3.org/2000/svg" className="w-full h-auto">
        <defs>
          <radialGradient id="centerGlow" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor="#3D7A6B" stopOpacity="0.2" />
            <stop offset="100%" stopColor="#3D7A6B" stopOpacity="0" />
          </radialGradient>
          <linearGradient id="edgeGrad" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#3D7A6B" stopOpacity="0.6" />
            <stop offset="100%" stopColor="#C49A6C" stopOpacity="0.6" />
          </linearGradient>
          <filter id="glow">
            <feGaussianBlur stdDeviation="4" result="coloredBlur" />
            <feMerge>
              <feMergeNode in="coloredBlur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
          <filter id="softGlow">
            <feGaussianBlur stdDeviation="8" result="coloredBlur" />
            <feMerge>
              <feMergeNode in="coloredBlur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>

        {/* Background glow at center */}
        <motion.circle
          cx="400" cy="320" r="180"
          fill="url(#centerGlow)"
          initial={{ opacity: 0, scale: 0.5 }}
          animate={{ opacity: [0.3, 0.6, 0.3], scale: [0.8, 1.1, 0.8] }}
          transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
        />

        {/* Edges */}
        {edges.map(([from, to], i) => {
          const n1 = nodes[from];
          const n2 = nodes[to];
          return (
            <g key={`edge-${i}`}>
              <motion.line
                x1={n1.x} y1={n1.y} x2={n2.x} y2={n2.y}
                stroke="#CABFAC"
                strokeWidth="1.5"
                initial={{ pathLength: 0, opacity: 0 }}
                animate={{ pathLength: 1, opacity: 1 }}
                transition={{ duration: 1.2, delay: 0.3 + i * 0.08 }}
              />
              {/* Traveling pulse */}
              <motion.circle
                r="3"
                fill="#3D7A6B"
                filter="url(#glow)"
                initial={{ opacity: 0 }}
                animate={{
                  cx: [n1.x, n2.x],
                  cy: [n1.y, n2.y],
                  opacity: [0, 1, 1, 0],
                }}
                transition={{
                  duration: 2 + Math.random() * 2,
                  delay: 2 + i * 0.3,
                  repeat: Infinity,
                  repeatDelay: 3 + Math.random() * 4,
                  ease: "easeInOut",
                }}
              />
            </g>
          );
        })}

        {/* Nodes */}
        {nodes.map((node, i) => (
          <g key={`node-${i}`}>
            {/* Node outer ring */}
            <motion.circle
              cx={node.x} cy={node.y}
              r={node.isCenter ? 40 : 28}
              fill="#FFFFFF"
              stroke={node.isCenter ? "#3D7A6B" : "#CABFAC"}
              strokeWidth={node.isCenter ? 2 : 1.5}
              initial={{ scale: 0, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              transition={{ duration: 0.6, delay: node.delay + 0.5, type: "spring" }}
            />

            {/* Center node special glow */}
            {node.isCenter && (
              <motion.circle
                cx={node.x} cy={node.y} r="44"
                fill="none"
                stroke="#3D7A6B"
                strokeWidth="1"
                initial={{ opacity: 0 }}
                animate={{ opacity: [0, 0.5, 0], scale: [1, 1.3, 1] }}
                transition={{ duration: 3, repeat: Infinity, ease: "easeInOut" }}
              />
            )}

            {/* Icon inside node */}
            <motion.g
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: node.delay + 0.8 }}
            >
              {node.isCenter ? (
                /* Blockchain icon - chain links */
                <g transform={`translate(${node.x - 14}, ${node.y - 14})`}>
                  <rect x="2" y="6" width="10" height="16" rx="3" fill="none" stroke="#3D7A6B" strokeWidth="1.8" />
                  <rect x="16" y="6" width="10" height="16" rx="3" fill="none" stroke="#C49A6C" strokeWidth="1.8" />
                  <line x1="12" y1="14" x2="16" y2="14" stroke="#3D7A6B" strokeWidth="1.8" />
                </g>
              ) : i === 0 ? (
                /* Factory icon */
                <g transform={`translate(${node.x - 10}, ${node.y - 10})`}>
                  <rect x="2" y="8" width="16" height="12" rx="1" fill="none" stroke="#2D6A4F" strokeWidth="1.5" />
                  <rect x="6" y="12" width="4" height="4" fill="none" stroke="#2D6A4F" strokeWidth="1" />
                  <line x1="14" y1="2" x2="14" y2="8" stroke="#2D6A4F" strokeWidth="1.5" />
                  <rect x="12" y="2" width="4" height="3" fill="none" stroke="#2D6A4F" strokeWidth="1" />
                </g>
              ) : i === 7 ? (
                /* Person/patient icon */
                <g transform={`translate(${node.x - 10}, ${node.y - 10})`}>
                  <circle cx="10" cy="6" r="4" fill="none" stroke="#C49A6C" strokeWidth="1.5" />
                  <path d="M2 20 C2 14 18 14 18 20" fill="none" stroke="#C49A6C" strokeWidth="1.5" />
                </g>
              ) : (
                /* Generic pill icon */
                <g transform={`translate(${node.x - 8}, ${node.y - 8})`}>
                  <rect x="2" y="2" width="12" height="12" rx="6" fill="none" stroke="#3A3F5F" strokeWidth="1.5" />
                  <line x1="8" y1="4" x2="8" y2="12" stroke="#3A3F5F" strokeWidth="1" />
                </g>
              )}
            </motion.g>

            {/* Label */}
            <motion.text
              x={node.x}
              y={node.y + (node.isCenter ? 56 : 44)}
              textAnchor="middle"
              fill="#6B6560"
              fontSize="11"
              fontFamily="Inter, sans-serif"
              initial={{ opacity: 0, y: 5 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: node.delay + 1 }}
            >
              {node.label}
            </motion.text>
          </g>
        ))}

        {/* Floating data particles */}
        {Array.from({ length: 12 }).map((_, i) => (
          <motion.circle
            key={`particle-${i}`}
            r={1 + Math.random() * 1.5}
            fill="#3D7A6B"
            opacity="0.4"
            initial={{
              cx: 100 + Math.random() * 600,
              cy: 50 + Math.random() * 480,
              opacity: 0,
            }}
            animate={{
              cy: [50 + Math.random() * 480, 50 + Math.random() * 480],
              cx: [100 + Math.random() * 600, 100 + Math.random() * 600],
              opacity: [0, 0.4, 0],
            }}
            transition={{
              duration: 6 + Math.random() * 6,
              delay: i * 0.5,
              repeat: Infinity,
              ease: "easeInOut",
            }}
          />
        ))}
      </svg>
    </div>
  );
}
