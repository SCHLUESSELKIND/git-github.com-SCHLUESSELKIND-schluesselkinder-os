import type { Metadata } from "next";
import { notFound } from "next/navigation";
import type { ReactNode } from "react";
import "@schluesselkinder/brand/soundsystem-tokens.css";
import { OperatorModeProvider } from "./_components/OperatorModeProvider";
import { isInternalConsoleEnabled } from "./_lib/operators";

export const dynamic = "force-dynamic";

export const metadata: Metadata = {
  applicationName: "SNUFFRAGA SOUNDSYSTEM",
  manifest: "/admin/soundsystem/manifest.webmanifest",
  robots: { follow: false, index: false },
  title: {
    default: "SNUFFRAGA SOUNDSYSTEM",
    template: "%s · SNUFFRAGA SOUNDSYSTEM"
  }
};

export default function SoundsystemLayout({ children }: Readonly<{ children: ReactNode }>) {
  if (!isInternalConsoleEnabled()) {
    notFound();
  }

  return <OperatorModeProvider>{children}</OperatorModeProvider>;
}
