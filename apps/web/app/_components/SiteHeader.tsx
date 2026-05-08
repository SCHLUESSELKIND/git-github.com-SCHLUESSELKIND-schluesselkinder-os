import Link from "next/link";
import { masterbrand } from "@schluesselkinder/brand";

const navItems = [
  { href: "/artists", label: "Artists" },
  { href: "/music", label: "Music" },
  { href: "/shop", label: "Shop" },
  { href: "/about", label: "About" }
] as const;

export function SiteHeader() {
  return (
    <header className="sticky top-0 z-50 border-b border-stone-800 bg-black/90 backdrop-blur-sm">
      <nav className="mx-auto flex max-w-7xl items-center justify-between px-5 py-4 md:px-8">
        <Link className="text-sm font-black uppercase text-stone-100" href="/">
          {masterbrand}
        </Link>
        <div className="flex items-center gap-4 text-xs font-black uppercase text-stone-400 md:gap-7 md:text-sm">
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
