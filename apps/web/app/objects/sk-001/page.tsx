import type { Metadata } from "next";
import { masterbrand } from "@schluesselkinder/brand";
import { BrandSymbol } from "../../_components/BrandSymbol";
import { SectionFrame } from "../../_components/SectionFrame";
import { SymbolRail } from "../../_components/SymbolRail";

export const metadata: Metadata = {
  title: `SK-001 BLACK HOODIE / KEY | ${masterbrand}`,
  description: "SCHLUESSELKINDER object archive record SK-001."
};

const metadataRows = [
  ["record", "SK-001"],
  ["object", "BLACK HOODIE / KEY"],
  ["object type", "HOODIE"],
  ["mark", "KEY"],
  ["surface", "BLACK-ON-BLACK"],
  ["status", "ARCHIVED SIGNAL"],
  ["transaction", "CLOSED"],
  ["archive class", "SK-CORE"]
] as const;

const recordMeta = [
  "OBJECT RECORD",
  "SK-001",
  "ACTIVE ARCHIVE",
  "2026"
] as const;

const objectImages = {
  front: "/objects/sk-001/front.png",
  back: "/objects/sk-001/back.png",
  left: "/objects/sk-001/left.png",
  right: "/objects/sk-001/right.png"
} as const;

export default function Sk001Page() {
  return (
    <main className="min-h-screen bg-[#070605] text-stone-100">
      <section className="border-b border-stone-800">
        <div className="mx-auto grid min-h-[calc(100vh-57px)] max-w-7xl gap-8 px-5 py-10 md:grid-cols-[0.86fr_1.14fr] md:px-8 md:py-14">
          <div className="flex flex-col justify-between border-l border-stone-800 pl-5 md:pl-8">
            <div className="grid grid-cols-2 gap-x-6 gap-y-3 text-xs font-black uppercase text-stone-500 md:grid-cols-4">
              {recordMeta.map((item) => (
                <p className={item === "OBJECT RECORD" ? "text-red-600" : ""} key={item}>
                  {item}
                </p>
              ))}
            </div>
            <div className="flex items-start justify-between gap-8 py-16 md:py-0">
              <div>
                <p className="text-xs font-black uppercase tracking-[0.45em] text-stone-600">Specimen plate</p>
                <h1
                  className="mt-8 max-w-5xl break-words font-black uppercase text-stone-100"
                  style={{ fontSize: "clamp(2.55rem, 10.5vw, 8.75rem)", lineHeight: 0.84, overflowWrap: "anywhere" }}
                >
                  <span className="block">BLACK</span>
                  <span className="block">HOODIE</span>
                  <span className="block">/ KEY</span>
                </h1>
                <div className="mt-8 max-w-xl text-xl leading-8 text-stone-300">
                  <p>Black-on-black.</p>
                  <p>Key mark. Cotton study.</p>
                </div>
              </div>
              <BrandSymbol className="h-14 w-14 text-stone-100/70" />
            </div>
            <div className="grid gap-0 border-y border-stone-800 text-xs font-black uppercase text-stone-500 md:grid-cols-3">
              <p className="border-b border-stone-800 py-4 md:border-b-0 md:border-r">mark: key</p>
              <p className="border-b border-stone-800 py-4 md:border-b-0 md:border-r">surface: black</p>
              <p className="py-4">transaction: closed</p>
            </div>
          </div>
          <ObjectPlate
            alt="SK-001 black hoodie front view with black-on-black key mark"
            caption="front view / black-on-black mark"
            className="min-h-[620px] md:min-h-[760px]"
            imageClassName="scale-[1.05] opacity-90"
            priority
            src={objectImages.front}
          />
        </div>
      </section>
      <SymbolRail labels={["SK-001", "ACTIVE ARCHIVE", "KEY", "BLACK-ON-BLACK", "SK-CORE"]} />
      <SectionFrame kicker="specimen plates" title="Object evidence.">
        <div className="grid gap-6 md:grid-cols-[1fr_0.72fr]">
          <ObjectPlate
            alt="SK-001 black hoodie side view with sleeve mark"
            caption="sleeve surface / hidden text mark"
            className="min-h-[560px] md:min-h-[680px]"
            imageClassName="scale-[1.42] object-[54%_72%] opacity-85"
            src={objectImages.left}
          />
          <div className="grid gap-6">
            <ObjectPlate
              alt="SK-001 black hoodie back silhouette"
              caption="back silhouette"
              className="min-h-[310px] md:min-h-[330px]"
              imageClassName="scale-[1.12] opacity-65"
              src={objectImages.back}
            />
            <ObjectPlate
              alt="SK-001 black hoodie right side profile"
              caption="side profile / mass"
              className="min-h-[310px] md:min-h-[330px]"
              imageClassName="scale-[1.36] object-[50%_62%] opacity-75"
              src={objectImages.right}
            />
          </div>
        </div>
      </SectionFrame>
      <SectionFrame kicker="archive metadata" title="Specimen index.">
        <div className="border-y border-stone-800">
          {metadataRows.map(([label, value]) => (
            <div className="grid gap-3 border-b border-stone-800 py-5 last:border-b-0 md:grid-cols-[0.35fr_1fr]" key={label}>
              <p className="text-xs font-black uppercase text-stone-500">{label}</p>
              <p className="text-sm font-black uppercase leading-7 text-stone-200">{value}</p>
            </div>
          ))}
        </div>
      </SectionFrame>
      <SectionFrame kicker="object state" title="Closed record.">
        <div className="grid gap-6 border-y border-stone-800 py-8 md:grid-cols-[0.35fr_1fr]">
          <p className="text-xs font-black uppercase text-stone-500">public state</p>
          <p className="max-w-2xl text-xl font-black uppercase leading-8 text-stone-200">
            Dieses Objekt ist als Evidenz im SCHLUESSELKINDER Archiv registriert.
          </p>
        </div>
      </SectionFrame>
    </main>
  );
}

type ObjectPlateProps = {
  alt: string;
  caption: string;
  className?: string;
  imageClassName?: string;
  priority?: boolean;
  src: string;
};

function ObjectPlate({ alt, caption, className = "", imageClassName = "", priority = false, src }: ObjectPlateProps) {
  return (
    <figure className={`relative min-w-0 overflow-hidden border border-stone-800 bg-black ${className}`}>
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_26%,rgba(120,120,110,0.16),rgba(0,0,0,0)_48%)]" />
      <img
        alt={alt}
        className={`relative z-10 h-full w-full object-contain brightness-[0.78] contrast-[1.08] saturate-0 ${imageClassName}`}
        decoding="async"
        fetchPriority={priority ? "high" : "auto"}
        loading={priority ? "eager" : "lazy"}
        src={src}
      />
      <div className="pointer-events-none absolute inset-0 bg-black/20" />
      <figcaption className="absolute bottom-4 left-4 z-20 max-w-[calc(100%-2rem)] text-[0.62rem] font-black uppercase leading-4 text-stone-600">
        {caption}
      </figcaption>
    </figure>
  );
}
