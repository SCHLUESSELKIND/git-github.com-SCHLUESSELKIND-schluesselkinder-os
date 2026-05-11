export type CatalogFetch = (input: string | URL, init?: RequestInit) => Promise<Response>;

export type CatalogClientOptions = Readonly<{
  apiBaseUrl?: string | null;
  fetcher?: CatalogFetch;
}>;

export class CatalogClientError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "CatalogClientError";
  }
}

export function resolveCatalogApiBaseUrl(options: CatalogClientOptions = {}) {
  const baseUrl = options.apiBaseUrl ?? process.env.NEXT_PUBLIC_API_URL ?? null;

  if (!baseUrl?.trim()) {
    return null;
  }

  return baseUrl.replace(/\/$/, "");
}

export function isCatalogApiConfigured(options: CatalogClientOptions = {}) {
  return resolveCatalogApiBaseUrl(options) !== null;
}

export async function readCatalogJson<T>(path: string, options: CatalogClientOptions = {}): Promise<T | null> {
  assertCatalogServerRuntime();

  const apiBaseUrl = resolveCatalogApiBaseUrl(options);

  if (!apiBaseUrl) {
    return null;
  }

  const response = await (options.fetcher ?? fetch)(`${apiBaseUrl}${path}`, {
    cache: "no-store",
    method: "GET"
  });

  if (response.status === 404) {
    return null;
  }

  if (!response.ok) {
    throw new CatalogClientError(`Catalog read failed for ${path}: ${response.status}`);
  }

  return response.json() as Promise<T>;
}

function assertCatalogServerRuntime() {
  if (typeof window !== "undefined") {
    throw new CatalogClientError("Catalog client is server-side only.");
  }
}
