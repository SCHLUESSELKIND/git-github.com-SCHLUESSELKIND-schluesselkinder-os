import type { Metadata } from "next";
import Link from "next/link";
import type { ReactNode } from "react";
import { masterbrand, seedCopy } from "@schluesselkinder/brand";
import "./globals.css";

export const metadata: Metadata = {
  title: masterbrand,
  description: seedCopy.shortDescription
};

export default function RootLayout({ children }: Readonly<{ children: ReactNode }>) {
  return (
    <html lang="en">
      <body>
        <header className="border-b border-zinc-200 bg-white">
          <nav className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
            <Link className="text-sm font-bold tracking-normal text-zinc-950" href="/">
              {masterbrand}
            </Link>
            <div className="flex items-center gap-5 text-sm font-medium text-zinc-700">
              <Link className="hover:text-zinc-950" href="/shop">
                Shop
              </Link>
              <Link className="hover:text-zinc-950" href="/admin">
                Admin
              </Link>
            </div>
          </nav>
        </header>
        {children}
      </body>
    </html>
  );
}
