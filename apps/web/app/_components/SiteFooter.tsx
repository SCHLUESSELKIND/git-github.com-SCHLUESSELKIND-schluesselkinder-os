import Link from "next/link";

const collectiveName = "SCHLUESSELKINDER";

const legalLinks = [
  { href: "/kontakt", label: "Kontakt" },
  { href: "/impressum", label: "Impressum" },
  { href: "/datenschutz", label: "Datenschutz" }
] as const;

export function SiteFooter() {
  return (
    <footer className="border-t border-stone-800 bg-[#070605] text-stone-500">
      <div className="mx-auto grid max-w-7xl gap-10 px-5 py-10 md:grid-cols-[1fr_auto] md:items-end md:px-8">
        <div>
          <p className="text-xs font-black uppercase text-stone-300">{collectiveName}</p>
          <p className="mt-3 max-w-sm text-xs uppercase leading-5 text-stone-600">
            Archive contact. Public pages remain static, manual, and controlled.
          </p>
        </div>
        <nav aria-label="Legal" className="flex flex-wrap gap-x-5 gap-y-3 text-xs font-black uppercase md:justify-end">
          {legalLinks.map((link) => (
            <Link className="transition-colors hover:text-red-700 focus-visible:outline focus-visible:outline-1 focus-visible:outline-red-900" href={link.href} key={link.href}>
              {link.label}
            </Link>
          ))}
        </nav>
      </div>
    </footer>
  );
}
