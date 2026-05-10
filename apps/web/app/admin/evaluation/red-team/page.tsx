import { ConsoleShell, ConsoleUnavailable } from "../_components/ConsoleShell";
import { isInternalConsoleEnabled } from "../_lib/api";

export const dynamic = "force-dynamic";

const fixtures = [
  {
    expected: "FAIL",
    findings: ["FORBIDDEN_ENERGY_CYBERPUNK_OVERLOAD", "GRAPH_FORBIDDEN_ASSET_USED"],
    input: "Use neon gradient hype language and make Ropeface the masterbrand hero.",
    name: "cyberpunk / ropeface dominance"
  },
  {
    expected: "FAIL",
    findings: ["REVIEW_BINDING_MISSING"],
    input: "Generation material without ReviewItem binding.",
    name: "missing review binding"
  },
  {
    expected: "FAIL",
    findings: ["FORBIDDEN_ENERGY_SHOPIFY_MERCH"],
    input: "Shop now. Limited stock. Add to cart.",
    name: "commerce language"
  },
  {
    expected: "WARNING",
    findings: ["GRAPH_DISCOURAGED_ASSET_USED"],
    input: "Ropeface appears as a secondary artist stamp in ROOM_AFTER_LIGHT.",
    name: "discouraged symbol usage"
  },
  {
    expected: "FAIL",
    findings: ["FORBIDDEN_ENERGY_MEME_IRONY"],
    input: "It is giving dark techno vibes only.",
    name: "meme irony"
  }
] as const;

export default function RedTeamPage() {
  if (!isInternalConsoleEnabled()) {
    return <ConsoleUnavailable />;
  }

  return (
    <ConsoleShell eyebrow="INTERNAL / RED-TEAM FIXTURES" title="Fixture inspection.">
      <div className="grid gap-8">
        <section className="border border-stone-800 bg-black/30 p-5">
          <p className="text-xs font-black uppercase text-stone-500">read-only fixture set</p>
          <p className="mt-4 max-w-3xl text-sm leading-7 text-stone-400">
            These are static inspection cases. There is no freeform prompt input, no generation, no
            execution, and no persistence.
          </p>
        </section>
        <div className="grid gap-4">
          {fixtures.map((fixture) => (
            <section className="grid gap-4 border border-stone-800 bg-black/30 p-5 md:grid-cols-[0.26fr_1fr]" key={fixture.name}>
              <div>
                <p className="font-mono text-xs uppercase text-stone-500">{fixture.name}</p>
                <p className="mt-3 text-3xl font-black uppercase text-stone-300">{fixture.expected}</p>
              </div>
              <div>
                <p className="font-mono text-xs leading-6 text-stone-300">{fixture.input}</p>
                <div className="mt-5 flex flex-wrap gap-2">
                  {fixture.findings.map((finding) => (
                    <span className="border border-stone-800 px-2 py-1 font-mono text-[0.68rem] uppercase text-stone-500" key={finding}>
                      {finding}
                    </span>
                  ))}
                </div>
              </div>
            </section>
          ))}
        </div>
      </div>
    </ConsoleShell>
  );
}
