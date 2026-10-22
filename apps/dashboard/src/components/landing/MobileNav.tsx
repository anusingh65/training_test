"use client";

import { useState } from "react";
import Link from "next/link";

const links = [
  { href: "#features", label: "Features" },
  { href: "#how-it-works", label: "How It Works" },
  { href: "#technology", label: "Technology" },
  { href: "#impact", label: "Impact" },
  { href: "/signin", label: "Sign In" },
  { href: "/signup", label: "Get Started" },
];

export default function MobileNav() {
  const [open, setOpen] = useState(false);
  return (
    <div className="mobile-nav">
      <button className="burger" onClick={() => setOpen(!open)} aria-label="Menu">
        <span className={`burger-line ${open ? "open" : ""}`} />
        <span className={`burger-line ${open ? "open" : ""}`} />
        <span className={`burger-line ${open ? "open" : ""}`} />
      </button>
      {open && (
        <div className="mobile-dropdown">
          {links.map((l) => (
            <Link key={l.href} href={l.href} onClick={() => setOpen(false)}>
              {l.label}
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
