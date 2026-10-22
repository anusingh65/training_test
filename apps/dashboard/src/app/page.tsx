import Link from "next/link";
import MobileNav from "@/components/landing/MobileNav";

const navLinks = [
  { href: "#features", label: "Features" },
  { href: "#how-it-works", label: "How It Works" },
  { href: "#technology", label: "Technology" },
  { href: "#impact", label: "Impact" },
];

/* ─── SVG Animation Components ─── */

function SupplyChainSVG() {
  return (
    <svg viewBox="0 0 400 400" className="split-svg" aria-hidden="true">
      <defs>
        <radialGradient id="sc-glow" cx="50%" cy="50%" r="45%">
          <stop offset="0%" stopColor="rgba(61,122,107,0.08)" />
          <stop offset="100%" stopColor="transparent" />
        </radialGradient>
      </defs>
      <circle cx="200" cy="200" r="180" fill="url(#sc-glow)" />

      {/* Concentric rings */}
      {[60, 100, 140].map((r, i) => (
        <circle
          key={r}
          cx="200"
          cy="200"
          r={r}
          fill="none"
          stroke="rgba(202,191,172,0.12)"
          strokeWidth="1"
          className={`warning-ring wr-${i}`}
        />
      ))}

      {/* Supply chain path — flowing from top-left to bottom-right */}
      <path
        d="M80,120 C120,120 140,180 200,180 C260,180 280,240 320,240"
        fill="none"
        stroke="rgba(202,191,172,0.3)"
        strokeWidth="2"
        strokeDasharray="8,4"
      />

      {/* Broken section — red */}
      <path
        d="M180,175 C195,178 205,178 220,182"
        fill="none"
        stroke="#C25B4B"
        strokeWidth="3"
        strokeLinecap="round"
        strokeDasharray="4,6"
        className="chain-break"
      />

      {/* Supply nodes */}
      {[
        { cx: 80, cy: 120, label: "MFG", delay: 0 },
        { cx: 150, cy: 155, label: "WHS", delay: 1 },
        { cx: 250, cy: 205, label: "DST", delay: 2 },
        { cx: 320, cy: 240, label: "RX", delay: 3 },
      ].map((node, i) => (
        <g key={i} className={`chain-node cn-${i}`}>
          <circle cx={node.cx} cy={node.cy} r="20" fill="rgba(61,122,107,0.08)" stroke="rgba(61,122,107,0.25)" strokeWidth="1.5" />
          <circle cx={node.cx} cy={node.cy} r="8" fill="#3D7A6B" opacity="0.6" />
          <text x={node.cx} y={node.cy + 34} textAnchor="middle" fill="#8A847D" fontSize="8" fontWeight="600" fontFamily="sans-serif" letterSpacing="0.08em">
            {node.label}
          </text>
        </g>
      ))}

      {/* Counterfeit warning — X mark */}
      <g className="chain-break" transform="translate(200,130)">
        <circle cx="0" cy="0" r="16" fill="rgba(194,91,75,0.1)" stroke="rgba(194,91,75,0.3)" strokeWidth="1.5" />
        <line x1="-6" y1="-6" x2="6" y2="6" stroke="#C25B4B" strokeWidth="2.5" strokeLinecap="round" />
        <line x1="6" y1="-6" x2="-6" y2="6" stroke="#C25B4B" strokeWidth="2.5" strokeLinecap="round" />
      </g>

      {/* Flow particles */}
      {[0, 1, 2].map((i) => (
        <circle
          key={i}
          cx="80"
          cy="120"
          r="3"
          fill="#3D7A6B"
          className={`chain-particle cp-${i}`}
        >
          <animateMotion
            dur="4s"
            begin={`${i * 1.3}s`}
            repeatCount="indefinite"
            path="M0,0 C40,0 60,60 120,60 C180,60 200,120 240,120"
          />
        </circle>
      ))}

      {/* Stat text */}
      <text x="200" y="320" textAnchor="middle" fill="#C25B4B" fontSize="11" fontWeight="600" fontFamily="sans-serif">
        1 in 10 medicines in developing countries
      </text>
      <text x="200" y="336" textAnchor="middle" fill="#8A847D" fontSize="9" fontWeight="300" fontFamily="sans-serif">
        are substandard or falsified — WHO
      </text>
    </svg>
  );
}

