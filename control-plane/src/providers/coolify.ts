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

    const payload: Record<string, unknown> = {
      type: this.config.wordpressServiceType,
      name: this.wordpressServiceName(site),
      description: `Audo managed WordPress site for ${site.primaryDomain}`,
      project_uuid: this.config.wordpressProjectUuid,
      server_uuid: this.config.wordpressServerUuid,
      destination_uuid: this.config.wordpressDestinationUuid,
      instant_deploy: this.config.wordpressInstantDeploy,
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

    return {
      id: String(response.uuid || nanoid()),
      provider: "coolify",
      status: this.config.wordpressInstantDeploy ? "queued" : "finished",
      url: `https://${site.primaryDomain}`,
      createdAt,
      details: {
        serviceUuid: response.uuid,
        serviceType: this.config.wordpressServiceType,
        requestedDomain: site.primaryDomain,
        domains: response.domains || []
      }
    };
  }

  private wordpressServiceName(site: SiteRecord): string {
    return `audo-${site.slug}-wordpress`.replace(/[^a-z0-9-]/gi, "-").replace(/-+/g, "-").toLowerCase();
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
