import type { Metadata } from "next";
import { masterbrand } from "@schluesselkinder/brand";
import { EditorialHero } from "../_components/EditorialHero";
import { SectionFrame } from "../_components/SectionFrame";

const description = "Kontakt fuer SCHLUESSELKINDER.";
const previewImage = "/brand/campaign-dungeon-chair.png";
const title = `Kontakt | ${masterbrand}`;

export const metadata: Metadata = {
  alternates: {
    canonical: "/kontakt"
  },
  description,
  openGraph: {
    description,
    images: [{ alt: "SCHLUESSELKINDER dark campaign room", height: 1400, url: previewImage, width: 1400 }],
    title,
    url: "/kontakt"
  },
  title,
  twitter: {
    card: "summary_large_image",
    description,
    images: [previewImage],
    title
  }
};

export default function KontaktPage() {
  return (
    <main className="min-h-screen bg-[#070605] text-stone-100">
      <EditorialHero eyebrow="archive contact" title="Kontakt.">
        <p>SCHLUESSELKINDER.</p>
        <p>Archive contact only.</p>
      </EditorialHero>
      <SectionFrame kicker="kontakt" title="Archive line.">
        <div className="grid gap-6 border-y border-stone-800 py-8 text-sm leading-7 text-stone-400">
          <p className="text-xs font-black uppercase text-red-600">SCHLUESSELKINDER / Frerich United Ventures GmbH</p>
          <p>E-Mail: ai@tomfrerich.de</p>
          <p>Archive inquiries only. Responses are manual and may take time.</p>
          <p>Keine automatisierte Abwicklung. Keine Plattform-Kommunikation. Kein Support-Center.</p>
        </div>
      </SectionFrame>
    </main>
  );
}
