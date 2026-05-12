import Link from "next/link";
import { masterbrand } from "@schluesselkinder/brand";

const navItems = [
  { href: "/artists", label: "Artist" },
  { href: "/music", label: "Sound" },
  { href: "/shop", label: "Object" },
  { href: "/about", label: "System" }
] as const;

export function SiteHeader() {
  return (
    <header className="sticky top-0 z-50 border-b border-stone-800 bg-black/90 backdrop-blur-sm">
      <nav className="mx-auto flex max-w-7xl flex-col gap-3 px-5 py-3 sm:flex-row sm:items-center sm:justify-between md:px-8">
        <Link className="text-sm font-black uppercase text-stone-100" href="/">
          {masterbrand}
        </Link>
        <div className="flex flex-wrap items-center gap-x-4 gap-y-2 text-[0.68rem] font-black uppercase text-stone-400 sm:justify-end md:gap-x-7 md:text-sm">
          {navItems.map((item) => (
            <Link className="transition-colors hover:text-red-600" href={item.href} key={item.href}>
              {item.label}
            </Link>
          ))}
        </div>
      </nav>
    </header>
  );
}
