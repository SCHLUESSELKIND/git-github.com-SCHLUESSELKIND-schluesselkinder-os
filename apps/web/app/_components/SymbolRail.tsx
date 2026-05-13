import { BrandSymbol } from "./BrandSymbol";

type SymbolRailProps = Readonly<{
  labels?: readonly string[];
}>;

export function SymbolRail({ labels = ["KEY", "ROPE", "ROOM", "AFTER", "SK"] }: SymbolRailProps) {
  return (
    <div className="border-y border-stone-800">
      <div className="mx-auto grid max-w-7xl grid-cols-[64px_minmax(0,1fr)] items-stretch px-4 md:grid-cols-[80px_minmax(0,1fr)] md:px-8">
        <div className="flex items-center justify-center border-x border-stone-800 px-4 py-4 text-stone-500 md:px-5">
          <BrandSymbol className="h-9 w-9" />
        </div>
        <div className="overflow-x-auto">
          <div
            className="grid min-w-max text-center text-[0.68rem] font-black uppercase text-stone-600 md:min-w-0"
            style={{ gridTemplateColumns: `repeat(${labels.length}, minmax(7.5rem, 1fr))` }}
          >
            {labels.map((label) => (
              <span className="border-r border-stone-800 px-3 py-5 last:border-r-0" key={label}>
                {label}
              </span>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
