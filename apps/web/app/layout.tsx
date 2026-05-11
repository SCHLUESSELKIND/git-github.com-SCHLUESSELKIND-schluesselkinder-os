import type { Metadata } from "next";
import type { ReactNode } from "react";
import { masterbrand, seedCopy } from "@schluesselkinder/brand";
import { SiteFooter } from "./_components/SiteFooter";
import { SiteHeader } from "./_components/SiteHeader";
import "./globals.css";

export const metadata: Metadata = {
  title: masterbrand,
  description: seedCopy.shortDescription
};

export default function RootLayout({ children }: Readonly<{ children: ReactNode }>) {
  return (
    <html lang="en">
      <body>
        <SiteHeader />
        {children}
        <SiteFooter />
      </body>
    </html>
  );
}
