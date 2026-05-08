import { BrandSymbol } from "./BrandSymbol";

type SymbolRailProps = Readonly<{
  labels?: readonly string[];
}>;

export function SymbolRail({ labels = ["KEY", "ROPE", "ROOM", "AFTER", "SK"] }: SymbolRailProps) {
  return (
    <div className="border-y border-stone-800">
      <div className="mx-auto grid max-w-7xl grid-cols-[80px_1fr] items-stretch px-5 md:px-8">
        <div className="flex items-center border-x border-stone-800 px-5 py-4 text-stone-500">
          <BrandSymbol className="h-9 w-9" />
        </div>
        <div className="grid grid-cols-5 text-center text-[0.7rem] font-black uppercase text-stone-600">
          {labels.map((label) => (
            <span className="border-r border-stone-800 py-5 last:border-r-0" key={label}>
              {label}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}
