import { SELF } from "cloudflare:test";
import { describe, it, expect } from "vitest";

describe("Hello World worker", () => {
  it("responds with not found and proper status for /404", async () => {
    const response = await SELF.fetch("http://example.com/404");
    expect(await response.status).toBe(404);
    expect(await response.text()).toBe("Not found");
  });
});
