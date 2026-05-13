import Link from "next/link";
import { getStaticShopProjection } from "../../lib/registry/object-pages";

export function ShopPreview() {
  const shop = getStaticShopProjection();

  return (
    <div className="grid gap-0 border-y border-stone-800 md:grid-cols-2">
      {shop.objects.map((object) => (
        <Link
          className="group min-h-72 border-b border-stone-800 p-5 transition-colors duration-300 hover:border-red-950 hover:bg-stone-950/25 focus-visible:outline focus-visible:outline-1 focus-visible:outline-offset-4 focus-visible:outline-red-900 md:border-b-0 md:border-r md:p-7 md:even:pt-24 md:last:border-r-0"
          href={object.href}
          key={object.id}
        >
          <p className="text-xs font-black uppercase text-red-600">{object.id}</p>
          <h3 className="mt-20 text-4xl font-black uppercase leading-none text-stone-100 transition-colors duration-300 group-hover:text-stone-200 md:text-5xl">
            {object.title}
          </h3>
          <div className="mt-8 text-sm font-black uppercase leading-6 text-stone-500">
            <p>{object.archiveClass}</p>
            <p>{object.state}</p>
          </div>
        </Link>
      ))}
    </div>
  );
}
