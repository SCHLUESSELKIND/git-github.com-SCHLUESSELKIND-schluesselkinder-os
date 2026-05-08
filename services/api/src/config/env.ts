export type ApiEnv = {
  host: string;
  logLevel: string;
  nodeEnv: string;
  port: number;
};

function readPort(value: string | undefined, fallback: number): number {
  if (!value) {
    return fallback;
  }

  const parsed = Number(value);

  if (!Number.isInteger(parsed) || parsed <= 0 || parsed > 65535) {
    throw new Error(`Invalid API_PORT: ${value}`);
  }

  return parsed;
}

export function loadApiEnv(env: NodeJS.ProcessEnv = process.env): ApiEnv {
  return {
    host: env.API_HOST ?? env.HOST ?? "0.0.0.0",
    logLevel: env.LOG_LEVEL ?? "info",
    nodeEnv: env.NODE_ENV ?? "development",
    port: readPort(env.API_PORT ?? env.PORT, 3001)
  };
}
