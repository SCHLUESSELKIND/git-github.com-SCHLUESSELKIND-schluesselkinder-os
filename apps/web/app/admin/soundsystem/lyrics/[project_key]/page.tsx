import Link from "next/link";
import { notFound } from "next/navigation";
import { SoundsystemShell } from "../../_components/SoundsystemShell";
import {
  InferenceClientError,
  getLyricsProject,
  listLyricsVersions
} from "../../_lib/inference";
import { NewLyricsVersionForm } from "../_components/NewLyricsVersionForm";

export const dynamic = "force-dynamic";

type Props = Readonly<{
  params: Promise<{ project_key: string }>;
}>;

export default async function LyricsProjectPage({ params }: Props) {
  const { project_key } = await params;

  try {
    const [project, versions] = await Promise.all([
      getLyricsProject(project_key),
      listLyricsVersions(project_key)
    ]);

    return (
      <SoundsystemShell title={`Project · ${project.project_key}`} status="MOCK PROVIDER · LIVE">
        <div className="grid gap-10 lg:grid-cols-[1fr_1fr]">
          <section>
            <header className="mb-4 grid gap-1">
              <p className="font-mono text-[0.62rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
                PROJECT
              </p>
              <h2 className="font-mono text-lg uppercase text-[color:var(--ss-text-primary)]">
                {project.project_key}
              </h2>
              <p className="font-mono text-[0.62rem] uppercase tracking-widest text-[color:var(--ss-text-secondary)]">
                CHARACTER · {project.character_code}
              </p>
              {project.title ? (
                <p className="font-mono text-[0.62rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
                  {project.title}
                </p>
              ) : null}
            </header>
            <NewLyricsVersionForm
              defaultProjectKey={project.project_key}
              projectKeyLocked
            />
            <p className="mt-4 font-mono text-[0.62rem] uppercase leading-5 tracking-widest text-[color:var(--ss-text-muted)]">
              Submitting a new brief appends another version to this project.
            </p>
          </section>
          <section>
            <header className="flex items-center justify-between border-b border-[color:var(--ss-border)] pb-3">
              <h2 className="font-mono text-[0.7rem] font-black uppercase tracking-widest text-[color:var(--ss-text-primary)]">
                VERSIONS
              </h2>
              <span className="font-mono text-[0.6rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
                {versions.length} ENTRIES
              </span>
            </header>
            {versions.length === 0 ? (
              <p className="mt-4 font-mono text-[0.7rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
                No versions yet.
              </p>
            ) : (
              <ul className="mt-4 divide-y divide-[color:var(--ss-border)] border border-[color:var(--ss-border)]">
                {versions
                  .slice()
                  .reverse()
                  .map((version) => (
                    <li key={version.id}>
                      <Link
                        href={`/admin/soundsystem/lyrics/${encodeURIComponent(project.project_key)}/${version.version}`}
                        className="block px-4 py-3 font-mono text-[0.72rem] uppercase tracking-widest text-[color:var(--ss-text-secondary)] hover:bg-[color:var(--ss-panel-elevated)] hover:text-[color:var(--ss-accent)] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-[-2px] focus-visible:outline-[color:var(--ss-accent)]"
                        style={{ minHeight: "var(--ss-tap-target)", backgroundColor: "var(--ss-panel)" }}
                      >
                        <div className="flex items-center justify-between">
                          <span className="text-[color:var(--ss-text-primary)]">v{version.version}</span>
                          <span className="text-[color:var(--ss-text-muted)]">
                            {version.structure.sections.length} sections
                          </span>
                        </div>
                        <div className="mt-1 text-[0.62rem] leading-5 text-[color:var(--ss-text-muted)]">
                          {version.edit_summary ?? "initial generation"}
                        </div>
                      </Link>
                    </li>
                  ))}
              </ul>
            )}
            <p className="mt-4 font-mono text-[0.62rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
              ← <Link className="hover:text-[color:var(--ss-accent)]" href="/admin/soundsystem/lyrics">
                lyrics index
              </Link>
            </p>
          </section>
        </div>
      </SoundsystemShell>
    );
  } catch (error) {
    if (error instanceof InferenceClientError && error.status === 404) {
      notFound();
    }
    throw error;
  }
}
