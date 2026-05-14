import type { Metadata, Viewport } from "next";
import type { ReactNode } from "react";
import { masterbrand, seedCopy } from "@schluesselkinder/brand";
import { SiteFooter } from "./_components/SiteFooter";
import { SiteHeader } from "./_components/SiteHeader";
import "./globals.css";

const siteDescription = seedCopy.shortDescription;
const previewImage = {
  alt: "SCHLUESSELKINDER dark campaign room",
  height: 1400,
  url: "/brand/campaign-dungeon-chair.png",
  width: 1400
};

export const metadata: Metadata = {
  applicationName: masterbrand,
  authors: [{ name: masterbrand }],
  creator: masterbrand,
  description: siteDescription,
  formatDetection: {
    address: false,
    email: false,
    telephone: false
  },
  icons: {
    apple: [{ type: "image/png", url: "/brand/rune-key-mark.png" }],
    icon: [{ type: "image/png", url: "/brand/rune-key-mark.png" }]
  },
  metadataBase: new URL("https://schluesselkinder.de"),
  openGraph: {
    description: siteDescription,
    images: [previewImage],
    locale: "de_DE",
    siteName: masterbrand,
    title: masterbrand,
    type: "website",
    url: "/"
  },
  publisher: masterbrand,
  robots: {
    follow: true,
    index: true
  },
  title: masterbrand,
  twitter: {
    card: "summary_large_image",
    description: siteDescription,
    images: [previewImage.url],
    title: masterbrand
  }
};

export const viewport: Viewport = {
  colorScheme: "dark",
  themeColor: "#070605"
};

export default function RootLayout({ children }: Readonly<{ children: ReactNode }>) {
  return (
    <html lang="de">
      <body>
        <SiteHeader />
        {children}
        <SiteFooter />
      </body>
    </html>
  );
}
