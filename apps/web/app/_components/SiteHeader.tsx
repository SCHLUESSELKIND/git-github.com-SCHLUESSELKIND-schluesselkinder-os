import Link from "next/link";
import { masterbrand } from "@schluesselkinder/brand";

const navItems = [
  { href: "/artists", label: "Artist" },
  { href: "/music", label: "Music" },
  { href: "/shop", label: "Objects" },
  { href: "/about", label: "System" }
] as const;

export function SiteHeader() {
  return (
    <header className="sticky top-0 z-50 border-b border-stone-800 bg-black/[0.88] backdrop-blur-md">
      <nav aria-label="Primary" className="mx-auto flex max-w-7xl items-center justify-between gap-3 px-4 py-3 md:gap-5 md:px-8">
        <Link className="shrink-0 text-xs font-black uppercase text-stone-100 transition-colors duration-300 hover:text-red-700 focus-visible:outline focus-visible:outline-1 focus-visible:outline-offset-4 focus-visible:outline-red-900 md:text-sm" href="/">
          {masterbrand}
        </Link>
        <div className="flex min-w-0 items-center gap-x-3 overflow-x-auto text-[0.62rem] font-black uppercase text-stone-400 sm:justify-end md:gap-x-7 md:text-sm">
          {navItems.map((item) => (
            <Link className="shrink-0 py-1 transition-colors duration-300 hover:text-red-600 focus-visible:outline focus-visible:outline-1 focus-visible:outline-offset-4 focus-visible:outline-red-900" href={item.href} key={item.href}>
              {item.label}
            </Link>
          ))}
        </div>
      </nav>
    </header>
  );
}
