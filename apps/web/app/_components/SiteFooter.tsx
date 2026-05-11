import Link from "next/link";
import { masterbrand } from "@schluesselkinder/brand";

const legalLinks = [
  { href: "/kontakt", label: "Kontakt" },
  { href: "/impressum", label: "Impressum" },
  { href: "/datenschutz", label: "Datenschutz" }
] as const;

const signalPlaceholders = ["TikTok", "Instagram", "SoundCloud"] as const;

export function SiteFooter() {
  return (
    <footer className="border-t border-stone-800 bg-[#070605] text-stone-500">
      <div className="mx-auto grid max-w-7xl gap-10 px-5 py-10 md:grid-cols-[1fr_auto_auto] md:px-8">
        <div>
          <p className="text-xs font-black uppercase text-stone-300">{masterbrand}</p>
          <p className="mt-3 max-w-sm text-xs uppercase leading-5 text-stone-600">
            Archive contact. External signals remain manually maintained.
          </p>
        </div>
        <nav aria-label="Legal" className="flex flex-wrap gap-x-5 gap-y-3 text-xs font-black uppercase">
          {legalLinks.map((link) => (
            <Link className="hover:text-red-700" href={link.href} key={link.href}>
              {link.label}
            </Link>
          ))}
        </nav>
        <div aria-label="External signal placeholders" className="flex flex-wrap gap-x-5 gap-y-3 text-xs font-black uppercase">
          {signalPlaceholders.map((label) => (
            <span className="text-stone-700" key={label}>
              {label}
            </span>
          ))}
        </div>
      </div>
    </footer>
  );
}
