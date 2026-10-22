"use client";

import { useState } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import {
  Shield, Mail, Lock, User, ArrowRight, Eye, EyeOff,
  Building2, Truck, Stethoscope, ShieldCheck,
} from "lucide-react";
const roles = [
  {
    id: "manufacturer",
    label: "Manufacturer",
    description: "Register drugs & manage supply chain",
    icon: Building2,
    color: "text-primary",
    bg: "bg-primary/10",
    border: "border-primary/30",
  },
  {
    id: "distributor",
    label: "Distributor",
    description: "Track & transfer drug custody",
    icon: Truck,
    color: "text-suspicious",
    bg: "bg-suspicious/10",
    border: "border-suspicious/30",
  },
  {
    id: "pharmacy",
    label: "Pharmacy",
    description: "Verify incoming drug shipments",
    icon: Stethoscope,
    color: "text-verified",
    bg: "bg-verified/10",
    border: "border-verified/30",
  },
  {
    id: "regulator",
    label: "Regulator",
    description: "Monitor & audit supply chain",
    icon: ShieldCheck,
    color: "text-accent",
    bg: "bg-accent/10",
    border: "border-accent/30",
  },
];

function SupplyChainNetworkSVG() {
  /* Waypoints along the supply chain path */
  const waypoints = [
    { x: 60, y: 70, label: "Manufacture", color: "#3D7A6B", step: "01" },
    { x: 200, y: 115, label: "Distribute", color: "#B08D3B", step: "02" },
    { x: 340, y: 200, label: "Verify", color: "#2D6A4F", step: "03" },
    { x: 200, y: 285, label: "Dispense", color: "#3A3F5F", step: "04" },
    { x: 60, y: 340, label: "Patient Safe", color: "#2D6A4F", step: "05" },
  ];

  return (
    <svg viewBox="0 0 400 430" width="520" height="560" aria-hidden="true">
      <defs>
        <radialGradient id="su-glow" cx="50%" cy="50%" r="45%">
          <stop offset="0%" stopColor="rgba(61,122,107,0.06)" />
          <stop offset="100%" stopColor="transparent" />
        </radialGradient>
        <linearGradient id="su-path-grad" x1="0%" y1="0%" x2="0%" y2="100%">
          <stop offset="0%" stopColor="#3D7A6B" />
          <stop offset="50%" stopColor="#C49A6C" />
          <stop offset="100%" stopColor="#2D6A4F" />
        </linearGradient>
        <linearGradient id="su-shield-fill" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="rgba(61,122,107,0.12)" />
          <stop offset="100%" stopColor="rgba(45,106,79,0.08)" />
        </linearGradient>

        {/* Main flow path */}
        <path
          id="su-flow"
          d="M60,70 C130,70 140,115 200,115 C260,115 280,200 340,200 C280,200 260,285 200,285 C140,285 130,340 60,340"
        />
      </defs>

      {/* Background glow */}
      <circle cx="200" cy="210" r="180" fill="url(#su-glow)" />

      {/* ── Supply chain flow path ── */}
      <path
        d="M60,70 C130,70 140,115 200,115 C260,115 280,200 340,200 C280,200 260,285 200,285 C140,285 130,340 60,340"
        fill="none"
        stroke="rgba(202,191,172,0.25)"
        strokeWidth="2"
        strokeDasharray="8,5"
        className="su-path-draw"
      />

      {/* Colored overlay path that draws in */}
      <path
        d="M60,70 C130,70 140,115 200,115 C260,115 280,200 340,200 C280,200 260,285 200,285 C140,285 130,340 60,340"
        fill="none"
        stroke="url(#su-path-grad)"
        strokeWidth="2"
        strokeLinecap="round"
        strokeDasharray="600"
        strokeDashoffset="600"
        className="su-path-color"
      />

      {/* ── Traveling dot along path ── */}
      {[0, 1, 2].map((i) => (
        <circle key={`dot-${i}`} r="3.5" fill="#3D7A6B" opacity="0">
          <animateMotion dur="6s" begin={`${i * 2}s`} repeatCount="indefinite">
            <mpath href="#su-flow" />
          </animateMotion>
          <animate attributeName="opacity" values="0;0.8;0.8;0" dur="6s" begin={`${i * 2}s`} repeatCount="indefinite" />
        </circle>
      ))}

      {/* ── Waypoint nodes ── */}
      {waypoints.map((wp, i) => (
        <g key={`wp-${i}`} className={`su-waypoint su-wp-${i}`}>
          {/* Outer glow ring */}
          <circle cx={wp.x} cy={wp.y} r="28" fill={`${wp.color}08`} stroke={`${wp.color}18`} strokeWidth="1" />

          {/* Node circle */}
          <circle cx={wp.x} cy={wp.y} r="20" fill="white" stroke={wp.color} strokeWidth="1.8" />

          {/* Step number */}
          <text x={wp.x} y={wp.y + 1} textAnchor="middle" dominantBaseline="central"
            fill={wp.color} fontSize="11" fontWeight="700" fontFamily="sans-serif">
            {wp.step}
          </text>

          {/* Label */}
          <text x={wp.x} y={wp.y + 36} textAnchor="middle"
            fill="#6B6560" fontSize="8" fontWeight="600" fontFamily="sans-serif">
            {wp.label}
          </text>

          {/* Small verified check on completed nodes */}
          {i < 4 && (
            <g>
              <circle cx={wp.x + 16} cy={wp.y - 14} r="5.5" fill="white" stroke="#2D6A4F" strokeWidth="1" />
              <path
                d={`M${wp.x + 13},${wp.y - 14} l2,2.5 l4,-4`}
                fill="none" stroke="#2D6A4F" strokeWidth="1.2" strokeLinecap="round" strokeLinejoin="round"
              />
            </g>
          )}
        </g>
      ))}

      {/* ── Central shield emblem ── */}
      <g className="su-shield-group">
        {/* Pulse rings */}
        <circle cx="200" cy="200" r="48" fill="none" stroke="rgba(61,122,107,0.06)" strokeWidth="1" className="su-shield-ring su-sr-0" />
        <circle cx="200" cy="200" r="58" fill="none" stroke="rgba(61,122,107,0.04)" strokeWidth="0.8" className="su-shield-ring su-sr-1" />

        {/* Shield background */}
        <circle cx="200" cy="200" r="36" fill="white" stroke="rgba(61,122,107,0.2)" strokeWidth="1" />

        {/* Shield icon */}
        <path
          d="M200,182 l-14,5.5 v11 c0,9 5.5,15 14,18.5 8.5,-3.5 14,-9.5 14,-18.5 v-11 z"
          fill="url(#su-shield-fill)" stroke="#3D7A6B" strokeWidth="1.8" strokeLinejoin="round"
          className="su-shield-path"
        />

        {/* Animated checkmark */}
        <polyline
          points="192,199 198,205 210,192"
          fill="none" stroke="#3D7A6B" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"
          className="su-checkmark"
        />
      </g>

      {/* ── Bottom: blockchain hash strip ── */}
      <g className="su-hash-strip">
        <rect x="40" y="388" width="320" height="28" rx="8" fill="rgba(58,63,95,0.04)" stroke="rgba(202,191,172,0.2)" strokeWidth="0.8" />

        {/* 3 mini blocks — evenly spaced inside the strip */}
        {[
          { x: 52, hash: "0x7a3f" },
          { x: 170, hash: "0x9c2d" },
          { x: 288, hash: "0xb1e5" },
        ].map((b, i) => (
          <g key={`hb-${i}`}>
            <rect x={b.x} y="393" width="60" height="18" rx="4" fill="rgba(61,122,107,0.05)" stroke="rgba(61,122,107,0.15)" strokeWidth="0.6" />
            <text x={b.x + 30} y="405" textAnchor="middle" fill="#3D7A6B" fontSize="7" fontFamily="monospace" fontWeight="600">
              {b.hash}
            </text>
            {/* Chain link arrow */}
            {i < 2 && (
              <>
                <line x1={b.x + 63} y1="402" x2={b.x + 115} y2="402" stroke="rgba(202,191,172,0.35)" strokeWidth="1" />
                <circle cx={b.x + 89} cy="402" r="2" fill="#C49A6C" opacity="0" className={`su-chain-dot su-cd-${i}`}>
                  <animate attributeName="opacity" values="0;0.8;0" dur="2s" begin={`${i * 0.8}s`} repeatCount="indefinite" />
                </circle>
              </>
            )}
          </g>
        ))}
      </g>

      {/* Label */}
      <text x="200" y="426" textAnchor="middle" fill="#8A847D" fontSize="7" fontWeight="500" fontFamily="sans-serif" letterSpacing="0.12em">
        BLOCKCHAIN VERIFIED SUPPLY CHAIN
      </text>
    </svg>
  );
}

