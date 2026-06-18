import { nanoid } from "nanoid";
import type {
  AppServices,
  AuthUser,
  BackupRecord,
  BuilderDocument,
  DomainRecord,
  GitHubIntegration,
  Plan,
  SiteDeployment,
  SiteEvent,
  SiteRecord,
  WordPressSettings
} from "./types.js";
import type { AppConfig } from "./config.js";
import { badRequest, conflict, notFound, paymentRequired } from "./errors.js";
import { defaultBuilderDocument, writePublishedSite } from "./siteRenderer.js";

const RESERVED_SLUGS = new Set([
  "admin",
  "api",
  "app",
  "assets",
  "billing",
  "cdn",
  "dashboard",
  "docs",
  "ftp",
  "mail",
  "root",
  "static",
  "support",
  "www"
]);
const WORDPRESS_THEME_SLUGS = new Set(["audo-neighborhood", "audo-studio", "audo-table", "audo-signal", "audo-sanctuary"]);

export interface CreateSiteInput {
  name: string;
  plan?: Plan;
  platform?: "builder" | "wordpress" | "github-app" | "concierge";
  template?: string;
  builder?: BuilderDocument;
  wordpress?: Partial<WordPressSettings>;
}

export interface UpdateSiteInput {
  name?: string;
  builder?: BuilderDocument;
  wordpress?: Partial<WordPressSettings>;
}

export interface GitHubInput {
  installationId?: string;
  owner: string;
  repo: string;
  branch?: string;
  buildCommand?: string;
  outputDirectory?: string;
}

function now(): string {
  return new Date().toISOString();
}

function slugify(value: string): string {
  return value
    .toLowerCase()
    .trim()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 48);
}

function normalizeSlug(value: string): string {
  const slug = slugify(value);
  if (!/^[a-z0-9](?:[a-z0-9-]{0,46}[a-z0-9])?$/.test(slug)) {
    throw badRequest("Slug must use lowercase letters, numbers, and hyphens.");
  }
  if (RESERVED_SLUGS.has(slug)) {
    throw conflict("That subdomain is reserved.", { slug });
  }
  return slug;
}

function generatedSlugBase(value: string): string {
  const base = slugify(value) || "site";
  return RESERVED_SLUGS.has(base) ? trimSlug(`${base}-site`) : base;
}

function trimSlug(value: string): string {
  return value.slice(0, 48).replace(/-+$/g, "") || "site";
}

function slugWithSuffix(base: string, suffix: number): string {
  if (suffix <= 1) {
    return trimSlug(base);
  }
  const tail = `-${suffix}`;
  return `${trimSlug(base).slice(0, 48 - tail.length).replace(/-+$/g, "") || "site"}${tail}`;
}

