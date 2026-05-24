import Link from "next/link";
import { SoundsystemShell } from "../_components/SoundsystemShell";
import {
  getInferenceCapabilities,
  InferenceClientError,
  listLyricsProjects,
  type LyricsRepositoryMode
} from "../_lib/inference";
import { NewLyricsVersionForm } from "./_components/NewLyricsVersionForm";
import { RepositoryModeBanner } from "./_components/RepositoryModeBanner";

export const dynamic = "force-dynamic";

export default async function LyricsIndexPage() {
  let projects: Awaited<ReturnType<typeof listLyricsProjects>> = [];
  let unreachable = false;
  let repositoryMode: LyricsRepositoryMode | null = null;
  try {
    projects = await listLyricsProjects();
  } catch (error) {
    if (error instanceof InferenceClientError) {
      unreachable = true;
    } else {
      throw error;
    }
  }
  try {
    const capabilities = await getInferenceCapabilities();
    repositoryMode = capabilities.lyrics_repository_mode;
  } catch {
    // Capabilities probe failure is non-fatal; keep the warning generic.
  }

  return (
    <SoundsystemShell title="Lyrics." status="MOCK PROVIDER · LIVE">
      <RepositoryModeBanner mode={repositoryMode} />
      <div className="grid gap-10 lg:grid-cols-[1fr_1fr]">
        <section>
          <NewLyricsVersionForm />
          <p className="mt-4 font-mono text-[0.62rem] uppercase leading-5 tracking-widest text-[color:var(--ss-text-muted)]">
            Submitting creates the project on first use and starts version 1.
          </p>
        </section>
        <section>
          <header className="flex items-center justify-between border-b border-[color:var(--ss-border)] pb-3">
            <h2 className="font-mono text-[0.7rem] font-black uppercase tracking-widest text-[color:var(--ss-text-primary)]">
              PROJECTS
            </h2>
            <span className="font-mono text-[0.6rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
              {unreachable ? "INFERENCE UNREACHABLE" : `${projects.length} ENTRIES`}
            </span>
          </header>
          {unreachable ? (
            <p
              className="mt-4 border border-[color:var(--ss-warning-dim)] px-4 py-3 font-mono text-[0.7rem] uppercase tracking-widest"
              style={{ color: "var(--ss-warning)" }}
            >
              Start <code className="text-[color:var(--ss-accent)]">uvicorn app.main:app --port 8010</code>{" "}
              under <code>services/soundsystem-inference</code> to enable the lyrics console.
            </p>
          ) : projects.length === 0 ? (
            <p className="mt-6 font-mono text-[0.7rem] uppercase tracking-widest text-[color:var(--ss-text-muted)]">
              No projects yet. Submit the form to create the first one.
            </p>
          ) : (
            <ul className="mt-4 divide-y divide-[color:var(--ss-border)] border border-[color:var(--ss-border)]">
              {projects.map((project) => (
                <li key={project.id}>
                  <Link
                    href={`/admin/soundsystem/lyrics/${encodeURIComponent(project.project_key)}`}
                    className="block px-4 py-3 font-mono text-[0.72rem] uppercase tracking-widest text-[color:var(--ss-text-secondary)] hover:bg-[color:var(--ss-panel-elevated)] hover:text-[color:var(--ss-accent)] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-[-2px] focus-visible:outline-[color:var(--ss-accent)]"
                    style={{ minHeight: "var(--ss-tap-target)", backgroundColor: "var(--ss-panel)" }}
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-[color:var(--ss-text-primary)]">{project.project_key}</span>
                      <span className="text-[color:var(--ss-text-muted)]">{project.character_code}</span>
                    </div>
                    {project.title ? (
                      <div className="mt-1 text-[0.62rem] text-[color:var(--ss-text-muted)]">
                        {project.title}
                      </div>
                    ) : null}
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </section>
      </div>
    </SoundsystemShell>
  );
}

