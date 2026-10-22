"use client";

import { motion } from "framer-motion";

export default function ShieldVerificationSVG({ size = 200 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 200 200" fill="none" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <linearGradient id="shieldGrad" x1="50%" y1="0%" x2="50%" y2="100%">
          <stop offset="0%" stopColor="#3D7A6B" />
          <stop offset="100%" stopColor="#C49A6C" />
        </linearGradient>
        <filter id="shieldGlow">
          <feGaussianBlur stdDeviation="6" result="coloredBlur" />
          <feMerge>
            <feMergeNode in="coloredBlur" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
      </defs>

      {/* Outer ring pulse */}
      <motion.circle
        cx="100" cy="100" r="90"
        fill="none"
        stroke="#3D7A6B"
        strokeWidth="0.5"
        initial={{ opacity: 0, scale: 0.8 }}
        animate={{ opacity: [0, 0.3, 0], scale: [0.8, 1.1, 0.8] }}
        transition={{ duration: 3, repeat: Infinity, ease: "easeInOut" }}
      />

      {/* Shield path - draws itself */}
      <motion.path
        d="M100 25 L155 55 L155 105 C155 145 100 175 100 175 C100 175 45 145 45 105 L45 55 Z"
        fill="none"
        stroke="url(#shieldGrad)"
        strokeWidth="3"
        strokeLinecap="round"
        strokeLinejoin="round"
        filter="url(#shieldGlow)"
        initial={{ pathLength: 0, opacity: 0 }}
        animate={{ pathLength: 1, opacity: 1 }}
        transition={{ duration: 2, ease: "easeInOut" }}
      />

      {/* Shield fill */}
      <motion.path
        d="M100 25 L155 55 L155 105 C155 145 100 175 100 175 C100 175 45 145 45 105 L45 55 Z"
        fill="#3D7A6B"
        opacity="0.08"
        initial={{ opacity: 0 }}
        animate={{ opacity: 0.08 }}
        transition={{ duration: 1, delay: 1.5 }}
      />

      {/* Checkmark - draws after shield */}
      <motion.path
        d="M75 102 L92 119 L128 83"
        fill="none"
        stroke="#2D6A4F"
        strokeWidth="4"
        strokeLinecap="round"
        strokeLinejoin="round"
        filter="url(#shieldGlow)"
        initial={{ pathLength: 0, opacity: 0 }}
        animate={{ pathLength: 1, opacity: 1 }}
        transition={{ duration: 0.8, delay: 2.2, ease: "easeOut" }}
      />

      {/* Orbiting dots */}
      {[0, 1, 2].map((i) => (
        <motion.circle
          key={i}
          r="3"
          fill="#C49A6C"
          initial={{ opacity: 0.5 }}
          animate={{
            cx: [
              100 + 85 * Math.cos((i * 2 * Math.PI) / 3),
              100 + 85 * Math.cos((i * 2 * Math.PI) / 3 + Math.PI),
              100 + 85 * Math.cos((i * 2 * Math.PI) / 3 + 2 * Math.PI),
            ],
            cy: [
              100 + 85 * Math.sin((i * 2 * Math.PI) / 3),
              100 + 85 * Math.sin((i * 2 * Math.PI) / 3 + Math.PI),
              100 + 85 * Math.sin((i * 2 * Math.PI) / 3 + 2 * Math.PI),
            ],
            opacity: [0.3, 0.7, 0.3],
          }}
          transition={{
            duration: 8,
            delay: i * 0.5,
            repeat: Infinity,
            ease: "linear",
          }}
        />
      ))}
    </svg>
  );
}
