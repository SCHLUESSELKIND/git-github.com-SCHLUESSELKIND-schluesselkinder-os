import type { Metadata } from "next";
import { masterbrand } from "@schluesselkinder/brand";
import { EditorialHero } from "../_components/EditorialHero";
import { SectionFrame } from "../_components/SectionFrame";

const description = "Datenschutzhinweise fuer SCHLUESSELKINDER.";
const previewImage = "/brand/campaign-dungeon-chair.png";
const title = `Datenschutz | ${masterbrand}`;

export const metadata: Metadata = {
  alternates: {
    canonical: "/datenschutz"
  },
  description,
  openGraph: {
    description,
    images: [{ alt: "SCHLUESSELKINDER dark campaign room", height: 1400, url: previewImage, width: 1400 }],
    title,
    url: "/datenschutz"
  },
  title,
  twitter: {
    card: "summary_large_image",
    description,
    images: [previewImage],
    title
  }
};

const sections = [
  ["Verantwortliche Stelle", "Frerich United Ventures GmbH, SCHLUESSELKINDER, An der Ronne 48, 50859 Koeln. Kontakt: ai@tomfrerich.de."],
  ["Hosting", "Hosting-Anbieter: Hetzner Online GmbH. Serverstandort: Deutschland / Europaeische Union."],
  ["Server-Logs", "Server-Logs koennen IP-Adresse, Zeitpunkt, angefragte URL, Referrer, User-Agent und technischen Status enthalten. Die Verarbeitung dient Stabilitaet, Sicherheit und Fehleranalyse. Speicherdauer: in der Regel bis zu 14 Tage, sofern kein Sicherheitsvorfall eine laengere Aufbewahrung erfordert."],
  ["Kontaktaufnahme", "Wenn per E-Mail Kontakt aufgenommen wird, werden die uebermittelten Angaben zur Bearbeitung der Anfrage verarbeitet. Die Kommunikation bleibt manuell. Daten werden nach Abschluss der Anfrage geloescht, sofern keine gesetzlichen Aufbewahrungspflichten entgegenstehen."],
  ["Technische Daten", "Es werden nur technische Daten verarbeitet, die fuer Betrieb, Sicherheit und Auslieferung der Website erforderlich sind."],
  ["Keine Marketing-Systeme", "In der Oeffnungsphase gibt es kein Marketing-Tracking, kein Retargeting, keine Werbeprofile und keine Advertising-Optimierungssysteme."],
  ["Keine Profilbildung", "Es gibt keine automatisierte Profilbildung, keine automatisierten Entscheidungen und keine verhaltensbasierte Optimierung."]
] as const;

export default function DatenschutzPage() {
  return (
    <main className="min-h-screen bg-[#070605] text-stone-100">
      <EditorialHero eyebrow="legal" title="Datenschutz.">
        <p>Minimal record.</p>
        <p>No marketing tracking.</p>
      </EditorialHero>
      <SectionFrame kicker="datenschutz" title="Technical only.">
        <div className="border-y border-stone-800">
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
