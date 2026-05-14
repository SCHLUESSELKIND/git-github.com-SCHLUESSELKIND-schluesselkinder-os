import Image from "next/image";
import { BrandSymbol } from "../../_components/BrandSymbol";
import { SectionFrame } from "../../_components/SectionFrame";
import { SymbolRail } from "../../_components/SymbolRail";

type MetadataRow = readonly [label: string, value: string];

export type ObjectArchiveRecord = {
  archiveClass: string;
  board: {
    alt: string;
    height: number;
    src: string;
    width: number;
  };
  id: string;
  metadata: readonly MetadataRow[];
  releaseReference: string;
  status: string;
  surface: string;
  summary: readonly string[];
  title: string;
  transaction: string;
  year: string;
};

export function ObjectArchiveRecordView({ record }: { record: ObjectArchiveRecord }) {
  return (
    <main className="min-h-screen bg-[#070605] text-stone-100">
      <section className="border-b border-stone-800">
        <div className="mx-auto max-w-7xl px-5 py-10 md:px-8 md:py-14">
          <div className="grid gap-8 border-l border-stone-800 pl-5 md:grid-cols-[0.22fr_1fr_0.34fr] md:items-end md:pl-8">
            <div className="flex min-h-36 flex-col justify-between gap-8">
              <p className="text-xs font-black uppercase text-red-600">OBJECT RECORD</p>
              <div>
                <p className="break-words text-xs font-black uppercase tracking-[0.38em] text-stone-600 md:tracking-[0.45em]">{record.id}</p>
                <p className="mt-3 text-xs font-black uppercase text-stone-700">{record.archiveClass}</p>
              </div>
            </div>
            <div>
              <h1
                className="max-w-5xl break-words font-black uppercase text-stone-100"
                style={{ fontSize: "clamp(2.35rem, 7.2vw, 6.4rem)", lineHeight: 0.88, overflowWrap: "anywhere" }}
              >
                {record.title}
              </h1>
              <div className="mt-7 flex flex-wrap gap-x-6 gap-y-3 border-t border-stone-800 pt-5 text-xs font-black uppercase text-stone-500">
                {record.summary.map((item) => (
                  <p key={item}>{item}</p>
                ))}
              </div>
            </div>
            <div className="grid border-y border-stone-800 text-xs font-black uppercase text-stone-500">
              <p className="border-b border-stone-800 py-3">surface: <span className="text-stone-200">{record.surface}</span></p>
              <p className="border-b border-stone-800 py-3">status: <span className="text-stone-200">{record.status}</span></p>
              <p className="border-b border-stone-800 py-3">transaction: <span className="text-stone-200">{record.transaction}</span></p>
              <p className="border-b border-stone-800 py-3">release: <span className="text-stone-200">{record.releaseReference}</span></p>
              <p className="py-3">year: <span className="text-stone-200">{record.year}</span></p>
            </div>
          </div>
        </div>
      </section>

      <section className="border-b border-stone-800 bg-black">
        <div className="mx-auto max-w-[1680px] px-0 py-0 md:px-8 md:py-10">
          <figure className="relative bg-[#030302] md:border md:border-stone-900">
            <div className="pointer-events-none absolute inset-0 z-10 border-y border-stone-950/80 md:border-x" />
            <Image
              alt={record.board.alt}
              className="h-auto max-h-[84svh] w-full object-contain"
              height={record.board.height}
              priority
              quality={95}
              sizes="100vw"
              src={record.board.src}
              width={record.board.width}
            />
          </figure>
        </div>
      </section>

      <SymbolRail labels={[record.id, record.archiveClass, record.surface, record.status, record.year]} />

      <SectionFrame kicker="archive metadata" title="Object index.">
        <div className="border-y border-stone-800">
          {record.metadata.map(([label, value]) => (
            <div className="grid gap-3 border-b border-stone-800 py-5 transition-colors duration-300 last:border-b-0 hover:border-stone-700 hover:bg-stone-950/20 md:grid-cols-[0.28fr_1fr]" key={label}>
              <p className="text-xs font-black uppercase text-stone-500">{label}</p>
              <p className="text-base font-black uppercase leading-7 text-stone-200">{value}</p>
            </div>
          ))}
        </div>
      </SectionFrame>

      <section className="border-t border-stone-800">
        <div className="mx-auto flex max-w-7xl items-center justify-between gap-6 px-5 py-8 md:px-8">
          <p className="text-xs font-black uppercase text-stone-600">Canonical archive plate</p>
          <BrandSymbol className="h-10 w-10 text-stone-700" />
        </div>
      </section>
    </main>
  );
}
