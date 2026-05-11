import type { Metadata } from "next";
import { masterbrand } from "@schluesselkinder/brand";
import { EditorialHero } from "../_components/EditorialHero";
import { SectionFrame } from "../_components/SectionFrame";

export const metadata: Metadata = {
  title: `Datenschutz | ${masterbrand}`,
  description: "Datenschutzplatzhalter fuer SCHLUESSELKINDER."
};

const sections = [
  ["Verantwortliche Stelle", "[NAME / FIRMA / KONTAKT EINTRAGEN]"],
  ["Hosting", "[HOSTING-ANBIETER UND SERVERSTANDORT EINTRAGEN]"],
  ["Server-Logs", "[LOG-UMFANG UND SPEICHERDAUER EINTRAGEN]"],
  ["Kontaktaufnahme", "[E-MAIL-VERARBEITUNG UND SPEICHERDAUER EINTRAGEN]"],
  ["Analyse", "In der Öffnungsphase keine Marketing-Pixel und keine Werbeprofile."]
] as const;

export default function DatenschutzPage() {
  return (
    <main className="min-h-screen bg-[#070605] text-stone-100">
      <EditorialHero eyebrow="legal" title="Datenschutz.">
        <p>Minimal record.</p>
        <p>No marketing profile.</p>
      </EditorialHero>
      <SectionFrame kicker="datenschutz" title="Vor Veröffentlichung prüfen.">
        <div className="border-y border-stone-800">
          <p className="border-b border-stone-800 py-5 text-sm font-black uppercase text-red-600">
            Platzhalter vor Veröffentlichung ersetzen.
          </p>
          {sections.map(([label, value]) => (
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
