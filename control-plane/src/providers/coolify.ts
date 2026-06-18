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

  async cloneWordPressTemplate(site: SiteRecord): Promise<SiteDeployment> {
    const createdAt = new Date().toISOString();
    if (!this.config.baseUrl || !this.config.apiToken || !this.config.wordpressTemplateAppUuid) {
      return {
        id: nanoid(),
        provider: "preview",
        status: "skipped",
        url: `https://${site.primaryDomain}`,
        createdAt,
        details: {
          reason: "wordpress_template_not_configured",
          requestedDomain: site.primaryDomain
        }
      };
    }
    return {
      id: nanoid(),
      provider: "coolify",
      status: "skipped",
      url: `https://${site.primaryDomain}`,
      createdAt,
      details: {
        reason: "coolify_wordpress_clone_requires_project_mapping",
        templateAppUuid: this.config.wordpressTemplateAppUuid,
        requestedDomain: site.primaryDomain
      }
    };
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
