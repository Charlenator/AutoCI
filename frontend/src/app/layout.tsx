import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import Sidebar from "../components/Sidebar";
import Topbar from "../components/Topbar";
import RightDrawer from "../components/RightDrawer";
import { Analytics } from "@vercel/analytics/next";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "AutoCI — Six Sigma recruitment intelligence",
  description:
    "Three interfaces, one foundation: traceable RAG chat, semantic candidate search, and an LSS-architected Continuous Improvement Suite.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body>
        <div className="app">
          <Sidebar />
          <div className="shell">
            <Topbar />
            <div className="main-wrap">
              <main className="main">{children}</main>
              <RightDrawer />
            </div>
          </div>
        </div>
        <Analytics />
      </body>
    </html>
  );
}
