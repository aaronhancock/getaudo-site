import type { AppConfig } from "../config.js";
import type { CloudflareProvider, DnsInstruction } from "../types.js";

interface CloudflareRecord {
  id: string;
  type: string;
  name: string;
  content: string;
}

interface CloudflareZone {
  id: string;
  name: string;
  status?: string;
}

interface CloudflareTunnelIngressRule {
  hostname?: string;
  service: string;
  originRequest?: Record<string, unknown>;
}

interface CloudflareTunnelConfig {
  ingress?: CloudflareTunnelIngressRule[];
  [key: string]: unknown;
}

export class CloudflareDnsProvider implements CloudflareProvider {
  private resolvedZone?: CloudflareZone;

  constructor(private config: AppConfig["cloudflare"], private freeDomain: string) {}

  async verifyConnection(): Promise<{ status: "ready" | "skipped"; zoneId?: string; zoneName?: string; details?: Record<string, unknown> }> {
    if (!this.config.apiToken) {
      return { status: "skipped", details: { reason: "cloudflare_token_not_configured" } };
    }
    const zone = await this.getZone();
    if (!zone) {
      return {
        status: "skipped",
        zoneName: this.zoneName(),
        details: { reason: "cloudflare_zone_not_found" }
      };
    }
    return {
      status: "ready",
      zoneId: zone.id,
      zoneName: zone.name,
      details: { zoneStatus: zone.status }
    };
  }

  async ensureFreeSubdomain(slug: string): Promise<{ status: "ready" | "skipped"; record?: DnsInstruction; details?: Record<string, unknown> }> {
    const host = `${slug}.${this.freeDomain}`;
    const target = this.config.freeSiteTarget || this.config.originIpv4;
    const type: "CNAME" | "A" = this.config.freeSiteTarget ? "CNAME" : "A";
    const zone = this.config.apiToken ? await this.getZone() : null;
    if (!this.config.apiToken || !zone || !target) {
      return {
        status: "skipped",
        record: { type, name: host, value: target || "configure CLOUDFLARE_FREE_SITE_TARGET or CLOUDFLARE_ORIGIN_IPV4", proxied: this.config.proxied },
        details: { reason: "cloudflare_not_configured", zoneName: this.zoneName() }
      };
    }

    const existing = await this.findRecord(zone.id, type, host);
    const payload = {
      type,
      name: host,
      content: target,
      proxied: this.config.proxied,
      ttl: 1
    };
    let saved: any;
    if (existing) {
      saved = await this.cloudflare(`/zones/${zone.id}/dns_records/${existing.id}`, {
        method: "PUT",
        body: JSON.stringify(payload)
      });
    } else {
      saved = await this.cloudflare(`/zones/${zone.id}/dns_records`, {
        method: "POST",
        body: JSON.stringify(payload)
      });
    }
    const tunnelIngress = await this.ensureTunnelIngress(host);
    return {
      status: "ready",
      record: { type, name: host, value: target, proxied: this.config.proxied },
      details: {
        zoneId: zone.id,
        recordId: saved.result?.id || existing?.id,
        action: existing ? "updated" : "created",
        tunnelIngress
      }
    };
  }

  async deleteFreeSubdomain(slug: string): Promise<{ status: "ready" | "skipped"; details?: Record<string, unknown> }> {
    const host = `${slug}.${this.freeDomain}`;
    const zone = this.config.apiToken ? await this.getZone() : null;
    if (!this.config.apiToken || !zone) {
      return { status: "skipped", details: { reason: "cloudflare_not_configured", host, zoneName: this.zoneName() } };
    }

    const deleted: string[] = [];
    for (const type of ["CNAME", "A"] as const) {
      const existing = await this.findRecord(zone.id, type, host);
      if (existing) {
        await this.cloudflare(`/zones/${zone.id}/dns_records/${existing.id}`, { method: "DELETE" });
        deleted.push(existing.id);
      }
    }
    const tunnelIngress = await this.deleteTunnelIngress(host);

    return { status: "ready", details: { host, deletedRecordIds: deleted, tunnelIngress } };
  }

  customDomainInstructions(host: string): DnsInstruction[] {
    const target = this.config.freeSiteTarget || this.freeDomain;
    return [
      {
        type: "CNAME",
        name: host,
        value: target,
        proxied: true
      }
    ];
  }

  private zoneName(): string {
    return this.config.zoneName || this.freeDomain;
  }

