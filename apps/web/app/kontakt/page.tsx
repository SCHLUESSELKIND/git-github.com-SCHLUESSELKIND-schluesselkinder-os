import type { Metadata } from "next";
import { masterbrand } from "@schluesselkinder/brand";
import { EditorialHero } from "../_components/EditorialHero";
import { SectionFrame } from "../_components/SectionFrame";

export const metadata: Metadata = {
  title: `Kontakt | ${masterbrand}`,
  description: "Kontaktplatzhalter fuer SCHLUESSELKINDER."
};

export default function KontaktPage() {
  return (
    <main className="min-h-screen bg-[#070605] text-stone-100">
      <EditorialHero eyebrow="legal / contact" title="Kontakt.">
        <p>Archive contact.</p>
        <p>Manual path only.</p>
      </EditorialHero>
      <SectionFrame kicker="kontakt" title="Manuell ersetzen.">
        <div className="grid gap-6 border-y border-stone-800 py-8 text-sm leading-7 text-stone-400">
          <p className="font-black uppercase text-red-600">Platzhalter vor Veröffentlichung ersetzen.</p>
          <p>E-Mail: [E-MAIL-ADRESSE EINTRAGEN]</p>
          <p>Verantwortliche Person / Stelle: [NAME / FIRMA EINTRAGEN]</p>
          <p>Object archive inquiries: manual inquiry only.</p>
          <p>Keine automatisierte Abwicklung. Keine Plattform-Kommunikation.</p>
        </div>
      </SectionFrame>
    </main>
  );
}
