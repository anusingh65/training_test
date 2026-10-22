"use client";

import { motion } from "framer-motion";

export default function WaveBackgroundSVG({ className = "" }: { className?: string }) {
  return (
    <div className={`absolute inset-0 overflow-hidden pointer-events-none ${className}`}>
      <svg
        viewBox="0 0 1440 400"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        className="absolute bottom-0 w-full"
        preserveAspectRatio="none"
      >
        <defs>
          <linearGradient id="wave1Grad" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#3D7A6B" stopOpacity="0.06" />
            <stop offset="50%" stopColor="#C49A6C" stopOpacity="0.06" />
            <stop offset="100%" stopColor="#3D7A6B" stopOpacity="0.06" />
          </linearGradient>
          <linearGradient id="wave2Grad" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#C49A6C" stopOpacity="0.04" />
            <stop offset="50%" stopColor="#3D7A6B" stopOpacity="0.04" />
            <stop offset="100%" stopColor="#C49A6C" stopOpacity="0.04" />
          </linearGradient>
        </defs>

        {/* Wave 1 */}
        <motion.path
          d="M0,200 C120,160 240,280 360,240 C480,200 600,120 720,160 C840,200 960,280 1080,240 C1200,200 1320,120 1440,160 L1440,400 L0,400 Z"
          fill="url(#wave1Grad)"
          animate={{
            d: [
              "M0,200 C120,160 240,280 360,240 C480,200 600,120 720,160 C840,200 960,280 1080,240 C1200,200 1320,120 1440,160 L1440,400 L0,400 Z",
              "M0,240 C120,200 240,120 360,160 C480,200 600,280 720,240 C840,200 960,120 1080,160 C1200,200 1320,280 1440,240 L1440,400 L0,400 Z",
              "M0,200 C120,160 240,280 360,240 C480,200 600,120 720,160 C840,200 960,280 1080,240 C1200,200 1320,120 1440,160 L1440,400 L0,400 Z",
            ],
          }}
          transition={{ duration: 10, repeat: Infinity, ease: "easeInOut" }}
        />

        {/* Wave 2 */}
        <motion.path
          d="M0,280 C160,240 320,320 480,280 C640,240 800,200 960,240 C1120,280 1280,320 1440,280 L1440,400 L0,400 Z"
          fill="url(#wave2Grad)"
          animate={{
            d: [
              "M0,280 C160,240 320,320 480,280 C640,240 800,200 960,240 C1120,280 1280,320 1440,280 L1440,400 L0,400 Z",
              "M0,260 C160,300 320,220 480,260 C640,300 800,240 960,280 C1120,220 1280,300 1440,260 L1440,400 L0,400 Z",
              "M0,280 C160,240 320,320 480,280 C640,240 800,200 960,240 C1120,280 1280,320 1440,280 L1440,400 L0,400 Z",
            ],
          }}
          transition={{ duration: 8, repeat: Infinity, ease: "easeInOut", delay: 1 }}
        />

        {/* Wave 3 - subtle */}
        <motion.path
          d="M0,320 C200,300 400,340 600,320 C800,300 1000,340 1200,320 C1300,310 1400,330 1440,320 L1440,400 L0,400 Z"
          fill="#CABFAC"
          fillOpacity="0.2"
          animate={{
            d: [
              "M0,320 C200,300 400,340 600,320 C800,300 1000,340 1200,320 C1300,310 1400,330 1440,320 L1440,400 L0,400 Z",
              "M0,330 C200,340 400,300 600,330 C800,340 1000,300 1200,330 C1300,340 1400,310 1440,330 L1440,400 L0,400 Z",
              "M0,320 C200,300 400,340 600,320 C800,300 1000,340 1200,320 C1300,310 1400,330 1440,320 L1440,400 L0,400 Z",
            ],
          }}
          transition={{ duration: 12, repeat: Infinity, ease: "easeInOut", delay: 0.5 }}
        />
      </svg>
    </div>
  );
}
