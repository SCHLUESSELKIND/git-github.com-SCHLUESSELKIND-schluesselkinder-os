import Fastify from "fastify";
import { pathToFileURL } from "node:url";
import { loadApiEnv } from "./config/env.js";
import { createPrismaRepositories, type ApiRepositories } from "./repositories.js";
import { registerArtistRoutes } from "./routes/artists.js";
import { registerBrandIntelligenceRoutes } from "./routes/brand-intelligence.js";
import { registerContentGraphRoutes } from "./routes/content-graph.js";
import { registerFragmentRoutes } from "./routes/fragments.js";
import { registerHealthRoutes } from "./routes/health.js";
import { registerMusicRoutes } from "./routes/music.js";
import { registerObjectRoutes } from "./routes/objects.js";

type BuildServerOptions = Readonly<{
  repositories?: ApiRepositories;
}>;

export function buildServer(options: BuildServerOptions = {}) {
  const env = loadApiEnv();
  const repositories = options.repositories ?? createPrismaRepositories();
  const server = Fastify({
    logger: {
      level: env.logLevel,
      redact: [
        "req.headers.authorization",
        "req.headers.cookie",
        "req.headers['x-api-key']",
        "req.headers['x-webhook-signature']"
      ]
    }
  });

  server.setErrorHandler((error, request, reply) => {
    const apiError = error instanceof Error ? error : new Error("unknown_error");

    request.log.error(
      {
        errorName: apiError.name,
        errorMessage: redactSensitiveValues(apiError.message)
      },
      "api request failed"
    );

    return reply.code(500).send({ error: "internal_error" });
  });

  void server.register(registerHealthRoutes);
  void server.register(async (instance) => registerArtistRoutes(instance, repositories));
  void server.register(async (instance) => registerObjectRoutes(instance, repositories));
  void server.register(async (instance) => registerMusicRoutes(instance, repositories));
  void server.register(async (instance) => registerFragmentRoutes(instance, repositories));
  void server.register(async (instance) => registerBrandIntelligenceRoutes(instance, repositories));
  void server.register(async (instance) => registerContentGraphRoutes(instance, repositories));

  return server;
}

function redactSensitiveValues(message: string): string {
  let redacted = message;

  for (const [key, value] of Object.entries(process.env)) {
    if (!value || value.length < 8) {
      continue;
    }

    const normalizedKey = key.toLowerCase();
    const mayBeSensitive =
      normalizedKey.includes("secret") ||
      normalizedKey.includes("token") ||
      normalizedKey.includes("password") ||
      normalizedKey.includes("database_url") ||
      normalizedKey.includes("key");

    if (mayBeSensitive) {
      redacted = redacted.split(value).join("[redacted]");
    }
  }

  return redacted;
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