function BlockchainSVG() {
  const blocks = [
    { x: 28, y: 30, hash: "0x7a3f...e1b2", prev: "0x0000...0000", nonce: "82741", num: 1247 },
    { x: 152, y: 30, hash: "0x9c2d...f4a8", prev: "0x7a3f...e1b2", nonce: "84078", num: 1248 },
    { x: 276, y: 30, hash: "0xb1e5...c9d3", prev: "0x9c2d...f4a8", nonce: "85415", num: 1249 },
  ];

  return (
    <svg viewBox="0 0 400 260" className="split-svg" aria-hidden="true">
      <defs>
        <linearGradient id="bc-header" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#3A3F5F" />
          <stop offset="100%" stopColor="#2D3348" />
        </linearGradient>
        <linearGradient id="bc-chain-grad" x1="0%" y1="0%" x2="100%" y2="0%">
          <stop offset="0%" stopColor="#3D7A6B" />
          <stop offset="100%" stopColor="#C49A6C" />
        </linearGradient>
      </defs>

      {/* Blockchain blocks */}
      {blocks.map((block, i) => (
        <g key={i} className={`bc-block bc-${i}`}>
          {/* Block body */}
          <rect x={block.x} y={block.y} width="108" height="148" rx="10"
            fill="rgba(61,122,107,0.03)" stroke="rgba(202,191,172,0.3)" strokeWidth="1.2" />

          {/* Block header */}
          <rect x={block.x} y={block.y} width="108" height="30" rx="10" fill="url(#bc-header)" />
          <rect x={block.x} y={block.y + 20} width="108" height="10" fill="url(#bc-header)" />
          <text x={block.x + 11} y={block.y + 20} fill="#C49A6C" fontSize="9" fontWeight="600" fontFamily="monospace">
            Block #{block.num}
          </text>

          {/* Hash */}
          <text x={block.x + 10} y={block.y + 52} fill="#8A847D" fontSize="7" fontFamily="sans-serif" fontWeight="500">
            HASH
          </text>
          <text x={block.x + 10} y={block.y + 64} fill="#3D7A6B" fontSize="8" fontFamily="monospace" fontWeight="600">
            {block.hash}
          </text>

          {/* Prev hash */}
          <text x={block.x + 10} y={block.y + 84} fill="#8A847D" fontSize="7" fontFamily="sans-serif" fontWeight="500">
            PREV HASH
          </text>
          <text x={block.x + 10} y={block.y + 96} fill="#C49A6C" fontSize="7.5" fontFamily="monospace" opacity="0.7">
            {block.prev}
          </text>

          {/* Nonce */}
          <text x={block.x + 10} y={block.y + 116} fill="#8A847D" fontSize="7" fontFamily="sans-serif" fontWeight="500">
            NONCE
          </text>
          <text x={block.x + 10} y={block.y + 128} fill="#33312E" fontSize="8.5" fontFamily="monospace">
            {block.nonce}
          </text>

          {/* Block verified indicator */}
          <circle cx={block.x + 92} cy={block.y + 130} r="8"
            fill="rgba(45,106,79,0.12)" stroke="#2D6A4F" strokeWidth="1" />
          <path d={`M${block.x + 88},${block.y + 130} l3,3 l5,-5`}
            fill="none" stroke="#2D6A4F" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
        </g>
      ))}

      {/* Chain links between blocks */}
      {[0, 1].map((i) => {
        const x1 = blocks[i].x + 108;
        const x2 = blocks[i + 1].x;
        const midX = (x1 + x2) / 2;
        const cy = 104;
        return (
          <g key={`chain-${i}`}>
            {/* Chain link line */}
            <line x1={x1 + 2} y1={cy} x2={x2 - 2} y2={cy}
              stroke="rgba(202,191,172,0.35)" strokeWidth="1.5" strokeLinecap="round" />
            {/* Arrow head */}
            <path d={`M${x2 - 6},${cy - 3} L${x2 - 1},${cy} L${x2 - 6},${cy + 3}`}
              fill="none" stroke="#3D7A6B" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
            {/* Animated pulse traveling along chain */}
            <circle cx={x1 + 2} cy={cy} r="3" fill="url(#bc-chain-grad)" className={`bc-chain-pulse bcp-${i}`} opacity="0">
              <animateMotion
                dur="1.8s"
                begin={`${1.2 + i * 0.8}s`}
                repeatCount="indefinite"
                path={`M0,0 L${x2 - x1 - 4},0`}
              />
            </circle>
            {/* Chain link icon */}
            <g transform={`translate(${midX}, ${cy})`}>
              <circle r="7" fill="#F5F3EF" stroke="rgba(61,122,107,0.25)" strokeWidth="1" />
              <path d="M-2.5,-1.5 A1.5,1.5,0,1,1,-2.5,1.5 L0,1.5 A1.5,1.5,0,1,0,0,-1.5 Z"
                fill="none" stroke="#3D7A6B" strokeWidth="1" strokeLinecap="round" />
            </g>
          </g>
        );
      })}

      {/* Bottom labels */}
      <text x="200" y="210" textAnchor="middle" fill="#3D7A6B" fontSize="8" fontWeight="600" fontFamily="sans-serif"
        letterSpacing="0.16em">
        SEPOLIA TESTNET
      </text>
      <text x="200" y="226" textAnchor="middle" fill="#8A847D" fontSize="7.5" fontWeight="300" fontFamily="sans-serif">
        Immutable, tamper-proof drug registration
      </text>
    </svg>
  );
}

