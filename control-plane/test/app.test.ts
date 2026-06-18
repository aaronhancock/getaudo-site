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
  cloudflare: { proxied: true, zoneName: "getaudo.com", tunnelOriginService: "https://127.0.0.1:443" },
  coolify: {
    wordpressServiceType: "wordpress-with-mariadb",
    wordpressInstantDeploy: true,
    wordpressAutoInstall: false,
    wordpressInstallTimeoutSeconds: 1
  },
  backups: {},
  stripe: {}
};

class FakeCloudflare implements CloudflareProvider {
  slugs: string[] = [];
  deletedSlugs: string[] = [];

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

  async deleteFreeSubdomain(slug: string) {
    this.deletedSlugs.push(slug);
    return { status: "ready" as const, details: { recordId: `record_${slug}` } };
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

  async provisionWordPressSite(site: SiteRecord): Promise<SiteDeployment> {
    return {
      id: "deploy_wordpress_test",
      provider: "preview",
      status: "skipped",
      url: `https://${site.primaryDomain}`,
      createdAt: new Date().toISOString(),
      details: { template: "wordpress", host: site.primaryDomain }
    };
  }

  async stopSite(site: SiteRecord): Promise<SiteDeployment> {
    return {
      id: "stop_site_test",
      provider: "preview",
      status: "skipped",
      url: `https://${site.primaryDomain}`,
      createdAt: new Date().toISOString(),
      details: { action: "stopped", host: site.primaryDomain }
    };
  }

  async deleteSite(site: SiteRecord): Promise<SiteDeployment> {
    return {
      id: "delete_site_test",
      provider: "preview",
      status: "skipped",
      url: `https://${site.primaryDomain}`,
      createdAt: new Date().toISOString(),
      details: { action: "deleted", host: site.primaryDomain }
    };
  }
}

class FailingWordPressCoolify extends FakeCoolify {
  async provisionWordPressSite(): Promise<SiteDeployment> {
    throw new Error("Coolify API unavailable");
  }
}

function createServices(cloudflare = new FakeCloudflare(), coolify: CoolifyProvider = new FakeCoolify()): AppServices {
  return {
    store: new MemorySiteStore(),
    cloudflare,
    coolify,
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
      body: JSON.stringify({ name: "Test Site", platform: "builder", template: "service" })
    });
    assert.equal(created.response.status, 201);
    assert.equal(created.body.site.slug, "test-site");
    assert.equal(created.body.site.primaryDomain, "test-site.getaudo.com");

    const published = await request(`/api/sites/${created.body.site.id}/publish`, { method: "POST", body: "{}" });
    assert.equal(published.response.status, 200);
    assert.equal(published.body.site.status, "published");
    assert.equal(published.body.site.domains[0].status, "ready");
    assert.equal(published.body.site.deployments.some((deployment: any) => "commit" in deployment), false);
    assert.deepEqual(cloudflare.slugs, ["test-site"]);

