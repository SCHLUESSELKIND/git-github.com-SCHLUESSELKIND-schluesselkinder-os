import assert from "node:assert/strict";
import { test } from "node:test";
import { buildServer } from "../server.js";

test("GET /health returns service status", async () => {
  const server = buildServer();

  const response = await server.inject({
    method: "GET",
    url: "/health"
  });

  assert.equal(response.statusCode, 200);
  assert.deepEqual(response.json(), {
    service: "api",
    status: "ok"
  });
});
