import Link from "next/link";
import { BoundaryStatus } from "./_components/BoundaryStatus";
import { ConsoleReadError, ConsoleShell, ConsoleUnavailable } from "./_components/ConsoleShell";
import { RawJsonBlock } from "./_components/ReportPanels";
import {
  fetchEvaluationHealth,
  fetchGenerationSummary,
  isInternalConsoleEnabled
} from "./_lib/api";

export const dynamic = "force-dynamic";

export default async function EvaluationIndexPage() {
  if (!isInternalConsoleEnabled()) {
    return <ConsoleUnavailable />;
  }

  try {
    const [health, generation] = await Promise.all([
      fetchEvaluationHealth(),
      fetchGenerationSummary()
    ]);

    return (
      <ConsoleShell title="Evaluation inspection.">
        <div className="grid gap-8">
          <BoundaryStatus health={health} />
          <section className="grid gap-6 md:grid-cols-3">
            <IndexPanel
              items={generation.outputs.map((output) => ({
                href: `/admin/evaluation/outputs/${output.outputKey}`,
                meta: output.status,
                title: output.outputKey
              }))}
              title="outputs"
            />
            <IndexPanel
              items={generation.briefs.map((brief) => ({
                href: `/admin/evaluation/briefs/${brief.briefKey}`,
                meta: brief.type,
                title: brief.briefKey
              }))}
              title="briefs"
            />
            <IndexPanel
              items={generation.constraintBundles.map((bundle) => ({
                href: `/admin/evaluation/constraints/${bundle.code}`,
                meta: `${bundle.constraints.length} constraints`,
                title: bundle.code
              }))}
              title="constraints"
            />
          </section>
          <section className="grid gap-4 border border-stone-800 bg-black/30 p-5 md:grid-cols-[0.34fr_1fr]">
            <div>
              <p className="text-xs font-black uppercase text-stone-500">red-team fixtures</p>
              <Link className="mt-4 inline-block text-xs font-black uppercase text-red-700 hover:text-red-500" href="/admin/evaluation/red-team">
                inspect fixtures
              </Link>
            </div>
            <p className="max-w-3xl text-sm leading-7 text-stone-400">
              Fixture inspection is static and read-only. It is used to verify that forbidden energy,
              graph violations, and review-binding failures remain visible.
            </p>
          </section>
          <RawJsonBlock data={{ health, generation }} />
        </div>
      </ConsoleShell>
    );
  } catch (error) {
    return <ConsoleReadError message={error instanceof Error ? error.message : "unknown read failure"} />;
  }
}

type IndexPanelProps = Readonly<{
  items: Array<{
    href: string;
    meta: string;
    title: string;
  }>;
  title: string;
}>;

function IndexPanel({ items, title }: IndexPanelProps) {
  return (
    <section className="border border-stone-800 bg-black/30">
      <div className="border-b border-stone-800 px-4 py-3 text-xs font-black uppercase text-stone-500">
        {title}
      </div>
      <div className="divide-y divide-stone-900">
        {items.map((item) => (
          <Link className="block p-4 hover:bg-stone-950" href={item.href} key={item.href}>
            <p className="break-words font-mono text-xs uppercase text-stone-300">{item.title}</p>
            <p className="mt-2 font-mono text-[0.68rem] uppercase text-stone-600">{item.meta}</p>
          </Link>
        ))}
      </div>
    </section>
  );
}