    const publicSite = await fetch(`${baseUrl}/`, { headers: { "x-forwarded-host": "test-site.getaudo.com" } });
    assert.equal(publicSite.status, 200);
    assert.match(await publicSite.text(), /Test Site|Created with Audo free hosting/);
  });

  it("generates unique free subdomains and ignores client supplied slugs", async () => {
    const duplicateName = await request("/api/sites", {
      method: "POST",
      body: JSON.stringify({ name: "Test Site", platform: "builder", slug: "manual-slug" })
    });
    assert.equal(duplicateName.response.status, 201);
    assert.equal(duplicateName.body.site.slug, "test-site-2");
    assert.equal(duplicateName.body.site.primaryDomain, "test-site-2.getaudo.com");
  });

  it("gates custom domains, GitHub, and backups to paid sites", async () => {
    const free = await request("/api/sites", {
      method: "POST",
      body: JSON.stringify({ name: "Free Site", platform: "builder" })
    });
    const domain = await request(`/api/sites/${free.body.site.id}/domains`, {
      method: "POST",
      body: JSON.stringify({ host: "example.com" })
    });
    assert.equal(domain.response.status, 402);

    const paid = await request("/api/sites", {
      method: "POST",
      body: JSON.stringify({ name: "Paid Site", plan: "paid" })
    });
    const backup = await request(`/api/sites/${paid.body.site.id}/backups`, { method: "POST", body: "{}" });
    assert.equal(backup.response.status, 202);
    assert.equal(backup.body.site.backups[0].id, "backup_test");
  });

  it("creates free DIY WordPress sites and provisions WordPress immediately", async () => {
    const created = await request("/api/sites", {
      method: "POST",
      body: JSON.stringify({
        name: "WordPress Free",
        platform: "wordpress",
        plan: "free",
        wordpress: {
          adminEmail: "not-the-owner@example.com",
          ownerEmail: "also-not-the-owner@example.com",
          themeSlug: "audo-studio"
        }
      })
    });
    assert.equal(created.response.status, 201);
    assert.equal(created.body.site.type, "wordpress");
    assert.equal(created.body.site.plan, "free");
    assert.equal(created.body.site.status, "published");
    assert.equal(created.body.site.primaryDomain, "wordpress-free.getaudo.com");
    assert.equal(created.body.site.wordpress.ownerEmail, "test-owner@preview.getaudo.com");
    assert.equal(created.body.site.wordpress.adminEmail, "test-owner@preview.getaudo.com");
    assert.equal(created.body.site.wordpress.themeSlug, "audo-neighborhood");
    assert.equal(created.body.site.deployments[0].id, "deploy_wordpress_test");
    assert.equal(created.body.site.deployments.some((deployment: any) => deployment.provider === "local-static"), false);

    const updated = await request(`/api/sites/${created.body.site.id}`, {
      method: "PATCH",
      body: JSON.stringify({ wordpress: { themeSlug: "audo-table" } })
    });
    assert.equal(updated.response.status, 200);
    assert.equal(updated.body.site.wordpress.themeSlug, "audo-neighborhood");
    assert.equal(updated.body.site.wordpress.adminEmail, "test-owner@preview.getaudo.com");
  });

  it("creates paid custom app and concierge site records without the builder flow", async () => {
    const appSite = await request("/api/sites", {
      method: "POST",
      body: JSON.stringify({ name: "Client Portal", platform: "github-app", plan: "free" })
    });
    assert.equal(appSite.response.status, 201);
    assert.equal(appSite.body.site.type, "github-app");
    assert.equal(appSite.body.site.plan, "paid");

    const unconnectedDeploy = await request(`/api/sites/${appSite.body.site.id}/publish`, { method: "POST", body: "{}" });
    assert.equal(unconnectedDeploy.response.status, 400);

    const connected = await request(`/api/sites/${appSite.body.site.id}/github`, {
      method: "POST",
      body: JSON.stringify({ owner: "audo", repo: "client-portal", branch: "main" })
    });
    assert.equal(connected.response.status, 200);
    assert.equal(connected.body.site.type, "github-app");
    assert.equal(connected.body.site.deployments[0].id, "deploy_github_test");

    const concierge = await request("/api/sites", {
      method: "POST",
      body: JSON.stringify({ name: "Done For You Site", platform: "concierge" })
    });
    assert.equal(concierge.response.status, 201);
    assert.equal(concierge.body.site.type, "concierge");
    assert.equal(concierge.body.site.plan, "paid");
  });

  it("records failed WordPress provisioning attempts", async () => {
    const failingServer = createServer(createApp(config, createServices(new FakeCloudflare(), new FailingWordPressCoolify())));
    await new Promise<void>((resolve) => failingServer.listen(0, resolve));
    const address = failingServer.address() as AddressInfo;
    const failingBaseUrl = `http://127.0.0.1:${address.port}`;

    async function failingRequest(path: string, init: RequestInit = {}) {
      const response = await fetch(`${failingBaseUrl}${path}`, {
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

    try {
      const created = await failingRequest("/api/sites", {
        method: "POST",
        body: JSON.stringify({ name: "Failing WordPress", platform: "wordpress", plan: "paid" })
      });
      assert.equal(created.response.status, 201);
      assert.match(created.body.warning.message, /Coolify API unavailable/);

      const site = await failingRequest(`/api/sites/${created.body.site.id}`);
      assert.equal(site.body.site.status, "configured");
      assert.equal(site.body.site.domains[0].status, "ready");
      assert.equal(site.body.site.deployments[0].status, "failed");
      assert.equal(site.body.site.deployments[0].details.action, "wordpress_provision_failed");

      const events = await failingRequest(`/api/sites/${created.body.site.id}/events`);
      assert.equal(events.body.events[0].type, "wordpress.provision_failed");
    } finally {
      await new Promise<void>((resolve, reject) => failingServer.close((error) => (error ? reject(error) : resolve())));
    }
  });

  it("unpublishes and deletes sites from Audo", async () => {
    const created = await request("/api/sites", {
      method: "POST",
      body: JSON.stringify({ name: "Delete Me", platform: "wordpress", plan: "free" })
    });
    assert.equal(created.body.site.status, "published");

    const unpublished = await request(`/api/sites/${created.body.site.id}/unpublish`, { method: "POST", body: "{}" });
    assert.equal(unpublished.response.status, 200);
    assert.equal(unpublished.body.site.status, "configured");
    assert.equal(unpublished.body.site.deployments[0].id, "stop_site_test");

    const deleted = await request(`/api/sites/${created.body.site.id}`, { method: "DELETE" });
    assert.equal(deleted.response.status, 200);
    assert.equal(deleted.body.site.status, "deleted");
    assert.equal(deleted.body.site.deployments[0].id, "delete_site_test");
    assert.ok(cloudflare.deletedSlugs.includes("delete-me"));

    const list = await request("/api/sites");
    assert.equal(list.body.sites.some((site: any) => site.id === created.body.site.id), false);

    const sameName = await request("/api/sites", {
      method: "POST",
      body: JSON.stringify({ name: "Delete Me", platform: "wordpress", plan: "free" })
    });
    assert.equal(sameName.body.site.slug, "delete-me");
  });

  it("reports Cloudflare status", async () => {
    const status = await request("/api/dns/cloudflare/status");
    assert.equal(status.response.status, 200);
    assert.equal(status.body.cloudflare.zoneName, "getaudo.com");
  });

  it("manages team users", async () => {
    const created = await request("/api/users", {
      method: "POST",
      body: JSON.stringify({
        email: "member@example.com",
        password: "password123",
        name: "Team Member",
        role: "member"
      })
    });
    assert.equal(created.response.status, 201);
    assert.equal(created.body.user.email, "member@example.com");
    assert.equal(created.body.user.role, "member");

    const list = await request("/api/users");
    assert.equal(list.response.status, 200);
    assert.ok(list.body.users.some((user: any) => user.email === "member@example.com"));

    const disabled = await request(`/api/users/${created.body.user.uid}`, {
      method: "PATCH",
      body: JSON.stringify({ disabled: true, role: "admin" })
    });
    assert.equal(disabled.response.status, 200);
    assert.equal(disabled.body.user.disabled, true);
    assert.equal(disabled.body.user.role, "admin");
  });

  it("can require a preview API secret", async () => {
    const lockedConfig = { ...config, previewApiSecret: "preview-secret" };
    const lockedServer = createServer(createApp(lockedConfig, createServices()));
    await new Promise<void>((resolve) => lockedServer.listen(0, resolve));
    const address = lockedServer.address() as AddressInfo;
    const lockedBaseUrl = `http://127.0.0.1:${address.port}`;

    try {
      const rejected = await fetch(`${lockedBaseUrl}/api/sites`, {
        headers: { "x-audo-preview-user": "test-owner" }
      });
      assert.equal(rejected.status, 401);

      const accepted = await fetch(`${lockedBaseUrl}/api/sites`, {
        headers: {
          "x-audo-preview-user": "test-owner",
          "x-audo-preview-secret": "preview-secret"
        }
      });
      assert.equal(accepted.status, 200);
    } finally {
      await new Promise<void>((resolve, reject) => lockedServer.close((error) => (error ? reject(error) : resolve())));
    }
  });
});
