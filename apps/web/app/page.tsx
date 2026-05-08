import { firstArtist, masterbrand, platformPlan, seedCopy } from "@schluesselkinder/brand";
import { SectionLabel, TrackList } from "@schluesselkinder/ui";

export default function Home() {
  return (
    <main className="min-h-screen bg-zinc-50 text-zinc-950">
      <section className="mx-auto grid max-w-6xl gap-10 px-6 py-16 md:grid-cols-[1.2fr_0.8fr] md:px-10 md:py-24">
        <div className="flex max-w-3xl flex-col gap-8">
          <SectionLabel>{masterbrand}</SectionLabel>
          <div className="space-y-6">
            <h1 className="text-5xl font-black leading-none tracking-normal md:text-7xl">
              {firstArtist.name}
            </h1>
            <p className="max-w-2xl text-lg leading-8 text-zinc-700">
              {seedCopy.shortDescription}
            </p>
          </div>
          <div className="flex flex-wrap gap-3 text-sm font-semibold">
            <span className="border border-zinc-950 bg-zinc-950 px-4 py-2 text-white">
              No Shopify
            </span>
            <span className="border border-zinc-300 bg-white px-4 py-2 text-zinc-800">
              Stripe later
            </span>
            <span className="border border-zinc-300 bg-white px-4 py-2 text-zinc-800">
              Printful later
            </span>
          </div>
        </div>

        <aside className="border-l-4 border-red-600 bg-white p-6 shadow-sm">
          <SectionLabel>First Release Seed</SectionLabel>
          <TrackList tracks={firstArtist.tracks} />
          <dl className="mt-8 grid gap-3 text-sm">
            <div className="flex justify-between gap-4 border-t border-zinc-200 pt-3">
              <dt className="text-zinc-500">Backend</dt>
              <dd className="font-medium text-zinc-900">{platformPlan.backendHost}</dd>
            </div>
            <div className="flex justify-between gap-4 border-t border-zinc-200 pt-3">
              <dt className="text-zinc-500">DNS</dt>
              <dd className="font-medium text-zinc-900">{platformPlan.dns}</dd>
            </div>
          </dl>
        </aside>
      </section>
    </main>
  );
}
