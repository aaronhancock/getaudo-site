import { nanoid } from "nanoid";
import type { AppConfig } from "../config.js";
import type { CoolifyProvider, SiteDeployment, SiteRecord } from "../types.js";

export class CoolifyApiProvider implements CoolifyProvider {
  constructor(private config: AppConfig["coolify"]) {}

  async deploySharedBuilder(commit?: string): Promise<SiteDeployment> {
    const createdAt = new Date().toISOString();
    if (!this.config.baseUrl || !this.config.apiToken || !this.config.sharedBuilderAppUuid) {
      return {
        id: nanoid(),
        provider: "preview",
        status: "skipped",
        commit,
        createdAt,
        details: { reason: "coolify_not_configured" }
      };
    }
    const response = await this.coolify(`/api/v1/applications/${this.config.sharedBuilderAppUuid}/start`, {
      method: "POST"
    });
    return {
      id: String(response.deployment_uuid || response.uuid || nanoid()),
      provider: "coolify",
      status: "queued",
      commit,
      createdAt,
      details: response
    };
  }

  async createGitHubApplication(site: SiteRecord): Promise<SiteDeployment> {
    const createdAt = new Date().toISOString();
    if (!this.config.baseUrl || !this.config.apiToken) {
      return {
        id: nanoid(),
        provider: "preview",
        status: "skipped",
        createdAt,
        details: { reason: "coolify_not_configured", repo: site.github.repo }
      };
    }
    return {
      id: nanoid(),
      provider: "coolify",
      status: "skipped",
      createdAt,
      details: {
        reason: "coolify_github_app_creation_requires_project_mapping",
        repo: site.github.repo,
        branch: site.github.branch
      }
    };
  }

  async provisionWordPressSite(site: SiteRecord): Promise<SiteDeployment> {
    const createdAt = new Date().toISOString();
    if (!this.config.baseUrl || !this.config.apiToken || !this.config.wordpressProjectUuid || !this.config.wordpressServerUuid) {
      return {
        id: nanoid(),
        provider: "preview",
        status: "skipped",
        url: `https://${site.primaryDomain}`,
        createdAt,
        details: {
          reason: "coolify_wordpress_not_configured",
          requestedDomain: site.primaryDomain
        }
      };
    }

    const existingServiceUuid = this.existingWordPressServiceUuid(site);
    if (existingServiceUuid) {
      const envResponse = await this.upsertWordPressEnv(existingServiceUuid, site);
      const startResponse = this.config.wordpressInstantDeploy
        ? await this.coolify(`/api/v1/services/${existingServiceUuid}/start`, { method: "POST" })
        : undefined;
      return {
        id: existingServiceUuid,
        provider: "coolify",
        status: this.config.wordpressInstantDeploy ? "queued" : "finished",
        url: `https://${site.primaryDomain}`,
        createdAt,
        details: {
          action: this.config.wordpressInstantDeploy ? "started_existing_wordpress_service" : "reused_existing_wordpress_service",
          serviceUuid: existingServiceUuid,
          serviceType: this.config.wordpressServiceType,
          requestedDomain: site.primaryDomain,
          envResponse,
          startResponse
        }
      };
    }

    const payload: Record<string, unknown> = {
      type: this.config.wordpressServiceType,
      name: this.wordpressServiceName(site),
      description: `Audo managed WordPress site for ${site.primaryDomain}`,
      project_uuid: this.config.wordpressProjectUuid,
      server_uuid: this.config.wordpressServerUuid,
      destination_uuid: this.config.wordpressDestinationUuid,
      instant_deploy: false,
      urls: [{ name: "wordpress", url: `https://${site.primaryDomain}` }]
    };
    if (this.config.wordpressEnvironmentUuid) {
      payload.environment_uuid = this.config.wordpressEnvironmentUuid;
    } else {
      payload.environment_name = this.config.wordpressEnvironmentName || "production";
    }

    Object.keys(payload).forEach((key) => {
      if (payload[key] == null || payload[key] === "") {
        delete payload[key];
      }
    });

    const response = await this.coolify("/api/v1/services", {
      method: "POST",
      body: JSON.stringify(payload)
    });
    const serviceUuid = String(response.uuid || "");
    const envResponse = serviceUuid ? await this.upsertWordPressEnv(serviceUuid, site) : undefined;
    const startResponse =
      this.config.wordpressInstantDeploy && serviceUuid
        ? await this.coolify(`/api/v1/services/${serviceUuid}/start`, { method: "POST" })
        : undefined;

    return {
      id: serviceUuid || nanoid(),
      provider: "coolify",
      status: this.config.wordpressInstantDeploy ? "queued" : "finished",
      url: `https://${site.primaryDomain}`,
      createdAt,
      details: {
        action: this.config.wordpressInstantDeploy ? "created_and_started_wordpress_service" : "created_wordpress_service",
        serviceUuid: response.uuid,
        serviceType: this.config.wordpressServiceType,
        requestedDomain: site.primaryDomain,
        domains: response.domains || [],
        envResponse,
        startResponse
      }
    };
  }