function normalizeHost(value: string): string {
  const host = value.toLowerCase().trim().replace(/^https?:\/\//, "").replace(/\/.*$/, "");
  if (!/^(?=.{1,253}$)([a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}$/.test(host)) {
    throw badRequest("Custom domain must be a valid hostname.");
  }
  return host;
}

function freeHost(slug: string, config: AppConfig): string {
  return `${slug}.${config.freeDomain}`;
}

function deploymentList(site: SiteRecord, deployment: SiteDeployment): SiteDeployment[] {
  return [deployment, ...site.deployments].slice(0, 50);
}

function backupList(site: SiteRecord, backup: BackupRecord): BackupRecord[] {
  return [backup, ...site.backups].slice(0, 100);
}

function errorDetails(error: unknown): Record<string, unknown> {
  if (error instanceof Error) {
    return {
      message: error.message,
      name: error.name
    };
  }
  return {
    message: String(error)
  };
}

function wordpressSettings(user: AuthUser, name: string, input: CreateSiteInput): WordPressSettings | undefined {
  if (input.platform && input.platform !== "wordpress") {
    return undefined;
  }
  const accountEmail = user.email || `${user.uid}@preview.getaudo.com`;
  const themeSlug = input.wordpress?.themeSlug?.trim() || "audo-neighborhood";
  return {
    siteTitle: input.wordpress?.siteTitle?.trim() || name,
    ownerEmail: accountEmail,
    adminEmail: accountEmail,
    themeSlug: WORDPRESS_THEME_SLUGS.has(themeSlug) ? themeSlug : "audo-neighborhood"
  };
}

export class SiteService {
  constructor(private config: AppConfig, private services: AppServices) {}

  async listSites(user: AuthUser): Promise<SiteRecord[]> {
    return this.services.store.listSites(user.teamId);
  }

  async getSite(user: AuthUser, siteId: string): Promise<SiteRecord> {
    const site = await this.services.store.getSite(user.teamId, siteId);
    if (!site) {
      throw notFound("Site not found");
    }
    return site;
  }

  async getPublishedFreeSiteByHost(hostValue: string): Promise<SiteRecord | null> {
    const host = hostValue.toLowerCase().trim().replace(/\.$/, "").replace(/:\d+$/, "");
    const suffix = `.${this.config.freeDomain}`;
    if (!host.endsWith(suffix) || host === this.config.freeDomain) {
      return null;
    }
    const slug = host.slice(0, -suffix.length);
    if (!slug || slug.includes(".")) {
      return null;
    }
    const site = await this.services.store.findSiteBySlug(slug);
    if (!site || site.status !== "published" || site.type !== "builder") {
      return null;
    }
    return site.domains.some((domain) => domain.host === host) ? site : null;
  }

  async createSite(user: AuthUser, input: CreateSiteInput): Promise<SiteRecord> {
    const name = input.name.trim();
    if (!name) {
      throw badRequest("Site name is required.");
    }
    const slug = await this.generateUniqueSlug(name);

    const createdAt = now();
    const platform = input.platform || "wordpress";
    const plan = input.plan === "paid" || platform === "github-app" || platform === "concierge" ? "paid" : "free";
    const domain: DomainRecord = {
      id: nanoid(),
      host: freeHost(slug, this.config),
      kind: "free-subdomain",
      status: "pending-dns",
      createdAt
    };
    const site: SiteRecord = {
      id: nanoid(),
      teamId: user.teamId,
      ownerUid: user.uid,
      name,
      slug,
      plan,
      status: "draft",
      type: platform === "github-app" || platform === "concierge" || platform === "wordpress" ? platform : "builder",
      primaryDomain: domain.host,
      domains: [domain],
      builder: input.builder || defaultBuilderDocument(input.template),
      wordpress: wordpressSettings(user, name, { ...input, platform }),
      github: { connected: false },
      deployments: [],
      backups: [],
      createdAt,
      updatedAt: createdAt
    };
    const created = await this.services.store.createSite(site);
    await this.event(created, "site.created", `Created ${created.name}`);
    return created;
  }

  private async generateUniqueSlug(name: string): Promise<string> {
    const base = generatedSlugBase(name);
    for (let suffix = 1; suffix <= 1000; suffix += 1) {
      const candidate = normalizeSlug(slugWithSuffix(base, suffix));
      if (!(await this.services.store.findSiteBySlug(candidate))) {
        return candidate;
      }
    }
    throw conflict("Could not generate a unique subdomain for that site name.", { name });
  }

  async updateSite(user: AuthUser, siteId: string, input: UpdateSiteInput): Promise<SiteRecord> {
    const site = await this.getSite(user, siteId);
    const patch: Partial<SiteRecord> = {};
    if (input.name != null) {
      const name = input.name.trim();
      if (!name) {
        throw badRequest("Site name cannot be empty.");
      }
      patch.name = name;
    }
    if (input.builder != null) {
      patch.builder = input.builder;
    }
    if (input.wordpress != null && site.type === "wordpress") {
      patch.wordpress = wordpressSettings(user, patch.name || site.name, { name: patch.name || site.name, platform: "wordpress", wordpress: input.wordpress });
    }
    const updated = await this.services.store.updateSite(site.teamId, site.id, patch);
    await this.event(updated, "site.updated", `Updated ${updated.name}`);
    return updated;
  }

  async provisionFreeDomain(user: AuthUser, siteId: string): Promise<SiteRecord> {
    const site = await this.getSite(user, siteId);
    const result = await this.services.cloudflare.ensureFreeSubdomain(site.slug);
    const domains = site.domains.map((domain) => {
      if (domain.kind !== "free-subdomain") {
        return domain;
      }
      return {
        ...domain,
        status: result.status === "ready" ? "ready" : "pending-dns",
        verification: result.record ? [result.record] : domain.verification
      } satisfies DomainRecord;
    });
    const updated = await this.services.store.updateSite(site.teamId, site.id, {
      domains,
      status: result.status === "ready" && site.status === "draft" ? "configured" : site.status
    });
    await this.event(updated, "dns.free_subdomain", `Provisioned ${freeHost(site.slug, this.config)}`, result.details);
    return updated;
  }

  async addCustomDomain(user: AuthUser, siteId: string, hostValue: string): Promise<SiteRecord> {
    const site = await this.getSite(user, siteId);
    if (site.plan !== "paid") {
      throw paymentRequired("Custom domains require a paid plan.");
    }
    const host = normalizeHost(hostValue);
    if (host.endsWith(`.${this.config.freeDomain}`) || host === this.config.freeDomain) {
      throw badRequest("Use the free subdomain endpoint for getaudo.com subdomains.");
    }
    const existing = site.domains.find((domain) => domain.host === host);
    const domain: DomainRecord = existing || {
      id: nanoid(),
      host,
      kind: "custom",
      status: "pending-dns",
      createdAt: now()
    };
    domain.verification = this.services.cloudflare.customDomainInstructions(host);
    const domains = existing ? site.domains.map((item) => (item.id === domain.id ? domain : item)) : [domain, ...site.domains];
    const updated = await this.services.store.updateSite(site.teamId, site.id, {
      domains,
      primaryDomain: host,
      status: site.status === "draft" ? "configured" : site.status
    });
    await this.event(updated, "dns.custom_domain", `Added custom domain ${host}`);
    return updated;
  }

  async publishSite(user: AuthUser, siteId: string, commit?: string): Promise<SiteRecord> {
    let site = await this.provisionFreeDomain(user, siteId);
    if (site.type === "wordpress") {
      let deployment: SiteDeployment;
      try {
        deployment = await this.services.coolify.provisionWordPressSite(site);
      } catch (error) {
        const failedDeployment: SiteDeployment = {
          id: nanoid(),
          provider: "coolify",
          status: "failed",
          url: `https://${site.primaryDomain}`,
          commit,
          createdAt: now(),
          details: {
            action: "wordpress_provision_failed",
            requestedDomain: site.primaryDomain,
            error: errorDetails(error)
          }
        };
        site = await this.services.store.updateSite(site.teamId, site.id, {
          deployments: deploymentList(site, failedDeployment)
        });
        await this.event(site, "wordpress.provision_failed", `WordPress provisioning failed for ${site.primaryDomain}`, failedDeployment.details);
        throw error;
      }
      site = await this.services.store.updateSite(site.teamId, site.id, {
        status: "published",
        deployments: deploymentList(site, deployment),
        publishedAt: now()
      });
      await this.event(site, "wordpress.provisioned", `Provisioned managed WordPress for ${site.primaryDomain}`, deployment.details);
      return site;
    }
    if (site.type === "github-app") {
      if (!site.github.connected) {
        throw badRequest("Connect a GitHub repository before deploying a custom app.");
      }
      const deployment = await this.services.coolify.createGitHubApplication(site);
      site = await this.services.store.updateSite(site.teamId, site.id, {
        status: deployment.status === "failed" ? site.status : "published",
        deployments: deploymentList(site, deployment),
        publishedAt: deployment.status === "failed" ? site.publishedAt : now()
      });
      await this.event(site, "github.deployment_requested", `Requested app deployment for ${site.primaryDomain}`, deployment.details);
      return site;
    }
    if (site.type === "concierge") {
      throw badRequest("Done-for-you sites are planned and provisioned manually by Audo.");
    }
    const artifactPath = await writePublishedSite(this.config.publishedSiteRoot, site);
    const localDeployment: SiteDeployment = {
      id: nanoid(),
      provider: "local-static",
      status: "finished",
      url: `https://${site.primaryDomain}`,
      commit,
      artifactPath,
      createdAt: now()
    };
    const remoteDeployment = await this.services.coolify.deploySharedBuilder(commit);
    const deployments = deploymentList({ ...site, deployments: deploymentList(site, localDeployment) }, remoteDeployment);
    site = await this.services.store.updateSite(site.teamId, site.id, {
      status: "published",
      deployments,
      publishedAt: now()
    });
    await this.event(site, "site.published", `Published ${site.primaryDomain}`, { artifactPath, remoteDeployment });
    return site;
  }

  async connectGitHub(user: AuthUser, siteId: string, input: GitHubInput): Promise<SiteRecord> {
    const site = await this.getSite(user, siteId);
    if (site.plan !== "paid") {
      throw paymentRequired("GitHub integration requires a paid plan.");
    }
    const github: GitHubIntegration = {
      installationId: input.installationId,
      owner: input.owner,
      repo: input.repo,
      branch: input.branch || "main",
      buildCommand: input.buildCommand,
      outputDirectory: input.outputDirectory,
      connected: true
    };
    const updated = await this.services.store.updateSite(site.teamId, site.id, {
      type: "github-app",
      github
    });
    const deployment = await this.services.coolify.createGitHubApplication(updated);
    const withDeployment = await this.services.store.updateSite(updated.teamId, updated.id, {
      deployments: deploymentList(updated, deployment)
    });
    await this.event(withDeployment, "github.connected", `Connected ${github.owner}/${github.repo}`, deployment.details);
    return withDeployment;
  }

  async requestBackup(user: AuthUser, siteId: string): Promise<SiteRecord> {
    const site = await this.getSite(user, siteId);
    if (site.plan !== "paid") {
      throw paymentRequired("Backups require a paid plan.");
    }
    const backup = await this.services.backups.requestBackup(site);
    const updated = await this.services.store.updateSite(site.teamId, site.id, {
      backups: backupList(site, backup)
    });
    await this.event(updated, "backup.requested", `Backup requested for ${site.primaryDomain}`, backup.details);
    return updated;
  }

  async unpublishSite(user: AuthUser, siteId: string): Promise<SiteRecord> {
    const site = await this.getSite(user, siteId);
    const deployment = await this.services.coolify.stopSite(site);
    const unpublishedAt = now();
    const updated = await this.services.store.updateSite(site.teamId, site.id, {
      status: "configured",
      unpublishedAt,
      deployments: deploymentList(site, deployment)
    });
    await this.event(updated, "site.unpublished", `Unpublished ${site.primaryDomain}`, deployment.details);
    return updated;
  }

  async deleteSite(user: AuthUser, siteId: string): Promise<SiteRecord> {
    const site = await this.getSite(user, siteId);
    const deployment = await this.services.coolify.deleteSite(site);
    const dns = await this.services.cloudflare.deleteFreeSubdomain(site.slug);
    const deletedAt = now();
    const updated = await this.services.store.updateSite(site.teamId, site.id, {
      status: "deleted",
      deletedAt,
      unpublishedAt: deletedAt,
      deployments: deploymentList(site, deployment)
    });
    await this.event(updated, "site.deleted", `Deleted ${site.primaryDomain} from Audo`, { deployment: deployment.details, dns });
    return updated;
  }

  async createCheckout(user: AuthUser, siteId: string, successUrl?: string, cancelUrl?: string): Promise<{ url: string; mode: "stripe" | "preview" }> {
    const site = await this.getSite(user, siteId);
    return this.services.billing.createCheckout({ site, plan: "paid", successUrl, cancelUrl });
  }

  async listEvents(user: AuthUser, siteId: string): Promise<SiteEvent[]> {
    return this.services.store.listEvents(user.teamId, siteId);
  }

  private async event(site: SiteRecord, type: string, message: string, data?: Record<string, unknown>): Promise<void> {
    const event: SiteEvent = {
      id: nanoid(),
      siteId: site.id,
      teamId: site.teamId,
      type,
      message,
      createdAt: now()
    };
    if (data !== undefined) {
      event.data = data;
    }
    await this.services.store.appendEvent(event);
  }
}
