import type { ReactNode } from "react";

type SectionFrameProps = Readonly<{
  kicker: string;
  title: string;
  children: ReactNode;
}>;

export function SectionFrame({ kicker, title, children }: SectionFrameProps) {
  return (
    <section className="border-t border-stone-800">
      <div className="mx-auto grid max-w-7xl items-start gap-10 px-5 py-14 sm:py-16 md:grid-cols-[0.42fr_1fr] md:px-8 md:py-24">
        <div>
          <p className="text-xs font-black uppercase text-red-600">{kicker}</p>
          <h2 className="mt-5 max-w-sm text-3xl font-black uppercase leading-none text-stone-100 sm:text-4xl md:mt-6 md:text-6xl">
            {title}
          </h2>
        </div>
        <div>{children}</div>
      </div>
    </section>
  );
}
