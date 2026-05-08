import { masterbrand, platformPlan } from "@schluesselkinder/brand";
import { SectionLabel } from "@schluesselkinder/ui";

export default function ShopPage() {
  return (
    <main className="min-h-screen bg-white text-zinc-950">
      <section className="mx-auto flex max-w-6xl flex-col gap-6 px-6 py-16 md:px-10">
        <SectionLabel>{masterbrand} Shop</SectionLabel>
        <h1 className="max-w-3xl text-4xl font-black leading-tight tracking-normal">
          Independent commerce without Shopify.
        </h1>
        <p className="max-w-2xl text-lg leading-8 text-zinc-700">
          Payments are reserved for {platformPlan.payments}; fulfillment is reserved for{" "}
          {platformPlan.fulfillment}.
        </p>
      </section>
    </main>
  );
}
