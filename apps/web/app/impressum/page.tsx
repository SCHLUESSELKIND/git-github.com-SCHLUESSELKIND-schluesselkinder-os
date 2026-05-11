import type { Metadata } from "next";
import { masterbrand } from "@schluesselkinder/brand";
import { EditorialHero } from "../_components/EditorialHero";
import { SectionFrame } from "../_components/SectionFrame";

export const metadata: Metadata = {
  title: `Impressum | ${masterbrand}`,
  description: "Impressumsplatzhalter fuer SCHLUESSELKINDER."
};

const rows = [
  ["Verantwortlich", "[NAME / FIRMA EINTRAGEN]"],
  ["Anschrift", "[ANSCHRIFT EINTRAGEN]"],
  ["E-Mail", "[E-MAIL-ADRESSE EINTRAGEN]"],
  ["Vertretungsberechtigte Person", "[PERSON EINTRAGEN]"],
  ["Register / Umsatzsteuer", "[FALLS ERFORDERLICH EINTRAGEN]"]
] as const;

export default function ImpressumPage() {
  return (
    <main className="min-h-screen bg-[#070605] text-stone-100">
      <EditorialHero eyebrow="legal" title="Impressum.">
        <p>Public legal record.</p>
        <p>Manual verification required.</p>
      </EditorialHero>
      <SectionFrame kicker="impressum" title="Platzhalter.">
        <div className="border-y border-stone-800">
          <p className="border-b border-stone-800 py-5 text-sm font-black uppercase text-red-600">
            Platzhalter vor Veröffentlichung ersetzen.
          </p>
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
