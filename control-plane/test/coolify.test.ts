import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { CoolifyApiProvider } from "../src/providers/coolify.js";
import type { AppConfig } from "../src/config.js";
import type { SiteRecord } from "../src/types.js";

const site: SiteRecord = {
  id: "site_test",
  teamId: "team_test",
  ownerUid: "owner_test",
  name: "Test WordPress",
  slug: "test-wordpress",
  plan: "paid",
  status: "configured",
  type: "wordpress",
  primaryDomain: "test-wordpress.getaudo.com",
  domains: [],
  builder: { version: 1, components: [] },
  wordpress: {
    siteTitle: "Test WordPress",
    ownerEmail: "owner@example.com",
    adminEmail: "owner@example.com",
    themeSlug: "audo-studio"
  },
  github: { connected: false },
  deployments: [],
  backups: [],
  createdAt: new Date().toISOString(),
  updatedAt: new Date().toISOString()
};

describe("Coolify WordPress provisioning", () => {
  it("creates a WordPress service from the configured Coolify template", async () => {
    const requests: Array<{ url: string; method?: string; body: any }> = [];
    const originalFetch = global.fetch;
    global.fetch = (async (url: string | URL | Request, init?: RequestInit) => {
      requests.push({ url: String(url), method: init?.method, body: JSON.parse(String(init?.body || "{}")) });
      if (String(url).endsWith("/start")) {
        return new Response(JSON.stringify({ message: "Service starting request queued." }), { status: 200 });
      }
      if (String(url).endsWith("/envs/bulk")) {
        return new Response(JSON.stringify({ message: "Environment variables updated." }), { status: 200 });
      }
      return new Response(JSON.stringify({ uuid: "service_test", domains: ["https://test-wordpress.getaudo.com"] }), { status: 201 });
    }) as typeof fetch;

    try {
      const coolify = new CoolifyApiProvider({
        baseUrl: "http://coolify:8080",
        apiToken: "token_test",
        wordpressServiceType: "wordpress-with-mariadb",
        wordpressProjectUuid: "project_test",
        wordpressEnvironmentName: "production",
        wordpressServerUuid: "server_test",
        wordpressDestinationUuid: "destination_test",
        wordpressInstantDeploy: true
      } satisfies AppConfig["coolify"]);
      const deployment = await coolify.provisionWordPressSite(site);

      assert.equal(deployment.id, "service_test");
      assert.equal(deployment.provider, "coolify");
      assert.equal(deployment.status, "queued");
      assert.equal(requests[0].url, "http://coolify:8080/api/v1/services");
      assert.deepEqual(requests[0].body, {
        type: "wordpress-with-mariadb",
        name: "audo-test-wordpress-wordpress",
        description: "Audo managed WordPress site for test-wordpress.getaudo.com",
        project_uuid: "project_test",
        server_uuid: "server_test",
        destination_uuid: "destination_test",
        instant_deploy: false,
        urls: [{ name: "wordpress", url: "https://test-wordpress.getaudo.com" }],
        environment_name: "production"
      });
      assert.equal(requests[1].url, "http://coolify:8080/api/v1/services/service_test/envs/bulk");
      assert.equal(requests[1].method, "PATCH");
      assert.deepEqual(
        requests[1].body.data.find((item: any) => item.key === "AUDO_THEME_SLUG"),
        {
          key: "AUDO_THEME_SLUG",
          value: "audo-studio",
          is_literal: true,
          is_multiline: false,
          is_shown_once: false,
          comment: "Managed by Audo control plane"
        }
      );
      assert.equal(requests[2].url, "http://coolify:8080/api/v1/services/service_test/start");
    } finally {
      global.fetch = originalFetch;
    }
  });
});
