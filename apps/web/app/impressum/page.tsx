import type { Metadata } from "next";
import { masterbrand } from "@schluesselkinder/brand";
import { EditorialHero } from "../_components/EditorialHero";
import { SectionFrame } from "../_components/SectionFrame";

const description = "Impressum fuer SCHLUESSELKINDER.";
const previewImage = "/brand/campaign-dungeon-chair.png";
const title = `Impressum | ${masterbrand}`;

export const metadata: Metadata = {
  alternates: {
    canonical: "/impressum"
  },
  description,
  openGraph: {
    description,
    images: [{ alt: "SCHLUESSELKINDER dark campaign room", height: 1400, url: previewImage, width: 1400 }],
    title,
    url: "/impressum"
  },
  title,
  twitter: {
    card: "summary_large_image",
    description,
    images: [previewImage],
    title
  }
};

const rows = [
  ["Anbieter", "Frerich United Ventures GmbH"],
  ["Marke", "SCHLUESSELKINDER"],
  ["Anschrift", "An der Ronne 48, 50859 Koeln"],
  ["Telefon", "016094642266"],
  ["E-Mail", "ai@tomfrerich.de"],
  ["Vertreten durch", "Geschaeftsfuehrer Thomas Frerich"],
  ["Handelsregister", "Amtsgericht Koeln, HRB 112376"],
  ["Umsatzsteuer-ID", "DE 356752511"]
] as const;

export default function ImpressumPage() {
  return (
    <main className="min-h-screen bg-[#070605] text-stone-100">
      <EditorialHero eyebrow="legal" title="Impressum.">
        <p>Angaben gemaess § 5 TMG.</p>
        <p>Operator record.</p>
      </EditorialHero>
      <SectionFrame kicker="impressum" title="Frerich United Ventures GmbH.">
        <div className="border-y border-stone-800">
          {rows.map(([label, value]) => (
            <div className="grid gap-3 border-b border-stone-800 py-5 last:border-b-0 md:grid-cols-[0.35fr_1fr]" key={label}>
              <p className="text-xs font-black uppercase text-stone-500">{label}</p>
              <p className="text-sm leading-7 text-stone-300">{value}</p>
            </div>
          ))}
        </div>
      </SectionFrame>
    </main>
  );
}