function NeuralNetworkSVG() {
  /* Neural network: 4 input → 5 hidden → 4 hidden → 3 output */
  const inputNodes = [
    { y: 70, label: "Scans" },
    { y: 135, label: "Hashes" },
    { y: 200, label: "Geo" },
    { y: 265, label: "Time" },
  ];
  const hidden1 = [55, 110, 165, 220, 275];
  const hidden2 = [80, 145, 210, 275];
  const outputNodes = [
    { y: 105, label: "Verified", color: "#2D6A4F" },
    { y: 180, label: "Suspicious", color: "#B08D3B" },
    { y: 255, label: "Counterfeit", color: "#C25B4B" },
  ];

  const lx = { input: 50, h1: 150, h2: 250, output: 350 };
  let connIdx = 0;

  /* Define explicit routes for signal particles (input → h1 → h2 → output) */
  const signalRoutes = [
    { path: `M${lx.input},${inputNodes[0].y} L${lx.h1},${hidden1[0]} L${lx.h2},${hidden2[0]} L${lx.output},${outputNodes[0].y}`, color: "#2D6A4F" },
    { path: `M${lx.input},${inputNodes[1].y} L${lx.h1},${hidden1[2]} L${lx.h2},${hidden2[1]} L${lx.output},${outputNodes[0].y}`, color: "#2D6A4F" },
    { path: `M${lx.input},${inputNodes[2].y} L${lx.h1},${hidden1[3]} L${lx.h2},${hidden2[2]} L${lx.output},${outputNodes[1].y}`, color: "#B08D3B" },
    { path: `M${lx.input},${inputNodes[3].y} L${lx.h1},${hidden1[4]} L${lx.h2},${hidden2[3]} L${lx.output},${outputNodes[2].y}`, color: "#C25B4B" },
  ];

  return (
    <svg viewBox="0 0 400 330" className="split-svg" aria-hidden="true">
      <defs>
        {/* Define signal paths so animateMotion can reference them */}
        {signalRoutes.map((route, i) => (
          <path key={`route-${i}`} id={`nn-route-${i}`} d={route.path} />
        ))}
      </defs>

      {/* Layer labels */}
      <text x={lx.input} y="28" textAnchor="middle" fill="#8A847D" fontSize="7" fontWeight="600" fontFamily="sans-serif" letterSpacing="0.12em">INPUT</text>
      <text x={lx.h1} y="28" textAnchor="middle" fill="#8A847D" fontSize="7" fontWeight="600" fontFamily="sans-serif" letterSpacing="0.12em">HIDDEN</text>
      <text x={lx.h2} y="28" textAnchor="middle" fill="#8A847D" fontSize="7" fontWeight="600" fontFamily="sans-serif" letterSpacing="0.12em">HIDDEN</text>
      <text x={lx.output} y="28" textAnchor="middle" fill="#8A847D" fontSize="7" fontWeight="600" fontFamily="sans-serif" letterSpacing="0.12em">OUTPUT</text>

      {/* Connections: input → hidden1 */}
      {inputNodes.map((inp) =>
        hidden1.map((hy) => {
          const ci = connIdx++ % 12;
          return (
            <line key={`ih-${inp.y}-${hy}`}
              x1={lx.input} y1={inp.y} x2={lx.h1} y2={hy}
              stroke="#3D7A6B" strokeWidth="0.8" className={`nn-connection nnc-${ci}`} />
          );
        })
      )}

      {/* Connections: hidden1 → hidden2 */}
      {hidden1.map((h1y) =>
        hidden2.map((h2y) => {
          const ci = connIdx++ % 12;
          return (
            <line key={`hh-${h1y}-${h2y}`}
              x1={lx.h1} y1={h1y} x2={lx.h2} y2={h2y}
              stroke="#C49A6C" strokeWidth="0.8" className={`nn-connection nnc-${ci}`} />
          );
        })
      )}

      {/* Connections: hidden2 → output */}
      {hidden2.map((h2y) =>
        outputNodes.map((out) => {
          const ci = connIdx++ % 12;
          return (
            <line key={`ho-${h2y}-${out.y}`}
              x1={lx.h2} y1={h2y} x2={lx.output} y2={out.y}
              stroke={out.color} strokeWidth="0.8" className={`nn-connection nnc-${ci}`} />
          );
        })
      )}

      {/* Signal particles — travel along defined routes using mpath */}
      {signalRoutes.map((route, i) => (
        <circle key={`sig-${i}`} r="3" fill={route.color} opacity="0">
          <animateMotion dur="3s" begin={`${i * 0.8}s`} repeatCount="indefinite" fill="freeze">
            <mpath href={`#nn-route-${i}`} />
          </animateMotion>
          <animate attributeName="opacity" values="0;0.9;0.9;0" dur="3s" begin={`${i * 0.8}s`} repeatCount="indefinite" />
        </circle>
      ))}

      {/* Input nodes — drawn AFTER connections so they appear on top */}
      {inputNodes.map((node, i) => (
        <g key={`in-${i}`} className={`nn-node nnn-${i}`}>
          <circle cx={lx.input} cy={node.y} r="14"
            fill="#F5F3EF" stroke="#3D7A6B" strokeWidth="1.5" />
          <circle cx={lx.input} cy={node.y} r="5" fill="#3D7A6B" />
          <text x={lx.input} y={node.y + 24} textAnchor="middle"
            fill="#8A847D" fontSize="6.5" fontWeight="500" fontFamily="sans-serif">{node.label}</text>
        </g>
      ))}

      {/* Hidden layer 1 nodes */}
      {hidden1.map((y, i) => (
        <g key={`h1-${i}`} className={`nn-node nnn-${(i + 2) % 8}`}>
          <circle cx={lx.h1} cy={y} r="10"
            fill="#F5F3EF" stroke="rgba(61,122,107,0.4)" strokeWidth="1" />
          <circle cx={lx.h1} cy={y} r="4" fill="#3D7A6B" opacity="0.6" />
        </g>
      ))}

      {/* Hidden layer 2 nodes */}
      {hidden2.map((y, i) => (
        <g key={`h2-${i}`} className={`nn-node nnn-${(i + 4) % 8}`}>
          <circle cx={lx.h2} cy={y} r="10"
            fill="#F5F3EF" stroke="rgba(196,154,108,0.4)" strokeWidth="1" />
          <circle cx={lx.h2} cy={y} r="4" fill="#C49A6C" opacity="0.6" />
        </g>
      ))}

      {/* Output nodes with status colors */}
      {outputNodes.map((node, i) => (
        <g key={`out-${i}`}>
          {/* Glow ring */}
          <circle cx={lx.output} cy={node.y} r="22"
            fill={node.color} opacity="0.06"
            className={`nn-output-glow nno-${["verified", "suspicious", "counterfeit"][i]}`} />
          {/* Node */}
          <circle cx={lx.output} cy={node.y} r="16"
            fill="#F5F3EF" stroke={node.color} strokeWidth="2" />
          <circle cx={lx.output} cy={node.y} r="6" fill={node.color} />
          {/* Label */}
          <text x={lx.output} y={node.y + 28} textAnchor="middle"
            fill={node.color} fontSize="7" fontWeight="600" fontFamily="sans-serif">{node.label}</text>
        </g>
      ))}

      {/* Bottom label */}
      <text x="200" y="315" textAnchor="middle" fill="#3D7A6B" fontSize="7.5" fontWeight="600" fontFamily="sans-serif" letterSpacing="0.14em">
        AUTOENCODER + ISOLATION FOREST
      </text>
    </svg>
  );
}

