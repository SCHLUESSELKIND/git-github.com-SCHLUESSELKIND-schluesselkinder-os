import { COMMAND_INTENTS, isInternalConsoleEnabled } from "../_lib/operators";

export const dynamic = "force-dynamic";

export function GET() {
  if (!isInternalConsoleEnabled()) {
    return new Response("Not found", { status: 404 });
  }

  const manifest = {
    name: "SNUFFRAGA SOUNDSYSTEM",
    short_name: "SNUFFRAGA",
    description: "Internal operator console for the SNUFFRAGA SOUNDSYSTEM AI engine.",
    start_url: "/admin/soundsystem",
    scope: "/admin/soundsystem/",
    display: "standalone",
    orientation: "portrait",
    background_color: "#000000",
    theme_color: "#000000",
    icons: [
      {
        src: "/admin/soundsystem/icon-192.png",
        sizes: "192x192",
        type: "image/png",
        purpose: "any"
      },
      {
        src: "/admin/soundsystem/icon-512.png",
        sizes: "512x512",
        type: "image/png",
        purpose: "any"
      }
    ],
    shortcuts: COMMAND_INTENTS.map((intent) => ({
      name: intent.title,
      short_name: intent.title,
      description: intent.summary,
      url: `/admin/soundsystem/${intent.slug}`
    }))
  };

  return new Response(JSON.stringify(manifest, null, 2), {
    headers: {
      "Content-Type": "application/manifest+json",
      "Cache-Control": "no-store"
    }
  });
}
