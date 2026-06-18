import { randomBytes } from "node:crypto";
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
      const installResponse = await this.maybeAutoInstallWordPress(site);
      return {
        id: existingServiceUuid,
        provider: "coolify",
        status: this.wordpressDeploymentStatus(installResponse),
        url: `https://${site.primaryDomain}`,
        createdAt,
        details: {
          action: this.config.wordpressInstantDeploy ? "started_existing_wordpress_service" : "reused_existing_wordpress_service",
          serviceUuid: existingServiceUuid,
          serviceType: this.config.wordpressServiceType,
          requestedDomain: site.primaryDomain,
          envResponse,
          startResponse,
          wordpressInstall: installResponse
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
    const installResponse = serviceUuid ? await this.maybeAutoInstallWordPress(site) : { status: "skipped", reason: "missing_service_uuid" };

    return {
      id: serviceUuid || nanoid(),
      provider: "coolify",
      status: this.wordpressDeploymentStatus(installResponse),
      url: `https://${site.primaryDomain}`,
      createdAt,
      details: {
        action: this.config.wordpressInstantDeploy ? "created_and_started_wordpress_service" : "created_wordpress_service",
        serviceUuid: response.uuid,
        serviceType: this.config.wordpressServiceType,
        requestedDomain: site.primaryDomain,
        domains: response.domains || [],
        envResponse,
        startResponse,
        wordpressInstall: installResponse
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
      AUDO_SITE_PLAN: site.plan,
      AUDO_ADS_ENABLED: site.plan === "paid" ? "false" : "true",
      AUDO_FREE_PAGE_LIMIT: "5",
      AUDO_FREE_UPLOAD_LIMIT_MB: "250"
    };
  }

  private async maybeAutoInstallWordPress(site: SiteRecord): Promise<Record<string, unknown> | undefined> {
    if (!this.config.wordpressAutoInstall) {
      return { status: "skipped", reason: "wordpress_auto_install_disabled" };
    }
    try {
      return await this.autoInstallWordPress(site);
    } catch (error) {
      return { status: "failed", error: this.errorDetails(error) };
    }
  }

  private async autoInstallWordPress(site: SiteRecord): Promise<Record<string, unknown>> {
    const baseUrl = `https://${site.primaryDomain}`.replace(/\/+$/, "");
    const adminEmail = site.wordpress?.adminEmail || site.wordpress?.ownerEmail || `${site.ownerUid}@preview.getaudo.com`;
    const adminUsername = this.wordpressAdminUsername(site);
    const initialAdminPassword = randomBytes(24).toString("base64url");
    const installUrl = `${baseUrl}/wp-admin/install.php`;
    const loginUrl = `${baseUrl}/wp-login.php`;
    const timeoutMs = Math.max(5, this.config.wordpressInstallTimeoutSeconds || 180) * 1000;
    const deadline = Date.now() + timeoutMs;
    let lastState: Record<string, unknown> = { status: "pending" };

    while (Date.now() <= deadline) {
      const state = await this.wordpressInstallState(installUrl);
      lastState = state;
      if (state.status === "already_installed") {
        return { status: "already_installed", adminUsername, adminEmail, loginUrl };
      }
      if (state.status === "installer_ready") {
        const installed = await this.submitWordPressInstall(installUrl, site, adminUsername, initialAdminPassword, adminEmail);
        if (installed.status === "installed" || installed.status === "already_installed") {
          return {
            status: installed.status,
            adminUsername,
            adminEmail,
            initialAdminPassword,
            loginUrl
          };
        }
        lastState = installed;
      }
      await this.sleep(5000);
    }

    return {
      status: "pending",
      reason: "wordpress_installer_not_ready",
      adminUsername,
      adminEmail,
      loginUrl,
      lastState
    };
  }

  private async wordpressInstallState(installUrl: string): Promise<Record<string, unknown>> {
    try {
      const response = await fetch(installUrl, {
        redirect: "manual",
        headers: { "user-agent": "Audo-Control-Plane/1.0" }
      });
      const text = await response.text().catch(() => "");
      if (/already installed/i.test(text) || response.headers.get("location")?.includes("wp-login.php")) {
        return { status: "already_installed", httpStatus: response.status };
      }
      if (response.ok && /install\.php\?step=2|weblog_title|admin_password|user_name/i.test(text)) {
        return { status: "installer_ready", httpStatus: response.status };
      }
      return { status: "waiting", httpStatus: response.status, sample: text.slice(0, 160) };
    } catch (error) {
      return { status: "waiting", error: this.errorDetails(error) };
    }
  }

  private async submitWordPressInstall(
    installUrl: string,
    site: SiteRecord,
    adminUsername: string,
    initialAdminPassword: string,
    adminEmail: string
  ): Promise<Record<string, unknown>> {
    const body = new URLSearchParams({
      weblog_title: site.wordpress?.siteTitle || site.name,
      user_name: adminUsername,
      admin_password: initialAdminPassword,
      admin_password2: initialAdminPassword,
      admin_email: adminEmail,
      blog_public: "1",
      Submit: "Install WordPress"
    });
    const response = await fetch(`${installUrl}?step=2`, {
      method: "POST",
      redirect: "manual",
      headers: {
        "content-type": "application/x-www-form-urlencoded",
        "user-agent": "Audo-Control-Plane/1.0"
      },
      body
    });
    const text = await response.text().catch(() => "");
    if (/already installed/i.test(text)) {
      return { status: "already_installed", httpStatus: response.status };
    }
    if ((response.ok || response.status < 400) && /success|log in|wp-login\.php/i.test(text + String(response.headers.get("location") || ""))) {
      return { status: "installed", httpStatus: response.status };
    }
    return { status: "waiting", httpStatus: response.status, sample: text.slice(0, 160) };
  }

  private wordpressAdminUsername(site: SiteRecord): string {
    const base = `audo_${site.slug}`.toLowerCase().replace(/[^a-z0-9_.@-]+/g, "_").replace(/-+/g, "_");
    return base.slice(0, 60).replace(/^_+|_+$/g, "") || "audo_admin";
  }

  private wordpressDeploymentStatus(installResponse: Record<string, unknown> | undefined): SiteDeployment["status"] {
    if (installResponse?.status === "installed" || installResponse?.status === "already_installed") {
      return "finished";
    }
    return this.config.wordpressInstantDeploy ? "queued" : "finished";
  }

  private sleep(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }

  private errorDetails(error: unknown): Record<string, unknown> {
    return error instanceof Error ? { message: error.message, stack: error.stack } : { message: String(error) };
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
