import { nanoid } from "nanoid";
import type { AppConfig } from "../config.js";
import type { BackupProvider, BackupRecord, SiteRecord } from "../types.js";

export class WebhookBackupProvider implements BackupProvider {
  constructor(private config: AppConfig["backups"]) {}

  async requestBackup(site: SiteRecord): Promise<BackupRecord> {
    const createdAt = new Date().toISOString();
    if (!this.config.webhookUrl) {
      return {
        id: nanoid(),
        status: "queued",
        createdAt,
        details: { mode: "preview", reason: "backup_webhook_not_configured" }
      };
    }
    const response = await fetch(this.config.webhookUrl, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({
        siteId: site.id,
        slug: site.slug,
        plan: site.plan,
        domains: site.domains.map((domain) => domain.host)
      })
    });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
      throw new Error(`Backup webhook failed: ${response.status} ${JSON.stringify(data)}`);
    }
    return {
      id: String(data.id || nanoid()),
      status: data.status || "queued",
      size: data.size,
      createdAt,
      details: data
    };
  }
}
