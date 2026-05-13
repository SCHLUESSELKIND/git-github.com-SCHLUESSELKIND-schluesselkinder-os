type ManifestLineProps = Readonly<{
  de: string;
  en: string;
}>;

export function ManifestLine({ de, en }: ManifestLineProps) {
  return (
    <div className="grid gap-4 border-b border-stone-800 py-6 transition-colors hover:border-stone-700 md:grid-cols-[0.9fr_1.1fr] md:py-7">
      <p className="text-xl font-black uppercase leading-tight text-stone-100 sm:text-2xl md:text-4xl">{de}</p>
      <p className="text-base leading-7 text-stone-400 md:self-end md:text-lg">{en}</p>
    </div>
  );
}
