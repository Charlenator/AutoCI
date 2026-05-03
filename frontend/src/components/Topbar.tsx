"use client";

import { usePathname } from "next/navigation";

const PAGE_NAMES: Record<string, string> = {
  "/": "Chat",
  "/candidates": "Candidate Search",
  "/cis": "Continuous Improvement",
  "/system-diagram": "System Diagram",
};

export default function Topbar() {
  const pathname = usePathname() ?? "/";
  const pageName = PAGE_NAMES[pathname] || "Dashboard";

  return (
    <header className="topbar">
      <div className="crumb">
        <span>AutoCI</span>
        <span className="sep">/</span>
        <span className="here">{pageName}</span>
      </div>

    </header>
  );
}