export default function SignUpPage() {
  const [step, setStep] = useState<1 | 2>(1);
  const [selectedRole, setSelectedRole] = useState("");
  const [form, setForm] = useState({ name: "", email: "", password: "", org: "" });
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    await new Promise((r) => setTimeout(r, 1500));
    window.location.href = "/dashboard";
  }

  return (
    <div className="min-h-screen bg-background flex">
      {/* Left - Animated SVG panel */}
      <div className="hidden lg:flex lg:w-1/2 relative items-center justify-center overflow-hidden bg-white/30">
        <div className="absolute inset-0 opacity-[0.04]" style={{
          backgroundImage: "linear-gradient(#CABFAC 1px, transparent 1px), linear-gradient(90deg, #CABFAC 1px, transparent 1px)",
          backgroundSize: "60px 60px",
        }} />
        <div className="absolute inset-0" style={{
          background: "radial-gradient(ellipse at center, transparent 20%, #E7E6E3 70%)",
        }} />

        <div className="relative z-10 flex flex-col items-center">
          <motion.div
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 1, ease: "easeOut" }}
          >
            <SupplyChainNetworkSVG />
          </motion.div>

          <motion.div
            className="text-center mt-6 max-w-sm"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.5 }}
          >
            <h2 className="text-2xl font-bold gradient-text">Join the Network</h2>
            <p className="text-text-muted text-sm mt-2 leading-relaxed">
              Become part of the blockchain-verified pharmaceutical supply chain and help protect patients worldwide.
            </p>
          </motion.div>
        </div>
      </div>

      {/* Right - Form */}
      <div className="flex-1 flex items-center justify-center p-8">
        <motion.div
          className="w-full max-w-md"
          initial={{ opacity: 0, x: 30 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.6 }}
        >
          {/* Logo */}
          <Link href="/" className="flex items-center gap-2.5 mb-10">
            <div className="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center">
              <Shield size={22} className="text-primary" />
            </div>
            <span className="text-xl font-bold gradient-text">MediChain</span>
          </Link>

          {/* Step indicator */}
          <div className="flex items-center gap-3 mb-8">
            <div className={`flex items-center gap-2 text-sm font-medium ${step >= 1 ? "text-primary" : "text-text-muted"}`}>
              <span className={`w-7 h-7 rounded-full flex items-center justify-center text-xs ${step >= 1 ? "bg-primary text-white" : "bg-white border border-border text-text-muted"}`}>1</span>
              Role
            </div>
            <div className={`flex-1 h-px ${step >= 2 ? "bg-primary" : "bg-border"}`} />
            <div className={`flex items-center gap-2 text-sm font-medium ${step >= 2 ? "text-primary" : "text-text-muted"}`}>
              <span className={`w-7 h-7 rounded-full flex items-center justify-center text-xs ${step >= 2 ? "bg-primary text-white" : "bg-white border border-border text-text-muted"}`}>2</span>
              Details
            </div>
          </div>

          {step === 1 ? (
            <motion.div
              key="step1"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
            >
              <h1 className="text-2xl font-bold text-text">Choose your role</h1>
              <p className="text-text-muted text-sm mt-1 mb-6">Select how you&apos;ll participate in the supply chain</p>

              <div className="space-y-3">
                {roles.map((role) => {
                  const Icon = role.icon;
                  const isSelected = selectedRole === role.id;
                  return (
                    <button
                      key={role.id}
                      type="button"
                      onClick={() => setSelectedRole(role.id)}
                      className={`w-full flex items-center gap-4 p-4 rounded-xl border transition-all text-left ${
                        isSelected
                          ? `${role.bg} ${role.border} border`
                          : "bg-white border-border hover:border-primary/20"
                      }`}
                    >
                      <div className={`w-11 h-11 rounded-xl ${role.bg} flex items-center justify-center ${role.color}`}>
                        <Icon size={20} />
                      </div>
                      <div className="flex-1">
                        <p className={`font-medium text-sm ${isSelected ? "text-text" : "text-text"}`}>{role.label}</p>
                        <p className="text-xs text-text-muted">{role.description}</p>
                      </div>
                      <div className={`w-5 h-5 rounded-full border-2 flex items-center justify-center ${
                        isSelected ? "border-primary bg-primary" : "border-border"
                      }`}>
                        {isSelected && <div className="w-2 h-2 rounded-full bg-white" />}
                      </div>
                    </button>
                  );
                })}
              </div>

              <button
                onClick={() => selectedRole && setStep(2)}
                disabled={!selectedRole}
                className="w-full mt-6 py-3 bg-primary hover:bg-primary/90 text-white font-medium rounded-xl transition-all disabled:opacity-30 flex items-center justify-center gap-2"
              >
                Continue
                <ArrowRight size={16} />
              </button>
            </motion.div>
          ) : (
            <motion.div
              key="step2"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
            >
              <button
                onClick={() => setStep(1)}
                className="text-sm text-text-muted hover:text-text mb-4 flex items-center gap-1"
              >
                <ArrowRight size={14} className="rotate-180" />
                Back
              </button>

              <h1 className="text-2xl font-bold text-text">Create your account</h1>
              <p className="text-text-muted text-sm mt-1 mb-6">
                Signing up as <span className="text-primary capitalize">{selectedRole}</span>
              </p>

              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <label className="block text-sm text-text-muted mb-1.5 font-medium">Full Name</label>
                  <div className="relative">
                    <User size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-text-muted" />
                    <input
                      type="text"
                      required
                      value={form.name}
                      onChange={(e) => setForm({ ...form, name: e.target.value })}
                      className="w-full pl-10 pr-4 py-3 bg-white border border-border rounded-xl text-sm text-text focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary/30 transition-all placeholder:text-text-muted/50"
                      placeholder="John Doe"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-sm text-text-muted mb-1.5 font-medium">Organization</label>
                  <div className="relative">
                    <Building2 size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-text-muted" />
                    <input
                      type="text"
                      required
                      value={form.org}
                      onChange={(e) => setForm({ ...form, org: e.target.value })}
                      className="w-full pl-10 pr-4 py-3 bg-white border border-border rounded-xl text-sm text-text focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary/30 transition-all placeholder:text-text-muted/50"
                      placeholder="Company name"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-sm text-text-muted mb-1.5 font-medium">Email</label>
                  <div className="relative">
                    <Mail size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-text-muted" />
                    <input
                      type="email"
                      required
                      value={form.email}
                      onChange={(e) => setForm({ ...form, email: e.target.value })}
                      className="w-full pl-10 pr-4 py-3 bg-white border border-border rounded-xl text-sm text-text focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary/30 transition-all placeholder:text-text-muted/50"
                      placeholder="you@company.com"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-sm text-text-muted mb-1.5 font-medium">Password</label>
                  <div className="relative">
                    <Lock size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-text-muted" />
                    <input
                      type={showPassword ? "text" : "password"}
                      required
                      value={form.password}
                      onChange={(e) => setForm({ ...form, password: e.target.value })}
                      className="w-full pl-10 pr-12 py-3 bg-white border border-border rounded-xl text-sm text-text focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary/30 transition-all placeholder:text-text-muted/50"
                      placeholder="Minimum 8 characters"
                      minLength={8}
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute right-3.5 top-1/2 -translate-y-1/2 text-text-muted hover:text-text"
                    >
                      {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                    </button>
                  </div>
                </div>

                <button
                  type="submit"
                  disabled={loading}
                  className="w-full py-3 bg-primary hover:bg-primary/90 text-white font-medium rounded-xl transition-all hover:shadow-lg hover:shadow-primary/20 disabled:opacity-50 flex items-center justify-center gap-2"
                >
                  {loading ? (
                    <motion.div
                      className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full"
                      animate={{ rotate: 360 }}
                      transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                    />
                  ) : (
                    <>
                      Create Account
                      <ArrowRight size={16} />
                    </>
                  )}
                </button>

                <p className="text-xs text-text-muted text-center mt-2">
                  By creating an account, you agree to our Terms of Service and Privacy Policy.
                </p>
              </form>
            </motion.div>
          )}

          <p className="text-center text-sm text-text-muted mt-8">
            Already have an account?{" "}
            <Link href="/signin" className="text-primary hover:underline font-medium">
              Sign in
            </Link>
          </p>
        </motion.div>
      </div>
    </div>
  );
}
