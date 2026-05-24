import Link from "next/link";
import { SoundsystemShell } from "../../_components/SoundsystemShell";
import { getReleasePack, InferenceClientError } from "../../_lib/inference";
import type { ReleasePack } from "../../_lib/inference-types";
import { ReleaseDetailView } from "./_components/ReleaseDetailView";

export const dynamic = "force-dynamic";

type Props = {
  params: Promise<{ release_id: string }>;
};

/**
 * Release Detail — inspect and manage a single release pack (S24).
 *
 * Server-rendered page that loads the release, then hands off to a
 * client component for interactive checklist editing and ready marking.
 */
export default async function ReleaseDetailPage({ params }: Props) {
  const { release_id } = await params;
  let release: ReleasePack | null = null;
  let errorMessage: string | null = null;

  try {
    release = await getReleasePack(release_id);
  } catch (error) {
    if (error instanceof InferenceClientError) {
      errorMessage =
        error.status === 404
          ? "Release pack not found."
          : `Inference error: ${error.message}`;
    } else {
      throw error;
    }
  }

  if (errorMessage || !release) {
    return (
      <SoundsystemShell title="Not found." status="RELEASE CENTER">
        <p
          className="border border-[color:var(--ss-warning-dim)] px-4 py-3 font-mono text-[0.7rem] uppercase tracking-widest"
          style={{ color: "var(--ss-warning)" }}
        >
          {errorMessage || "Release pack not found."}
        </p>
        <Link
          href="/admin/soundsystem/releases"
          className="mt-4 inline-block font-mono text-[0.7rem] uppercase tracking-widest text-[color:var(--ss-accent)] hover:underline"
        >
          ← Back to Releases
        </Link>
      </SoundsystemShell>
    );
  }

  return (
    <SoundsystemShell title={release.title} status="RELEASE DETAIL">
      {/* Back link */}
      <Link
        href="/admin/soundsystem/releases"
        className="mb-6 inline-block font-mono text-[0.65rem] uppercase tracking-widest text-[color:var(--ss-accent)] hover:underline"
      >
        ← Releases
      </Link>

      <ReleaseDetailView initialRelease={release} />
    </SoundsystemShell>
  );
}
