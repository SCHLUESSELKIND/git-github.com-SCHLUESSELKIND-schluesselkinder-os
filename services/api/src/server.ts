import Fastify from "fastify";
import { pathToFileURL } from "node:url";
import { loadApiEnv } from "./config/env.js";
import { registerHealthRoutes } from "./routes/health.js";

export function buildServer() {
  const env = loadApiEnv();
  const server = Fastify({
    logger: {
      level: env.logLevel
    }
  });

  void server.register(registerHealthRoutes);

  return server;
}

async function start() {
  const env = loadApiEnv();
  const server = buildServer();

  await server.listen({ host: env.host, port: env.port });
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  start().catch((error: unknown) => {
    console.error(error);
    process.exit(1);
  });
}
