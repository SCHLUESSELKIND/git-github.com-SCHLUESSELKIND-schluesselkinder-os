import type { ReactNode } from "react";

export function TexturePanel({ children }: Readonly<{ children: ReactNode }>) {
  return (
    <div className="texture-concrete border border-stone-800 bg-[#11100d] p-5 md:p-8">
      {children}
    </div>
  );
}
