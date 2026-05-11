import { notFound } from "next/navigation";
import type { ReactNode } from "react";

const internalConsoleEnabled = process.env.NEXT_PUBLIC_INTERNAL_CONSOLE_ENABLED === "true";

export const dynamic = "force-dynamic";

export default function AdminLayout({
  children
}: Readonly<{
  children: ReactNode;
}>) {
  if (!internalConsoleEnabled) {
    notFound();
  }

  return children;
}