  async stopSite(site: SiteRecord): Promise<SiteDeployment> {
    const createdAt = new Date().toISOString();
    const serviceUuid = this.existingWordPressServiceUuid(site);
    if (!this.config.baseUrl || !this.config.apiToken || !serviceUuid) {
      return {
        id: nanoid(),
        provider: "preview",
        status: "skipped",
        url: `https://${site.primaryDomain}`,
        createdAt,
        details: {
          action: "unpublish_skipped",
          reason: serviceUuid ? "coolify_not_configured" : "no_managed_coolify_service",
          requestedDomain: site.primaryDomain
        }
      };
    }

    const response = await this.coolify(`/api/v1/services/${serviceUuid}/stop`, { method: "POST" });
    return {
      id: nanoid(),
      provider: "coolify",
      status: "finished",
      url: `https://${site.primaryDomain}`,
      createdAt,
      details: {
        action: "stopped_coolify_service",
        serviceUuid,
        stopResponse: response
      }
    };
  }

  async deleteSite(site: SiteRecord): Promise<SiteDeployment> {
    const createdAt = new Date().toISOString();
    const serviceUuid = this.existingWordPressServiceUuid(site);
    if (!this.config.baseUrl || !this.config.apiToken || !serviceUuid) {
      return {
        id: nanoid(),
        provider: "preview",
        status: "skipped",
        url: `https://${site.primaryDomain}`,
        createdAt,
        details: {
          action: "delete_skipped",
          reason: serviceUuid ? "coolify_not_configured" : "no_managed_coolify_service",
          requestedDomain: site.primaryDomain
        }
      };
    }

    const response = await this.coolify(`/api/v1/services/${serviceUuid}`, { method: "DELETE" });
    return {
      id: nanoid(),
      provider: "coolify",
      status: "finished",
      url: `https://${site.primaryDomain}`,
      createdAt,
      details: {
        action: "deleted_coolify_service",
        serviceUuid,
        deleteResponse: response
      }
    };
  }

  private existingWordPressServiceUuid(site: SiteRecord): string | undefined {
    for (const deployment of site.deployments) {
      const value = deployment.details?.serviceUuid;
      if (typeof value === "string" && value) {
        return value;
      }
    }
    return undefined;
  }

  private wordpressServiceName(site: SiteRecord): string {
    return `audo-${site.slug}-wordpress`.replace(/[^a-z0-9-]/gi, "-").replace(/-+/g, "-").toLowerCase();
  }

  private wordpressEnv(site: SiteRecord): Record<string, string> {
    const settings = site.wordpress;
    const ownerEmail = settings?.ownerEmail || `${site.ownerUid}@preview.getaudo.com`;
    const adminEmail = settings?.adminEmail || ownerEmail;
    return {
      AUDO_SITE_ID: site.id,
      AUDO_SITE_DOMAIN: site.primaryDomain,
      AUDO_SITE_TITLE: settings?.siteTitle || site.name,
      AUDO_OWNER_EMAIL: ownerEmail,
      AUDO_ADMIN_EMAIL: adminEmail,
      AUDO_THEME_SLUG: settings?.themeSlug || "audo-neighborhood",
      AUDO_SITE_PLAN: site.plan,
      AUDO_ADS_ENABLED: site.plan === "paid" ? "false" : "true",
      AUDO_FREE_PAGE_LIMIT: "5",
      AUDO_FREE_UPLOAD_LIMIT_MB: "250",
      WORDPRESS_REDIS_HOST: "redis"
    };
  }

  private async upsertWordPressEnv(serviceUuid: string, site: SiteRecord): Promise<{ count: number; response: unknown }> {
    const data = Object.entries(this.wordpressEnv(site)).map(([key, value]) => ({
      key,
      value,
      is_literal: true,
      is_multiline: false,
      is_shown_once: false,
      comment: "Managed by Audo control plane"
    }));
    const response = await this.coolify(`/api/v1/services/${serviceUuid}/envs/bulk`, {
      method: "PATCH",
      body: JSON.stringify({ data })
    });
    return { count: data.length, response };
  }

  private async coolify(path: string, init: RequestInit): Promise<any> {
    const base = this.config.baseUrl?.replace(/\/+$/, "");
    const response = await fetch(`${base}${path}`, {
      ...init,
      headers: {
        accept: "application/json",
        "content-type": "application/json",
        authorization: `Bearer ${this.config.apiToken}`,
        ...(init.headers || {})
      }
    });
    const text = await response.text();
    let data: any = {};
    try {
      data = text ? JSON.parse(text) : {};
    } catch {
      data = { raw: text };
    }
    if (!response.ok) {
      throw new Error(`Coolify API error: ${response.status} ${JSON.stringify(data)}`);
    }
    return data;
  }
}
