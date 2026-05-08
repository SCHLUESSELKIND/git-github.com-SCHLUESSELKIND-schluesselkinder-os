import type { ReactNode } from "react";

type RotatedMetaProps = Readonly<{
  children: ReactNode;
}>;

export function RotatedMeta({ children }: RotatedMetaProps) {
  return (
    <p className="hidden origin-bottom-left -rotate-90 text-xs font-black uppercase text-stone-500 md:block">
      {children}
    </p>
  );
}
