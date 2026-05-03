"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

interface NavTab {
  href: string;
  label: string;
  icon: string;
  matchPrefixes?: string[];
}

const PRIMARY_TABS: NavTab[] = [
  { href: "/", label: "RAG Chat", icon: "💬", matchPrefixes: ["/"] },
  { href: "/candidates", label: "Candidate Search", icon: "🔍", matchPrefixes: ["/candidates"] },
  { href: "/cis", label: "Continuous Improvement Suite", icon: "🛠️", matchPrefixes: ["/cis"] },
];

const SECONDARY_LINKS: NavTab[] = [
  { href: "/dashboard", label: "Legacy dashboard", icon: "📊" },
  { href: "/system-diagram", label: "System diagram", icon: "🗺️" },
];

function isActive(pathname: string, tab: NavTab): boolean {
  if (tab.href === "/") return pathname === "/";
  if (tab.matchPrefixes) return tab.matchPrefixes.some((p) => pathname === p || pathname.startsWith(p + "/"));
  return pathname === tab.href;
}

export default function TopNav() {
  const pathname = usePathname() ?? "/";
  return (
    <nav className="bg-white shadow-sm border-b border-gray-200 sticky top-0 z-30">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16 items-center">
          <div className="flex items-center gap-8">
            <Link href="/" className="text-xl font-bold text-gray-800 tracking-tight">
              AutoCI
            </Link>
            <div className="flex items-center gap-1">
              {PRIMARY_TABS.map((tab) => {
                const active = isActive(pathname, tab);
                return (
                  <Link
                    key={tab.href}
                    href={tab.href}
                    className={[
                      "px-3 py-2 rounded-md text-sm font-medium transition-colors flex items-center gap-2",
                      active
                        ? "bg-blue-50 text-blue-700 border border-blue-200"
                        : "text-gray-600 hover:text-gray-900 hover:bg-gray-50 border border-transparent",
                    ].join(" ")}
                  >
                    <span className="text-base">{tab.icon}</span>
                    <span>{tab.label}</span>
                  </Link>
                );
              })}
            </div>
          </div>
          <div className="flex items-center gap-2">
            {SECONDARY_LINKS.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                className="text-gray-500 hover:text-gray-800 px-3 py-2 rounded-md text-xs font-medium flex items-center gap-1.5"
              >
                <span>{link.icon}</span>
                <span>{link.label}</span>
              </Link>
            ))}
          </div>
        </div>
      </div>
    </nav>
  );
}