function TechConstellationSVG() {
  /* Constellation of technologies around a central hub */
  const cx = 200, cy = 200;
  const techNodes = [
    { angle: 0, r: 120, label: "Sepolia", color: "#3D7A6B", icon: "S" },
    { angle: 45, r: 130, label: "Solidity", color: "#3D7A6B", icon: "S" },
    { angle: 90, r: 115, label: "IPFS", color: "#C49A6C", icon: "I" },
    { angle: 135, r: 125, label: "Isolation Forest", color: "#C49A6C", icon: "IF" },
    { angle: 180, r: 120, label: "FastAPI", color: "#3A3F5F", icon: "F" },
    { angle: 225, r: 130, label: "Next.js", color: "#3A3F5F", icon: "N" },
    { angle: 270, r: 115, label: "Supabase", color: "#8A847D", icon: "D" },
    { angle: 315, r: 125, label: "Flutter", color: "#8A847D", icon: "M" },
  ];

  const nodes = techNodes.map((t) => ({
    ...t,
    x: cx + Math.cos((t.angle * Math.PI) / 180) * t.r,
    y: cy + Math.sin((t.angle * Math.PI) / 180) * t.r,
  }));

  return (
    <svg viewBox="0 0 400 400" className="split-svg" aria-hidden="true">
      <defs>
        <radialGradient id="tc-hub-glow" cx="50%" cy="50%" r="35%">
          <stop offset="0%" stopColor="rgba(61,122,107,0.12)" />
          <stop offset="100%" stopColor="transparent" />
        </radialGradient>
        <radialGradient id="tc-outer-glow" cx="50%" cy="50%" r="50%">
          <stop offset="0%" stopColor="rgba(196,154,108,0.04)" />
          <stop offset="100%" stopColor="transparent" />
        </radialGradient>
      </defs>

      {/* Background */}
      <circle cx={cx} cy={cy} r="190" fill="url(#tc-outer-glow)" />

      {/* Orbit rings */}
      <circle cx={cx} cy={cy} r="120" fill="none" stroke="rgba(202,191,172,0.1)" strokeWidth="1" strokeDasharray="4,6" />
      <circle cx={cx} cy={cy} r="80" fill="none" stroke="rgba(202,191,172,0.08)" strokeWidth="1" />

      {/* Slowly rotating orbit ring with dots */}
      <g className="tc-orbit">
        {[0, 60, 120, 180, 240, 300].map((a, i) => {
          const nx = cx + Math.cos((a * Math.PI) / 180) * 80;
          const ny = cy + Math.sin((a * Math.PI) / 180) * 80;
          return <circle key={a} cx={nx} cy={ny} r="2" fill="#3D7A6B" opacity="0.2" className={`tc-data-dot tcd-${i}`} />;
        })}
      </g>

      {/* Counter-rotating orbit with amber dots */}
      <g className="tc-orbit-reverse">
        {[30, 90, 150, 210, 270, 330].map((a) => {
          const nx = cx + Math.cos((a * Math.PI) / 180) * 55;
          const ny = cy + Math.sin((a * Math.PI) / 180) * 55;
          return <circle key={a} cx={nx} cy={ny} r="1.5" fill="#C49A6C" opacity="0.15" />;
        })}
      </g>

      {/* Edges: connect each node to center hub */}
      {nodes.map((n, i) => (
        <line key={`e-${i}`}
          x1={cx} y1={cy} x2={n.x} y2={n.y}
          stroke={n.color} strokeWidth="1" className="tc-edge" />
      ))}

      {/* Edges: connect adjacent nodes */}
      {nodes.map((n, i) => {
        const next = nodes[(i + 1) % nodes.length];
        return (
          <line key={`adj-${i}`}
            x1={n.x} y1={n.y} x2={next.x} y2={next.y}
            stroke="rgba(202,191,172,0.12)" strokeWidth="0.8" className="tc-edge" />
        );
      })}

      {/* Hub center */}
      <circle cx={cx} cy={cy} r="40" fill="url(#tc-hub-glow)" className="tc-hub-pulse" />
      <circle cx={cx} cy={cy} r="28" fill="rgba(61,122,107,0.06)" stroke="rgba(61,122,107,0.25)" strokeWidth="1.5" />
      {/* Shield icon in hub */}
      <path
        d={`M${cx},${cy - 14} L${cx + 12},${cy - 8} L${cx + 12},${cy + 4} C${cx + 12},${cy + 10} ${cx + 6},${cy + 15} ${cx},${cy + 18} C${cx - 6},${cy + 15} ${cx - 12},${cy + 10} ${cx - 12},${cy + 4} L${cx - 12},${cy - 8} Z`}
        fill="rgba(61,122,107,0.15)" stroke="#3D7A6B" strokeWidth="1.5" />
      <text x={cx} y={cy + 32} textAnchor="middle" fill="#3D7A6B" fontSize="7" fontWeight="600" fontFamily="sans-serif" letterSpacing="0.1em">
        MEDICHAIN
      </text>

      {/* Tech nodes */}
      {nodes.map((n, i) => (
        <g key={`node-${i}`} className={`tc-node tcn-${i}`}>
          {/* Node circle */}
          <circle cx={n.x} cy={n.y} r="22"
            fill="rgba(255,255,255,0.7)" stroke={n.color} strokeWidth="1.5" />
          {/* Icon letter */}
          <text x={n.x} y={n.y + 4} textAnchor="middle"
            fill={n.color} fontSize="12" fontWeight="700" fontFamily="sans-serif">
            {n.icon}
          </text>
          {/* Label */}
          <text x={n.x} y={n.y + 36}
            textAnchor="middle" fill="#8A847D" fontSize="7" fontWeight="500" fontFamily="sans-serif">
            {n.label}
          </text>
        </g>
      ))}

    </svg>
  );
}

