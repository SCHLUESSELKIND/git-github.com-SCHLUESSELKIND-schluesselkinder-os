type GlyphRailProps = Readonly<{
  items?: readonly string[];
}>;

export function GlyphRail({ items = ["///", "XX", "00", "SK", "RED", "AFTER"] }: GlyphRailProps) {
  return (
    <div aria-hidden="true" className="grid grid-cols-6 border-y border-stone-800 text-center text-xs font-black uppercase text-stone-600">
      {items.map((item) => (
        <span className="border-r border-stone-800 py-3 last:border-r-0" key={item}>
          {item}
        </span>
      ))}
    </div>
  );
}
