"use client";

import { motion } from "framer-motion";

const pills = [
  { x: 80, y: 100, size: 30, rotation: 30, delay: 0 },
  { x: 250, y: 60, size: 22, rotation: -20, delay: 1 },
  { x: 420, y: 130, size: 26, rotation: 45, delay: 0.5 },
  { x: 600, y: 50, size: 20, rotation: -35, delay: 1.5 },
  { x: 700, y: 120, size: 28, rotation: 15, delay: 0.8 },
  { x: 150, y: 180, size: 18, rotation: 60, delay: 2 },
  { x: 350, y: 200, size: 24, rotation: -50, delay: 1.2 },
  { x: 520, y: 180, size: 16, rotation: 25, delay: 0.3 },
  { x: 50, y: 220, size: 14, rotation: -15, delay: 1.8 },
  { x: 750, y: 210, size: 20, rotation: 40, delay: 0.6 },
];

function PillShape({ size, color1, color2 }: { size: number; color1: string; color2: string }) {
  const w = size;
  const h = size * 0.42;
  const r = h / 2;
  return (
    <g>
      {/* Left half */}
      <path
        d={`M${w / 2},0 L${r},0 A${r},${r} 0 0,0 ${r},${h} L${w / 2},${h} Z`}
        fill={color1}
        opacity="0.7"
      />
      {/* Right half */}
      <path
        d={`M${w / 2},0 L${w - r},0 A${r},${r} 0 0,1 ${w - r},${h} L${w / 2},${h} Z`}
        fill={color2}
        opacity="0.7"
      />
      {/* Dividing line */}
      <line x1={w / 2} y1="0" x2={w / 2} y2={h} stroke="rgba(255,255,255,0.15)" strokeWidth="0.5" />
      {/* Highlight */}
      <ellipse cx={w * 0.3} cy={h * 0.3} rx={w * 0.12} ry={h * 0.15} fill="rgba(255,255,255,0.15)" />
    </g>
  );
}

const colorPairs = [
  ["#3D7A6B", "#2D6356"],
  ["#C49A6C", "#A88255"],
  ["#2D6A4F", "#1F5740"],
  ["#3D7A6B", "#C49A6C"],
  ["#3A3F5F", "#2D3250"],
];

export default function FloatingPillsSVG() {
  return (
    <div className="absolute inset-0 overflow-hidden pointer-events-none">
      <svg
        viewBox="0 0 800 280"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        className="w-full h-full"
        preserveAspectRatio="xMidYMid slice"
      >
        {pills.map((pill, i) => {
          const [c1, c2] = colorPairs[i % colorPairs.length];
          return (
            <motion.g
              key={i}
              initial={{
                x: pill.x,
                y: pill.y,
                rotate: pill.rotation,
                opacity: 0,
              }}
              animate={{
                y: [pill.y, pill.y - 20, pill.y],
                rotate: [pill.rotation, pill.rotation + 10, pill.rotation],
                opacity: [0.1, 0.2, 0.1],
              }}
              transition={{
                duration: 6 + i * 0.5,
                delay: pill.delay,
                repeat: Infinity,
                ease: "easeInOut",
              }}
            >
              <PillShape size={pill.size} color1={c1} color2={c2} />
            </motion.g>
          );
        })}
      </svg>
    </div>
  );
}