  private async getZone(): Promise<CloudflareZone | null> {
    if (this.resolvedZone) {
      return this.resolvedZone;
    }
    if (this.config.zoneId) {
      const result = await this.cloudflare(`/zones/${this.config.zoneId}`);
      this.resolvedZone = result.result || null;
      return this.resolvedZone || null;
    }

    const query = new URLSearchParams({ name: this.zoneName() });
    if (this.config.accountId) {
      query.set("account.id", this.config.accountId);
    }
    const result = await this.cloudflare(`/zones?${query.toString()}`);
    const zones = Array.isArray(result.result) ? result.result : [];
    this.resolvedZone = zones[0] || undefined;
    return this.resolvedZone || null;
  }

  private async findRecord(zoneId: string, type: "CNAME" | "A", name: string): Promise<CloudflareRecord | null> {
    const query = new URLSearchParams({ type, name });
    const result = await this.cloudflare(`/zones/${zoneId}/dns_records?${query.toString()}`);
    const records = Array.isArray(result.result) ? result.result : [];
    return records[0] || null;
  }

  private tunnelId(): string | undefined {
    if (this.config.tunnelId) {
      return this.config.tunnelId;
    }
    const target = this.config.freeSiteTarget || "";
    const match = target.match(/^([0-9a-f-]{36})\.cfargotunnel\.com$/i);
    return match?.[1];
  }

  private async ensureTunnelIngress(host: string): Promise<Record<string, unknown>> {
    const tunnelId = this.tunnelId();
    if (!this.config.apiToken || !this.config.accountId || !tunnelId || !this.config.freeSiteTarget?.includes("cfargotunnel.com")) {
      return { status: "skipped", reason: "cloudflare_tunnel_not_configured", host };
    }

    const config = await this.getTunnelConfig(tunnelId);
    const ingress = Array.isArray(config.ingress) ? [...config.ingress] : [];
    const rule: CloudflareTunnelIngressRule = {
      hostname: host,
      service: this.config.tunnelOriginService,
      originRequest: {
        noTLSVerify: true,
        httpHostHeader: host
      }
    };
    const nextIngress = ingress.filter((item) => item.hostname !== host);
    const wildcardIndex = nextIngress.findIndex((item) => item.hostname === `*.${this.freeDomain}`);
    const fallbackIndex = nextIngress.findIndex((item) => item.service?.startsWith("http_status:"));
    const insertIndex = wildcardIndex >= 0 ? wildcardIndex : fallbackIndex >= 0 ? fallbackIndex : nextIngress.length;
    nextIngress.splice(insertIndex, 0, rule);

    await this.putTunnelConfig(tunnelId, { ...config, ingress: nextIngress });
    return { status: "ready", host, tunnelId, action: ingress.some((item) => item.hostname === host) ? "updated" : "created" };
  }

  private async deleteTunnelIngress(host: string): Promise<Record<string, unknown>> {
    const tunnelId = this.tunnelId();
    if (!this.config.apiToken || !this.config.accountId || !tunnelId || !this.config.freeSiteTarget?.includes("cfargotunnel.com")) {
      return { status: "skipped", reason: "cloudflare_tunnel_not_configured", host };
    }

    const config = await this.getTunnelConfig(tunnelId);
    const ingress = Array.isArray(config.ingress) ? config.ingress : [];
    const nextIngress = ingress.filter((item) => item.hostname !== host);
    if (nextIngress.length === ingress.length) {
      return { status: "ready", host, tunnelId, action: "not_found" };
    }
    await this.putTunnelConfig(tunnelId, { ...config, ingress: nextIngress });
    return { status: "ready", host, tunnelId, action: "deleted" };
  }

  private async getTunnelConfig(tunnelId: string): Promise<CloudflareTunnelConfig> {
    const result = await this.cloudflare(`/accounts/${this.config.accountId}/cfd_tunnel/${tunnelId}/configurations`);
    return result.result?.config || {};
  }

  private async putTunnelConfig(tunnelId: string, config: CloudflareTunnelConfig): Promise<void> {
    await this.cloudflare(`/accounts/${this.config.accountId}/cfd_tunnel/${tunnelId}/configurations`, {
      method: "PUT",
      body: JSON.stringify({ config })
    });
  }

  private async cloudflare(path: string, init: RequestInit = { method: "GET" }): Promise<any> {
    const response = await fetch(`https://api.cloudflare.com/client/v4${path}`, {
      ...init,
      headers: {
        "content-type": "application/json",
        authorization: `Bearer ${this.config.apiToken}`,
        ...(init.headers || {})
      }
    });
    const data = await response.json();
    if (!response.ok || data.success === false) {
      throw new Error(`Cloudflare API error: ${JSON.stringify(data.errors || data)}`);
    }
    return data;
  }
}
