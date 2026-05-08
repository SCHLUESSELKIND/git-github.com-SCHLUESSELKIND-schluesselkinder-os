import Fastify from "fastify";
import { pathToFileURL } from "node:url";

export function buildServer() {
  const server = Fastify({
    logger: {
      level: process.env.LOG_LEVEL ?? "info"
    }
  });

  server.get("/health", async () => ({
    service: "api",
    status: "ok"
  }));

  return server;
}

async function start() {
  const server = buildServer();
  const port = Number(process.env.PORT ?? 3001);
  const host = process.env.HOST ?? "0.0.0.0";

  await server.listen({ host, port });
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  start().catch((error: unknown) => {
    console.error(error);
    process.exit(1);
  });
}