function MobileAppSVG() {
  /* s = module size, g = gap for the QR grid */
  const s = 4, g = 1;
  const m = s + g; /* 5px per module */

  /* Clean QR code as a 13x13 binary grid */
  const qr: number[][] = [
    [1,1,1,1,1,1,1,0,1,0,1,1,1],
    [1,0,0,0,0,0,1,0,0,1,0,0,1],
    [1,0,1,1,1,0,1,0,1,0,1,0,1],
    [1,0,1,1,1,0,1,0,1,1,0,1,0],
    [1,0,0,0,0,0,1,0,0,1,1,0,1],
    [1,1,1,1,1,1,1,0,1,0,1,0,1],
    [0,0,0,0,0,0,0,0,1,1,0,0,0],
    [1,0,1,0,1,1,0,1,0,1,1,0,1],
    [1,1,0,1,0,0,1,0,1,0,1,1,0],
    [0,1,1,0,1,1,0,1,0,1,0,0,1],
    [1,0,1,1,1,0,1,0,1,1,0,1,1],
    [1,0,0,0,0,0,1,0,0,1,1,0,0],
    [1,1,1,1,1,1,1,0,1,0,0,1,1],
  ];

  return (
    <svg viewBox="0 0 400 500" className="split-svg" aria-hidden="true">
      {/* Phone frame */}
      <rect x="100" y="20" width="200" height="460" rx="28" fill="#33312E" stroke="#CABFAC" strokeWidth="1.5" />
      <rect x="108" y="32" width="184" height="436" rx="20" fill="#FAFAF8" />

      {/* Status bar notch */}
      <rect x="165" y="38" width="70" height="5" rx="2.5" fill="rgba(202,191,172,0.4)" />

      {/* App header */}
      <text x="200" y="66" textAnchor="middle" fill="#33312E" fontSize="9" fontWeight="700" fontFamily="sans-serif" letterSpacing="0.12em">MEDICHAIN</text>
      <line x1="118" y1="74" x2="282" y2="74" stroke="rgba(202,191,172,0.2)" strokeWidth="0.5" />

      {/* ═══ Phase 1: QR Scan Screen ═══ */}
      <g className="phone-qr-screen">
        <text x="200" y="96" textAnchor="middle" fill="#8A847D" fontSize="8" fontWeight="500" fontFamily="sans-serif">
          Scan QR Code
        </text>

        {/* Corner brackets — positioned around QR area */}
        <g className="qr-bracket" stroke="#3D7A6B" strokeWidth="2" strokeLinecap="round" fill="none">
          <path d="M157,108 L157,102 L163,102" />
          <path d="M243,108 L243,102 L237,102" />
          <path d="M157,180 L157,186 L163,186" />
          <path d="M243,180 L243,186 L237,186" />
        </g>

        {/* QR code — clean 13x13 grid, centered */}
        <g transform="translate(168, 112)">
          {qr.map((row, ry) =>
            row.map((cell, cx) =>
              cell === 1 ? (
                <rect key={`${ry}-${cx}`}
                  x={cx * m} y={ry * m} width={s} height={s} rx="0.5"
                  fill="#33312E" />
              ) : null
            )
          )}
        </g>

        {/* Scan line — animates vertically across QR */}
        <line x1="164" y1="112" x2="236" y2="112"
          stroke="#3D7A6B" strokeWidth="1.5" strokeLinecap="round" opacity="0.5"
          className="qr-scan-line" />

        {/* Instruction */}
        <text x="200" y="206" textAnchor="middle" fill="#8A847D" fontSize="7" fontWeight="400" fontFamily="sans-serif">
          Point camera at medicine QR code
        </text>

        {/* Scan button */}
        <rect x="155" y="218" width="90" height="26" rx="13" fill="#3D7A6B" />
        <text x="193" y="231" textAnchor="middle" dominantBaseline="central" fill="white" fontSize="8" fontWeight="600" fontFamily="sans-serif" letterSpacing="0.06em">
          Scanning
        </text>
        {/* Animated dots after text */}
        {[0, 1, 2].map((i) => (
          <circle key={i} cx={218 + i * 4.5} cy="231" r="1" fill="white">
            <animate attributeName="opacity" values="0.2;1;0.2" dur="1.2s" begin={`${i * 0.25}s`} repeatCount="indefinite" />
          </circle>
        ))}
      </g>

      {/* ═══ Phase 2: Result Screen ═══ */}
      <g className="phone-result-screen">

        {/* Verified badge */}
        <g className="result-item ri-1">
          <rect x="118" y="82" width="164" height="30" rx="15" fill="rgba(45,106,79,0.1)" />
          <circle cx="140" cy="97" r="6" fill="#2D6A4F" />
          <path d="M137,97 l2,2.5 l4,-4.5" fill="none" stroke="white" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round" />
          <text x="153" y="100" fill="#2D6A4F" fontSize="9.5" fontWeight="700" fontFamily="sans-serif">VERIFIED</text>
          <text x="220" y="100" fill="#8A847D" fontSize="7" fontFamily="sans-serif">Batch #A2847</text>
        </g>

        {/* ── Pill + text info ── */}
        <g className="result-item ri-2">
          {/* Pill capsule — rotating ON ITS OWN AXIS via SVG animateTransform */}
          <g>
            <animateTransform attributeName="transform" type="rotate"
              from="0 150 168" to="360 150 168" dur="6s" repeatCount="indefinite" />
            {/* Outer capsule outline */}
            <ellipse cx="150" cy="168" rx="22" ry="11"
              fill="none" stroke="rgba(202,191,172,0.3)" strokeWidth="0.8" />
            {/* Left half — sage green */}
            <path d="M150,157 A11,11,0,0,0,150,179 Q138,179 132,168 Q138,157 150,157 Z"
              fill="rgba(61,122,107,0.25)" stroke="#3D7A6B" strokeWidth="1.2" />
            {/* Right half — golden amber */}
            <path d="M150,157 A11,11,0,0,1,150,179 Q162,179 168,168 Q162,157 150,157 Z"
              fill="rgba(196,154,108,0.25)" stroke="#C49A6C" strokeWidth="1.2" />
            {/* Center seam */}
            <line x1="150" y1="157" x2="150" y2="179" stroke="rgba(202,191,172,0.4)" strokeWidth="0.6" />
            {/* Shine */}
            <ellipse cx="144" cy="164" rx="5" ry="2.5" fill="rgba(255,255,255,0.25)" />
          </g>

          {/* Text placeholder lines */}
          <rect x="186" y="140" width="82" height="5" rx="2.5" fill="rgba(202,191,172,0.35)" />
          <rect x="186" y="150" width="58" height="4" rx="2" fill="rgba(202,191,172,0.25)" />
          <rect x="186" y="160" width="92" height="4" rx="2" fill="rgba(202,191,172,0.25)" />
          <rect x="186" y="170" width="44" height="4" rx="2" fill="rgba(202,191,172,0.2)" />
          <rect x="186" y="180" width="70" height="4" rx="2" fill="rgba(202,191,172,0.2)" />
          <rect x="186" y="190" width="56" height="4" rx="2" fill="rgba(202,191,172,0.15)" />
        </g>

        {/* ── Supply chain section ── */}
        <g className="result-item ri-3">
          <line x1="118" y1="208" x2="282" y2="208" stroke="rgba(202,191,172,0.2)" strokeWidth="0.5" />
          <text x="118" y="224" fill="#8A847D" fontSize="7" fontWeight="600" fontFamily="sans-serif" letterSpacing="0.08em">
            SUPPLY CHAIN
          </text>
          {/* Timeline dots */}
          {[0, 1, 2, 3].map((i) => (
            <g key={`sc-${i}`}>
              <circle cx={135 + i * 40} cy="240" r="4"
                fill={i < 3 ? "rgba(61,122,107,0.2)" : "rgba(202,191,172,0.2)"}
                stroke={i < 3 ? "#3D7A6B" : "#CABFAC"} strokeWidth="1" />
              {i < 3 && <line x1={139 + i * 40} y1="240" x2={171 + i * 40} y2="240"
                stroke="rgba(202,191,172,0.3)" strokeWidth="1" />}
            </g>
          ))}
          {/* Text lines below timeline */}
          <rect x="118" y="254" width="140" height="3.5" rx="1.75" fill="rgba(202,191,172,0.25)" />
          <rect x="118" y="262" width="100" height="3.5" rx="1.75" fill="rgba(202,191,172,0.2)" />
          <rect x="118" y="270" width="120" height="3.5" rx="1.75" fill="rgba(202,191,172,0.18)" />
        </g>

        {/* ── Mini map / risk chart ── */}
        <g className="result-item ri-4">
          <line x1="118" y1="284" x2="282" y2="284" stroke="rgba(202,191,172,0.2)" strokeWidth="0.5" />
          <text x="118" y="299" fill="#8A847D" fontSize="7" fontWeight="600" fontFamily="sans-serif" letterSpacing="0.08em">
            RISK MAP
          </text>

          {/* Map container */}
          <rect x="118" y="306" width="164" height="100" rx="8"
            fill="rgba(61,122,107,0.03)" stroke="rgba(202,191,172,0.2)" strokeWidth="0.8" />

          {/* Grid lines */}
          {[336, 366].map((y) => (
            <line key={y} x1="118" y1={y} x2="282" y2={y} stroke="rgba(202,191,172,0.1)" strokeWidth="0.5" />
          ))}
          {[160, 200, 240].map((x) => (
            <line key={x} x1={x} y1="306" x2={x} y2="406" stroke="rgba(202,191,172,0.07)" strokeWidth="0.5" />
          ))}

          {/* Area fill under chart line */}
          <path d="M130,392 L158,376 L185,380 L210,356 L238,346 L265,336 L265,400 L130,400 Z"
            fill="rgba(61,122,107,0.06)" />

          {/* Chart line */}
          <polyline points="130,392 158,376 185,380 210,356 238,346 265,336"
            fill="none" stroke="#3D7A6B" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"
            className="map-line-draw" />

          {/* Data dots */}
          <circle cx="130" cy="392" r="3" fill="#3D7A6B" className="map-dot md-1" opacity="0" />
          <circle cx="158" cy="376" r="2.5" fill="#C25B4B" className="map-dot md-2" opacity="0" />
          <circle cx="185" cy="380" r="2.5" fill="#3D7A6B" className="map-dot md-1" opacity="0" />
          <circle cx="210" cy="356" r="2.5" fill="#B08D3B" className="map-dot md-3" opacity="0" />
          <circle cx="238" cy="346" r="2.5" fill="#3D7A6B" className="map-dot md-2" opacity="0" />
          <circle cx="265" cy="336" r="3" fill="#2D6A4F" className="map-dot md-1" opacity="0" />
        </g>
      </g>
    </svg>
  );
}

