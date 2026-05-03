import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import TopNav from "../components/TopNav";
import RightDrawer from "../components/RightDrawer";

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
      <body className="h-full flex flex-col bg-gray-50 text-gray-900">
        <TopNav />
        <div className="flex flex-1 min-h-0">
          <main className="flex-1 min-w-0 min-h-0 overflow-hidden">{children}</main>
          <RightDrawer />
        </div>
      </body>
    </html>
  );
}
