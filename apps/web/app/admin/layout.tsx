import type { Metadata } from "next";
import { notFound } from "next/navigation";
import type { ReactNode } from "react";
import "@schluesselkinder/brand/soundsystem-tokens.css";
import { isInternalConsoleEnabled } from "./_lib/admin-gate";

export const dynamic = "force-dynamic";

export const metadata: Metadata = {
  applicationName: "SCHLUESSELKINDER · ADMIN",
  robots: {
    index: false,
    follow: false,
    noarchive: true,
    nocache: true,
    nosnippet: true
  },
  title: {
    default: "SCHLUESSELKINDER · ADMIN",
    template: "%s · ADMIN"
  }
};

export default function AdminLayout({
  children
}: Readonly<{
  children: ReactNode;
}>) {
  // Middleware is the primary gate; this in-route check is defense-in-depth
  // for build-time renders that bypass middleware (e.g. error pages).
  if (!isInternalConsoleEnabled()) {
    notFound();
  }
  return children;
}
