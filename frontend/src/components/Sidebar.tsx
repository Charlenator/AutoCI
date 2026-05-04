"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import KnowledgeSourcesPanel from "./chat/KnowledgeSourcesPanel";

interface NavItem {
  href: string;
  label: string;
  icon: React.ReactNode;
}

const NAV_ITEMS: NavItem[] = [
  {
    href: "/",
    label: "RAG Chat",
    icon: (
      <svg className="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
      </svg>
    ),
  },
  {
    href: "/candidates",
    label: "Candidate Search",
    icon: (
      <svg className="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
        <circle cx="9" cy="7" r="4" />
        <path d="M23 21v-2a4 4 0 0 0-3-3.87" />
        <path d="M16 3.13a4 4 0 0 1 0 7.75" />
      </svg>
    ),
  },
  {
    href: "/cis",
    label: "Continuous Improvement",
    icon: (
      <svg className="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="12" cy="12" r="10" />
        <path d="M12 6v6l4 2" />
      </svg>
    ),
  },
];

function isActive(pathname: string, href: string): boolean {
  if (href === "/") return pathname === "/";
  return pathname === href || pathname.startsWith(href + "/");
}

export default function Sidebar() {
  const pathname = usePathname() ?? "/";
  const [sourcesOpen, setSourcesOpen] = useState(false);

  return (
    <>
      <aside className="sidebar">
        {/* Brand */}
        <div className="brand">
          <div className="brand-mark">A</div>
          <div>
            <div className="brand-name">RAGcruitment</div>
            <div className="brand-sub">recruitment analytics</div>
          </div>
        </div>

        {/* Workspace switcher */}


        {/* Nav section label */}
        <div className="nav-section">
          <div className="nav-label">Workspace</div>
          <nav className="nav">
            {NAV_ITEMS.map((item) => {
              const active = isActive(pathname, item.href);
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={active ? "active" : ""}
                >
                  {item.icon}
                  <span>{item.label}</span>
                </Link>
              );
            })}
          </nav>
        </div>

        {/* Sources button pinned to bottom */}
        <div className="sidebar-foot">
          <button
            type="button"
            className="sources-btn"
            onClick={() => setSourcesOpen(true)}
            aria-label="Browse knowledge sources"
          >
            <span>Knowledge sources</span>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
              <path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z" />
              <path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z" />
            </svg>
          </button>
        </div>
      </aside>

      <KnowledgeSourcesPanel open={sourcesOpen} onClose={() => setSourcesOpen(false)} />
    </>
  );
}
