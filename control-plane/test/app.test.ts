import assert from "node:assert/strict";
import { after, before, describe, it } from "node:test";
import type { AddressInfo } from "node:net";
import { createServer, type Server } from "node:http";
import { createApp } from "../src/app.js";
import type { AppConfig } from "../src/config.js";
import { MemorySiteStore } from "../src/store.js";
import type { AppServices, BackupRecord, CloudflareProvider, CoolifyProvider, SiteDeployment, SiteRecord } from "../src/types.js";

const config: AppConfig = {
  nodeEnv: "test",
  port: 0,
  corsOrigin: "http://localhost",
  authMode: "preview",
  storeMode: "memory",
  freeDomain: "getaudo.com",
  publicBaseUrl: "https://getaudo.com",
  publishedSiteRoot: "/tmp/audo-control-plane-test",
  cloudflare: { proxied: true, zoneName: "getaudo.com" },
  coolify: {},
  backups: {},
  stripe: {}
};

class FakeCloudflare implements CloudflareProvider {
  slugs: string[] = [];

  async verifyConnection() {
    return { status: "ready" as const, zoneId: "zone_test", zoneName: "getaudo.com" };
  }

  async ensureFreeSubdomain(slug: string) {
    this.slugs.push(slug);
    return {
      status: "ready" as const,
      record: { type: "CNAME" as const, name: `${slug}.getaudo.com`, value: "getaudo.com", proxied: true },
      details: { recordId: `record_${slug}` }
    };
  }

  customDomainInstructions(host: string) {
    return [{ type: "CNAME" as const, name: host, value: "getaudo.com", proxied: true }];
  }
}

class FakeCoolify implements CoolifyProvider {
  async deploySharedBuilder(): Promise<SiteDeployment> {
    return { id: "deploy_test", provider: "preview", status: "skipped", createdAt: new Date().toISOString() };
  }

  async createGitHubApplication(site: SiteRecord): Promise<SiteDeployment> {
    return {
      id: "deploy_github_test",
      provider: "preview",
      status: "skipped",
      createdAt: new Date().toISOString(),
      details: { repo: site.github.repo }
    };
  }
}

function createServices(cloudflare = new FakeCloudflare()): AppServices {
  return {
    store: new MemorySiteStore(),
    cloudflare,
    coolify: new FakeCoolify(),
    backups: {
      async requestBackup(): Promise<BackupRecord> {
        return { id: "backup_test", status: "queued", createdAt: new Date().toISOString() };
      }
    },
    billing: {
      async createCheckout() {
        return { url: "https://getaudo.com/app?checkout=preview", mode: "preview" as const };
      }
    }
  };
}

describe("Audo control plane", () => {
  let server: Server;
  let baseUrl: string;
  let cloudflare: FakeCloudflare;

  before(async () => {
    cloudflare = new FakeCloudflare();
    server = createServer(createApp(config, createServices(cloudflare)));
    await new Promise<void>((resolve) => server.listen(0, resolve));
    const address = server.address() as AddressInfo;
    baseUrl = `http://127.0.0.1:${address.port}`;
  });

  after(async () => {
    await new Promise<void>((resolve, reject) => server.close((error) => (error ? reject(error) : resolve())));
  });

  async function request(path: string, init: RequestInit = {}) {
    const response = await fetch(`${baseUrl}${path}`, {
      ...init,
      headers: {
        "content-type": "application/json",
        "x-audo-preview-user": "test-owner",
        ...(init.headers || {})
      }
    });
    const body = await response.json();
    return { response, body };
  }

  it("creates a site, provisions DNS, and publishes it", async () => {
    const created = await request("/api/sites", {
      method: "POST",
      body: JSON.stringify({ name: "Test Site", slug: "test-site", template: "service" })
    });
    assert.equal(created.response.status, 201);
    assert.equal(created.body.site.primaryDomain, "test-site.getaudo.com");

    const published = await request(`/api/sites/${created.body.site.id}/publish`, { method: "POST", body: "{}" });
    assert.equal(published.response.status, 200);
    assert.equal(published.body.site.status, "published");
    assert.equal(published.body.site.domains[0].status, "ready");
    assert.deepEqual(cloudflare.slugs, ["test-site"]);
  });

  it("prevents duplicate free subdomains", async () => {
    const duplicate = await request("/api/sites", {
      method: "POST",
      body: JSON.stringify({ name: "Another Test", slug: "test-site" })
    });
    assert.equal(duplicate.response.status, 409);
    assert.equal(duplicate.body.error.code, "conflict");
  });

  it("gates custom domains, GitHub, and backups to paid sites", async () => {
    const free = await request("/api/sites", {
      method: "POST",
      body: JSON.stringify({ name: "Free Site", slug: "free-site" })
    });
    const domain = await request(`/api/sites/${free.body.site.id}/domains`, {
      method: "POST",
      body: JSON.stringify({ host: "example.com" })
    });
    assert.equal(domain.response.status, 402);

    const paid = await request("/api/sites", {
      method: "POST",
      body: JSON.stringify({ name: "Paid Site", slug: "paid-site", plan: "paid" })
    });
    const backup = await request(`/api/sites/${paid.body.site.id}/backups`, { method: "POST", body: "{}" });
    assert.equal(backup.response.status, 202);
    assert.equal(backup.body.site.backups[0].id, "backup_test");
  });

  it("reports Cloudflare status", async () => {
    const status = await request("/api/dns/cloudflare/status");
    assert.equal(status.response.status, 200);
    assert.equal(status.body.cloudflare.zoneName, "getaudo.com");
  });
});
