import { notFound } from "next/navigation";
import { SoundsystemShell } from "../../../_components/SoundsystemShell";
import {
  InferenceClientError,
  getInferenceCapabilities,
  getLyricsVersionByNumber,
  listLyricsVersions,
  type LyricsRepositoryMode
} from "../../../_lib/inference";
import { RepositoryModeBanner } from "../../_components/RepositoryModeBanner";
import { LyricsEditor } from "./_components/LyricsEditor";

export const dynamic = "force-dynamic";

type Props = Readonly<{
  params: Promise<{ project_key: string; version_id: string }>;
}>;

export default async function LyricsVersionPage({ params }: Props) {
  const { project_key, version_id } = await params;
  const versionNumber = Number.parseInt(version_id, 10);
  if (!Number.isFinite(versionNumber) || versionNumber < 1) {
    notFound();
  }

  try {
    const [version, allVersions] = await Promise.all([
      getLyricsVersionByNumber(project_key, versionNumber),
      listLyricsVersions(project_key)
    ]);

    let repositoryMode: LyricsRepositoryMode | null = null;
    try {
      const capabilities = await getInferenceCapabilities();
      repositoryMode = capabilities.lyrics_repository_mode;
    } catch {
      // Capabilities probe failure is non-fatal; banner falls back to session-scoped.
    }

    return (
      <SoundsystemShell
        title={`${project_key} · v${version.version}`}
        status="MOCK PROVIDER · LIVE"
      >
        <RepositoryModeBanner mode={repositoryMode} />
        <LyricsEditor
          projectKey={project_key}
          version={version}
          allVersions={allVersions}
        />
      </SoundsystemShell>
    );
  } catch (error) {
    if (error instanceof InferenceClientError && error.status === 404) {
      notFound();
    }
    throw error;
  }
}
