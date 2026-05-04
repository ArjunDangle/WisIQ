import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { HealthDot } from "@/components/ui/HealthDot";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "WisIQ | Enterprise Hardware Assistant",
  description: "Enterprise hardware AI assistant by WisIQ",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="antialiased">
      <body
        className={`${geistSans.variable} ${geistMono.variable} font-sans min-h-screen bg-background text-foreground flex flex-col`}
      >
        <header className="fixed top-0 left-0 right-0 h-14 flex items-center px-6 z-50 glass">
          <div className="flex items-center gap-2 font-medium tracking-wide text-sm">
            <span>WisIQ</span>
          </div>
          <div className="ml-auto flex items-center gap-3">
            <span className="text-[10px] uppercase tracking-widest text-muted-foreground font-semibold">
              System Status
            </span>
            <HealthDot />
          </div>
        </header>
        <main className="flex-1 flex flex-col mt-14 h-[calc(100vh-3.5rem)]">
          {children}
        </main>
      </body>
    </html>
  );
}
