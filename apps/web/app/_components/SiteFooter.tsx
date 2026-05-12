import Link from "next/link";
import { masterbrand } from "@schluesselkinder/brand";

const legalLinks = [
  { href: "/kontakt", label: "Kontakt" },
  { href: "/impressum", label: "Impressum" },
  { href: "/datenschutz", label: "Datenschutz" }
] as const;

const externalSignals = [
  { href: "https://soundcloud.com/thomas-frerich-681624781", label: "SoundCloud" }
] as const;

export function SiteFooter() {
  return (
    <footer className="border-t border-stone-800 bg-[#070605] text-stone-500">
      <div className="mx-auto grid max-w-7xl gap-10 px-5 py-10 md:grid-cols-[1fr_auto_auto] md:px-8">
        <div>
          <p className="text-xs font-black uppercase text-stone-300">{masterbrand}</p>
          <p className="mt-3 max-w-sm text-xs uppercase leading-5 text-stone-600">
            Archive contact. External signals remain manual.
          </p>
        </div>
        <nav aria-label="Legal" className="flex flex-wrap gap-x-5 gap-y-3 text-xs font-black uppercase">
          {legalLinks.map((link) => (
            <Link className="hover:text-red-700" href={link.href} key={link.href}>
              {link.label}
            </Link>
          ))}
        </nav>
        <div aria-label="External signals" className="flex flex-wrap gap-x-5 gap-y-3 text-xs font-black uppercase">
          {externalSignals.map((signal) => (
            <a className="text-stone-700 hover:text-red-700" href={signal.href} key={signal.href} rel="noreferrer" target="_blank">
              {signal.label}
            </a>
          ))}
        </div>
      </div>
    </footer>
  );
}
