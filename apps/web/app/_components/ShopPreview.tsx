import { seedCopy } from "@schluesselkinder/brand";

export function ShopPreview() {
  return (
    <div className="grid gap-0 border-y border-stone-800 md:grid-cols-[0.85fr_1.15fr_0.7fr]">
      {seedCopy.shopPreview.map((item) => (
        <article className="min-h-72 border-b border-stone-800 p-5 md:border-b-0 md:border-r md:p-7 md:even:pt-24 md:last:border-r-0" key={item.label}>
          <p className="text-xs font-black uppercase text-red-600">object study</p>
          <h3 className="mt-20 text-4xl font-black uppercase leading-none text-stone-100 md:text-5xl">{item.label}</h3>
          <div className="mt-8 text-lg leading-7 text-stone-400">
            <p>{item.de}</p>
            <p>{item.en}</p>
          </div>
        </article>
      ))}
    </div>
  );
}
