type ManifestLineProps = Readonly<{
  de: string;
  en: string;
}>;

export function ManifestLine({ de, en }: ManifestLineProps) {
  return (
    <div className="grid gap-4 border-b border-stone-800 py-7 md:grid-cols-[0.9fr_1.1fr]">
      <p className="text-2xl font-black uppercase leading-tight text-stone-100 md:text-4xl">{de}</p>
      <p className="text-lg leading-7 text-stone-400 md:self-end">{en}</p>
    </div>
  );
}
