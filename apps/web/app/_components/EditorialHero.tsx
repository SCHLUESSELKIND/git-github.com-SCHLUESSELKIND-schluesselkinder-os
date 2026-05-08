import type { ReactNode } from "react";

type EditorialHeroProps = Readonly<{
  eyebrow: string;
  title: string;
  aside?: ReactNode;
  children?: ReactNode;
}>;

export function EditorialHero({ eyebrow, title, aside, children }: EditorialHeroProps) {
  return (
    <section className="relative mx-auto grid min-h-[calc(100vh-57px)] max-w-7xl gap-10 px-5 py-12 md:grid-cols-[1.15fr_0.85fr] md:px-8 md:py-18">
      <div className="absolute inset-x-5 top-8 h-px bg-stone-800 md:inset-x-8" />
      <div className="relative flex flex-col justify-between border-l border-stone-800 pl-5 md:pl-8">
        <p className="text-xs font-black uppercase text-red-600">{eyebrow}</p>
        <div className="py-20 md:py-28">
          <h1 className="max-w-5xl break-words text-6xl font-black uppercase leading-[0.86] text-stone-100 md:text-9xl">
            {title}
          </h1>
          {children ? <div className="mt-10 max-w-2xl text-xl leading-8 text-stone-300">{children}</div> : null}
        </div>
      </div>
      {aside ? <div className="relative self-end">{aside}</div> : null}
    </section>
  );
}
