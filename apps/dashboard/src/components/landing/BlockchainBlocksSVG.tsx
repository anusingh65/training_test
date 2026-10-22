"use client";

import { motion } from "framer-motion";

const blocks = [
  { x: 20, hash: "0x7a3f...e1b2" },
  { x: 170, hash: "0x9c2d...f4a8" },
  { x: 320, hash: "0xb1e5...c9d3" },
  { x: 470, hash: "0xd8f2...a6e7" },
];

export default function BlockchainBlocksSVG({ size = 200 }: { size?: number }) {
  return (
    <svg width={size * 3.2} height={size * 0.65} viewBox="0 0 640 130" fill="none" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <linearGradient id="blockGrad" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#3D7A6B" stopOpacity="0.1" />
          <stop offset="100%" stopColor="#C49A6C" stopOpacity="0.1" />
        </linearGradient>
        <linearGradient id="chainGrad" x1="0%" y1="0%" x2="100%" y2="0%">
          <stop offset="0%" stopColor="#3D7A6B" />
          <stop offset="100%" stopColor="#C49A6C" />
        </linearGradient>
      </defs>

      {blocks.map((block, i) => (
        <motion.g
          key={i}
          initial={{ opacity: 0, x: block.x - 20 }}
          animate={{ opacity: 1, x: block.x }}
          transition={{ delay: i * 0.4, duration: 0.6, type: "spring" }}
        >
          {/* Block */}
          <rect x={block.x} y="15" width="130" height="80" rx="8" fill="url(#blockGrad)" stroke="#CABFAC" strokeWidth="1.5" />

          {/* Block header */}
          <rect x={block.x} y="15" width="130" height="24" rx="8" fill="#3A3F5F" />
          <rect x={block.x} y="31" width="130" height="8" fill="#3A3F5F" />
          <text x={block.x + 10} y="32" fill="#CABFAC" fontSize="10" fontWeight="600" fontFamily="monospace">
            Block #{(1247 + i).toString()}
          </text>

          {/* Hash */}
          <text x={block.x + 10} y="58" fill="#6B6560" fontSize="8" fontFamily="Inter, sans-serif">
            Hash
          </text>
          <text x={block.x + 10} y="70" fill="#C49A6C" fontSize="9" fontFamily="monospace">
            {block.hash}
          </text>

          {/* Nonce */}
          <text x={block.x + 10} y="86" fill="#6B6560" fontSize="8" fontFamily="Inter, sans-serif">
            Nonce: {(82741 + i * 1337).toString()}
          </text>

          {/* Chain link to next block */}
          {i < blocks.length - 1 && (
            <motion.g
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: (i + 1) * 0.4 + 0.2 }}
            >
              <line
                x1={block.x + 130}
                y1="55"
                x2={block.x + 150}
                y2="55"
                stroke="#CABFAC"
                strokeWidth="2"
              />
              {/* Arrow */}
              <path
                d={`M${block.x + 146} 50 L${block.x + 153} 55 L${block.x + 146} 60`}
                fill="none"
                stroke="#3D7A6B"
                strokeWidth="1.5"
                strokeLinecap="round"
              />
              {/* Pulse along chain link */}
              <motion.circle
                r="3"
                fill="#3D7A6B"
                animate={{
                  cx: [block.x + 130, block.x + 153],
                  opacity: [0, 1, 0],
                }}
                transition={{
                  duration: 1.2,
                  delay: 3 + i * 1.5,
                  repeat: Infinity,
                  repeatDelay: 4,
                  ease: "easeInOut",
                }}
                cy="55"
              />
            </motion.g>
          )}
        </motion.g>
      ))}

      {/* "New block" indicator on the right */}
      <motion.g
        initial={{ opacity: 0 }}
        animate={{ opacity: [0, 0.5, 0] }}
        transition={{ duration: 3, delay: 4, repeat: Infinity, repeatDelay: 2 }}
      >
        <rect x="620" y="25" width="10" height="60" rx="3" fill="none" stroke="#3D7A6B" strokeWidth="1" strokeDasharray="3 2" />
        <text x="625" y="60" fill="#3D7A6B" fontSize="14" textAnchor="middle" fontWeight="bold">+</text>
      </motion.g>
    </svg>
  );
}
