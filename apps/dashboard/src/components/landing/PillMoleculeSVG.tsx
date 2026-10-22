"use client";

import { motion } from "framer-motion";

export default function PillMoleculeSVG({ size = 200 }: { size?: number }) {
  const orbitNodes = [
    { angle: 0, r: 70, color: "#3D7A6B", nodeSize: 6 },
    { angle: 60, r: 70, color: "#C49A6C", nodeSize: 5 },
    { angle: 120, r: 70, color: "#2D6A4F", nodeSize: 7 },
    { angle: 180, r: 70, color: "#3A3F5F", nodeSize: 5 },
    { angle: 240, r: 70, color: "#B08D3B", nodeSize: 6 },
    { angle: 300, r: 70, color: "#9B2C2C", nodeSize: 4 },
  ];

  return (
    <svg width={size} height={size} viewBox="0 0 200 200" fill="none" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <linearGradient id="pillGrad1" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#3D7A6B" />
          <stop offset="100%" stopColor="#2D6356" />
        </linearGradient>
        <linearGradient id="pillGrad2" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#C49A6C" />
          <stop offset="100%" stopColor="#A88255" />
        </linearGradient>
        <filter id="pillShadow">
          <feGaussianBlur stdDeviation="4" result="coloredBlur" />
          <feMerge>
            <feMergeNode in="coloredBlur" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
      </defs>

      {/* Orbit rings */}
      <motion.circle
        cx="100" cy="100" r="70"
        fill="none"
        stroke="#CABFAC"
        strokeWidth="0.8"
        strokeDasharray="4 4"
        initial={{ pathLength: 0 }}
        animate={{ pathLength: 1 }}
        transition={{ duration: 2 }}
      />
      <motion.circle
        cx="100" cy="100" r="50"
        fill="none"
        stroke="#CABFAC"
        strokeWidth="0.5"
        strokeDasharray="3 3"
        initial={{ pathLength: 0 }}
        animate={{ pathLength: 1 }}
        transition={{ duration: 1.5 }}
      />

      {/* Orbit connection lines */}
      {orbitNodes.map((node, i) => {
        const x = 100 + node.r * Math.cos((node.angle * Math.PI) / 180);
        const y = 100 + node.r * Math.sin((node.angle * Math.PI) / 180);
        return (
          <motion.line
            key={`line-${i}`}
            x1="100" y1="100" x2={x} y2={y}
            stroke="#CABFAC"
            strokeWidth="0.5"
            initial={{ opacity: 0 }}
            animate={{ opacity: 0.5 }}
            transition={{ delay: 1 + i * 0.15 }}
          />
        );
      })}

      {/* Orbiting nodes */}
      {orbitNodes.map((node, i) => (
        <motion.g
          key={`orbit-${i}`}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 1.5 + i * 0.1 }}
        >
          <motion.circle
            r={node.nodeSize}
            fill={node.color}
            opacity="0.8"
            animate={{
              cx: [
                100 + node.r * Math.cos(((node.angle) * Math.PI) / 180),
                100 + node.r * Math.cos(((node.angle + 360) * Math.PI) / 180),
              ],
              cy: [
                100 + node.r * Math.sin(((node.angle) * Math.PI) / 180),
                100 + node.r * Math.sin(((node.angle + 360) * Math.PI) / 180),
              ],
            }}
            transition={{
              duration: 12 + i * 2,
              repeat: Infinity,
              ease: "linear",
            }}
          />
        </motion.g>
      ))}

      {/* Central capsule - rotates slowly */}
      <motion.g
        animate={{ rotate: 360 }}
        transition={{ duration: 20, repeat: Infinity, ease: "linear" }}
        style={{ transformOrigin: "100px 100px" }}
      >
        {/* Capsule body */}
        <rect x="72" y="88" width="56" height="24" rx="12" fill="url(#pillGrad1)" filter="url(#pillShadow)" />
        {/* Capsule divider */}
        <line x1="100" y1="88" x2="100" y2="112" stroke="rgba(255,255,255,0.2)" strokeWidth="1" />
        {/* Right half overlay */}
        <path d="M100,88 L116,88 A12,12 0 0,1 116,112 L100,112 Z" fill="url(#pillGrad2)" />
        {/* Highlight */}
        <ellipse cx="90" cy="95" rx="10" ry="3" fill="rgba(255,255,255,0.2)" />
      </motion.g>

      {/* Inner orbiting electrons */}
      {[0, 120, 240].map((startAngle, i) => (
        <motion.circle
          key={`inner-${i}`}
          r="3"
          fill="#3A3F5F"
          opacity="0.6"
          animate={{
            cx: [
              100 + 50 * Math.cos((startAngle * Math.PI) / 180),
              100 + 50 * Math.cos(((startAngle + 360) * Math.PI) / 180),
            ],
            cy: [
              100 + 50 * Math.sin((startAngle * Math.PI) / 180),
              100 + 50 * Math.sin(((startAngle + 360) * Math.PI) / 180),
            ],
          }}
          transition={{
            duration: 8,
            delay: i * 0.3,
            repeat: Infinity,
            ease: "linear",
          }}
        />
      ))}
    </svg>
  );
}