/* ─── Main Page ─── */

export default function LandingPage() {
  return (
    <div className="page-shell">
      <header className="site-header">
        <Link href="/" className="logo-wrap">
          <div className="logo-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
            </svg>
          </div>
          <div className="logo-text">
            <span className="logo-title">MediChain</span>
          </div>
        </Link>
        <nav className="site-nav desktop-nav">
          {navLinks.map((link) => (
            <a key={link.href} href={link.href}>
              {link.label}
            </a>
          ))}
          <Link href="/signin">Sign In</Link>
          <Link href="/signup" className="site-nav-cta">
            Get Started
          </Link>
        </nav>
        <MobileNav />
      </header>

      <main className="site-main">
      <div className="landing-page">
      {/* ── Hero ── */}
      <div className="landing-hero">
        <div className="hero-content stagger">
          <span className="hero-kicker">Powered by Sepolia Blockchain</span>
          <h1>
            Protecting Lives with Verified Medicine
          </h1>
          <p className="hero-subtitle">
            Blockchain verification and AI-powered risk detection ensuring every
            medicine in the supply chain is authentic, safe, and traceable.
          </p>
          <div className="hero-buttons">
            <Link href="/signup" className="button">
              Get Started Free &rarr;
            </Link>
            <Link href="/dashboard" className="button secondary">
              View Demo Dashboard
            </Link>
          </div>
          <div className="badge-row" style={{ marginTop: 24 }}>
            <span className="badge">Blockchain Secured</span>
            <span className="badge">AI Powered</span>
            <span className="badge">Real-time Alerts</span>
          </div>
        </div>
      </div>

      {/* ── Content sections ── */}
      <div className="landing-content">

        {/* 1. The Problem — SVG left, text right */}
        <section className="split-section" id="features">
          <div className="split-visual">
            <SupplyChainSVG />
          </div>
          <div className="split-text">
            <div className="section-header">
              <span className="section-kicker">The Problem</span>
              <h2>Counterfeit drugs kill over 1 million people every year.</h2>
            </div>
            <p className="section-body">
              Pharmaceutical supply chains span continents with dozens of handoffs.
              At each step, counterfeit drugs can enter the chain undetected. Current
              paper-based tracking is fragmented, slow, and easy to forge. MediChain
              replaces it with cryptographic proof at every step.
            </p>
          </div>
        </section>

        {/* 2. How It Works — text left, SVG right */}
        <section className="split-section split-reverse" id="how-it-works">
          <div className="split-visual">
            <BlockchainSVG />
          </div>
          <div className="split-text">
            <div className="section-header">
              <span className="section-kicker">How It Works</span>
              <h2>SHA-256 hashing, on-chain proof, instant verification.</h2>
            </div>
            <p className="section-body">
              Every drug batch is registered with a cryptographic hash stored on
              the Sepolia blockchain. IPFS pins the full metadata. At every handoff,
              custody is signed on-chain. Patients scan a QR code to verify the
              entire chain in seconds.
            </p>
            <div className="steps-grid">
              <div className="step-card">
                <div className="step-number">01</div>
                <h3>Register</h3>
                <p>Manufacturer hashes drug metadata and registers on-chain.</p>
              </div>
              <div className="step-card">
                <div className="step-number">02</div>
                <h3>Track</h3>
                <p>Every custody transfer is signed and recorded on blockchain.</p>
              </div>
              <div className="step-card">
                <div className="step-number">03</div>
                <h3>Scan</h3>
                <p>QR code scanned at any point verifies full chain instantly.</p>
              </div>
              <div className="step-card">
                <div className="step-number">04</div>
                <h3>Protect</h3>
                <p>AI flags anomalies; counterfeits are caught before reaching patients.</p>
              </div>
            </div>
          </div>
        </section>

        {/* Stats bar */}
        <section className="landing-section">
          <div className="stats-bar">
            <div className="stat">
              <span className="stat-value">25K+</span>
              <span className="stat-label">Drugs tracked</span>
            </div>
            <div className="stat">
              <span className="stat-value">99.5%</span>
              <span className="stat-label">Detection accuracy</span>
            </div>
            <div className="stat">
              <span className="stat-value">15</span>
              <span className="stat-label">Cities covered</span>
            </div>
            <div className="stat">
              <span className="stat-value">1M+</span>
              <span className="stat-label">Scans processed</span>
            </div>
            <div className="stat">
              <span className="stat-value">&lt;2s</span>
              <span className="stat-label">Verification time</span>
            </div>
          </div>
        </section>

        {/* 3. AI Risk Detection — SVG left, text right */}
        <section className="split-section" id="impact">
          <div className="split-visual">
            <NeuralNetworkSVG />
          </div>
          <div className="split-text">
            <div className="section-header">
              <span className="section-kicker">AI Risk Detection</span>
              <h2>Machine learning that catches what humans miss.</h2>
            </div>
            <p className="section-body">
              An AutoEncoder and Isolation Forest analyze every scan for
              anomalies — duplicate scans across cities, impossible travel patterns,
              hash mismatches, geographic outliers. Each drug gets a real-time
              risk score from 0 to 100.
            </p>
            <div className="class-grid">
              <div className="class-card class-verified">
                <div className="class-icon">&#10003;</div>
                <h4>Verified</h4>
                <p>Authentic drug, full chain intact</p>
                <span className="class-pattern">Risk score 0–20</span>
              </div>
              <div className="class-card class-suspicious">
                <div className="class-icon">?</div>
                <h4>Suspicious</h4>
                <p>Anomalies detected, needs review</p>
                <span className="class-pattern">Risk score 21–60</span>
              </div>
              <div className="class-card class-counterfeit">
                <div className="class-icon">!</div>
                <h4>Counterfeit</h4>
                <p>High-confidence counterfeit flag</p>
                <span className="class-pattern">Risk score 61–100</span>
              </div>
            </div>
          </div>
        </section>

        {/* 4. Technology — text left, SVG right */}
        <section className="split-section split-reverse" id="technology">
          <div className="split-visual">
            <TechConstellationSVG />
          </div>
          <div className="split-text">
            <div className="section-header">
              <span className="section-kicker">Technology</span>
              <h2>Full-stack, from blockchain to mobile.</h2>
            </div>
            <div className="tech-columns tech-columns-compact">
              <div className="tech-col">
                <h4>Blockchain</h4>
                <ul>
                  <li>Sepolia testnet</li>
                  <li>Solidity smart contracts</li>
                  <li>IPFS via Pinata</li>
                </ul>
              </div>
              <div className="tech-col">
                <h4>ML / AI</h4>
                <ul>
                  <li>AutoEncoder</li>
                  <li>Isolation Forest</li>
                  <li>FastAPI serving</li>
                </ul>
              </div>
              <div className="tech-col">
                <h4>Backend</h4>
                <ul>
                  <li>Next.js 14 (App Router)</li>
                  <li>Supabase (Postgres + Auth)</li>
                  <li>Real-time subscriptions</li>
                </ul>
              </div>
              <div className="tech-col">
                <h4>Mobile</h4>
                <ul>
                  <li>Flutter 3.x / Dart</li>
                  <li>QR scanner + crypto</li>
                  <li>Riverpod state</li>
                </ul>
              </div>
            </div>
            <div className="tech-tags">
              <span className="t-tag">Sepolia</span>
              <span className="t-tag">Solidity</span>
              <span className="t-tag">IPFS</span>
              <span className="t-tag">AutoEncoder</span>
              <span className="t-tag">FastAPI</span>
              <span className="t-tag">Next.js</span>
              <span className="t-tag">Supabase</span>
              <span className="t-tag">Flutter</span>
              <span className="t-tag">ethers.js</span>
            </div>
          </div>
        </section>

        {/* 5. Companion App — SVG left, text right */}
        <section className="split-section">
          <div className="split-visual">
            <MobileAppSVG />
          </div>
          <div className="split-text">
            <div className="section-header">
              <span className="section-kicker">Mobile App</span>
              <h2>Scan, verify, and report — right from your phone.</h2>
            </div>
            <div className="app-features-list">
              <div className="app-feature">
                <h4>Instant QR Verification</h4>
                <p>Scan any drug&apos;s QR code to verify authenticity against the blockchain in under 2 seconds.</p>
              </div>
              <div className="app-feature">
                <h4>Supply Chain Timeline</h4>
                <p>View the complete custody chain from manufacturer to your hands, every handoff verified.</p>
              </div>
              <div className="app-feature">
                <h4>AI Risk Score</h4>
                <p>Real-time risk assessment powered by AutoEncoder, analyzing patterns across millions of scans.</p>
              </div>
              <div className="app-feature">
                <h4>Report Counterfeits</h4>
                <p>Flag suspicious drugs instantly. Reports feed into the live heatmap and alert system.</p>
              </div>
            </div>
          </div>
        </section>

        {/* Mission */}
        <section className="landing-section landing-mission">
          <div className="section-header" style={{ alignItems: "center" }}>
            <span className="section-kicker">Our Mission</span>
            <h2>Drug safety shouldn&apos;t depend on where you live.</h2>
          </div>
          <p className="section-body">
            In developing countries, 1 in 10 medical products is substandard or
            falsified. MediChain makes pharmaceutical verification accessible
            to everyone — from large distributors to individual patients with
            nothing more than a smartphone.
          </p>
        </section>

        {/* CTA */}
        <section className="landing-section landing-cta">
          <h2>Built with purpose. Ready for partnership.</h2>
          <Link href="/signup" className="cta-link">Get started &rarr;</Link>
        </section>
        </div>
      </div>
      </main>

      <footer className="site-footer">
        <div>
          <strong>MediChain</strong>
          <span>Blockchain-verified pharmaceutical safety.</span>
        </div>
        <div>
          <span>Powered by Sepolia &middot; Built with purpose.</span>
          <a href="mailto:hello@medichain.io">hello@medichain.io</a>
        </div>
      </footer>
    </div>
  );
}
