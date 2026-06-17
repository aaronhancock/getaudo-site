export type Plan = "free" | "paid";
export type SiteStatus = "draft" | "configured" | "published" | "suspended";

export interface AuthUser {
  uid: string;
  email?: string;
  name?: string;
  teamId: string;
  role: "owner" | "admin" | "member";
}

export interface BuilderComponent {
  id: string;
  type: string;
  label?: string;
  headline?: string;
  body?: string;
  button?: string;
  brand?: string;
  links?: string;
  items?: string;
}

export interface BuilderDocument {
  version: 1;
  components: BuilderComponent[];
}

export interface DomainRecord {
  id: string;
  host: string;
  kind: "free-subdomain" | "custom";
  status: "ready" | "pending-dns" | "active" | "failed";
  createdAt: string;
  verification?: DnsInstruction[];
}

export interface DnsInstruction {
  type: "CNAME" | "A" | "TXT";
  name: string;
  value: string;
  proxied?: boolean;
}

export interface GitHubIntegration {
  installationId?: string;
  owner?: string;
  repo?: string;
  branch?: string;
  buildCommand?: string;
  outputDirectory?: string;
  connected: boolean;
}

export interface SiteDeployment {
  id: string;
  provider: "local-static" | "coolify" | "preview";
  status: "queued" | "running" | "finished" | "failed" | "skipped";
  url?: string;
  commit?: string;
  artifactPath?: string;
  createdAt: string;
  details?: Record<string, unknown>;
}

export interface BackupRecord {
  id: string;
  status: "queued" | "running" | "complete" | "failed";
  size?: string;
  createdAt: string;
  details?: Record<string, unknown>;
}

export interface SiteRecord {
  id: string;
  teamId: string;
  ownerUid: string;
  name: string;
  slug: string;
  plan: Plan;
  status: SiteStatus;
  type: "builder" | "github-app";
  primaryDomain: string;
  domains: DomainRecord[];
  builder: BuilderDocument;
  github: GitHubIntegration;
  deployments: SiteDeployment[];
  backups: BackupRecord[];
  createdAt: string;
  updatedAt: string;
  publishedAt?: string;
}

export interface SiteEvent {
  id: string;
  siteId: string;
  teamId: string;
  type: string;
  message: string;
  createdAt: string;
  data?: Record<string, unknown>;
}

export interface AppServices {
  store: SiteStore;
  cloudflare: CloudflareProvider;
  coolify: CoolifyProvider;
  backups: BackupProvider;
  billing: BillingProvider;
}

export interface SiteStore {
  listSites(teamId: string): Promise<SiteRecord[]>;
  getSite(teamId: string, siteId: string): Promise<SiteRecord | null>;
  findSiteBySlug(slug: string): Promise<SiteRecord | null>;
  createSite(site: SiteRecord): Promise<SiteRecord>;
  updateSite(teamId: string, siteId: string, patch: Partial<SiteRecord>): Promise<SiteRecord>;
  appendEvent(event: SiteEvent): Promise<SiteEvent>;
  listEvents(teamId: string, siteId: string): Promise<SiteEvent[]>;
}

export interface CloudflareProvider {
  verifyConnection(): Promise<{ status: "ready" | "skipped"; zoneId?: string; zoneName?: string; details?: Record<string, unknown> }>;
  ensureFreeSubdomain(slug: string): Promise<{ status: "ready" | "skipped"; record?: DnsInstruction; details?: Record<string, unknown> }>;
  customDomainInstructions(host: string): DnsInstruction[];
}

export interface CoolifyProvider {
  deploySharedBuilder(commit?: string): Promise<SiteDeployment>;
  createGitHubApplication(site: SiteRecord): Promise<SiteDeployment>;
}

export interface BackupProvider {
  requestBackup(site: SiteRecord): Promise<BackupRecord>;
}

export interface BillingProvider {
  createCheckout(params: { site: SiteRecord; plan: "paid"; successUrl?: string; cancelUrl?: string }): Promise<{ url: string; mode: "stripe" | "preview" }>;
}
