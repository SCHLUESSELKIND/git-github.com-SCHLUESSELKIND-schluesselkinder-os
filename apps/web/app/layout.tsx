import type { Metadata } from "next";
import type { ReactNode } from "react";
import { masterbrand, seedCopy } from "@schluesselkinder/brand";
import { SiteFooter } from "./_components/SiteFooter";
import { SiteHeader } from "./_components/SiteHeader";
import "./globals.css";

const collectiveName = "SCHLUESSELKINDER";
const siteDescription = seedCopy.shortDescription;
const previewImage = {
  alt: "SCHLUESSELKINDER dark campaign room",
  height: 1400,
  url: "/brand/campaign-dungeon-chair.png",
  width: 1400
};

export const metadata: Metadata = {
  applicationName: collectiveName,
  authors: [{ name: collectiveName }],
  creator: collectiveName,
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
    siteName: collectiveName,
    title: masterbrand,
    type: "website",
    url: "/"
  },
  publisher: collectiveName,
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
