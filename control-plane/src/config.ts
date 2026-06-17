import path from "node:path";

export type AuthMode = "firebase" | "preview";
export type StoreMode = "firestore" | "memory";

export interface AppConfig {
  nodeEnv: string;
  port: number;
  corsOrigin: string;
  authMode: AuthMode;
  storeMode: StoreMode;
  freeDomain: string;
  publicBaseUrl: string;
  publishedSiteRoot: string;
  cloudflare: {
    apiToken?: string;
    accountId?: string;
    zoneId?: string;
    zoneName?: string;
    freeSiteTarget?: string;
    originIpv4?: string;
    proxied: boolean;
  };
  coolify: {
    baseUrl?: string;
    apiToken?: string;
    sharedBuilderAppUuid?: string;
  };
  backups: {
    webhookUrl?: string;
  };
  stripe: {
    secretKey?: string;
    paidPriceId?: string;
  };
}

function env(name: string, fallback = ""): string {
  return process.env[name] || fallback;
}

function envBool(name: string, fallback = false): boolean {
  const value = process.env[name];
  if (value == null) {
    return fallback;
  }
  return ["1", "true", "yes", "on"].includes(value.toLowerCase());
}

export function loadConfig(): AppConfig {
  const nodeEnv = env("NODE_ENV", "development");
  const defaultPublishedRoot = path.resolve(process.cwd(), "published-sites");
  return {
    nodeEnv,
    port: Number(env("PORT", "8080")),
    corsOrigin: env("CORS_ORIGIN", "https://getaudo.com,http://localhost:8081,http://127.0.0.1:8081"),
    authMode: (env("AUTH_MODE", nodeEnv === "production" ? "firebase" : "preview") as AuthMode),
    storeMode: (env("STORE_MODE", nodeEnv === "production" ? "firestore" : "memory") as StoreMode),
    freeDomain: env("AUDO_FREE_DOMAIN", "getaudo.com"),
    publicBaseUrl: env("PUBLIC_BASE_URL", "https://getaudo.com"),
    publishedSiteRoot: env("PUBLISHED_SITE_ROOT", defaultPublishedRoot),
    cloudflare: {
      apiToken: env("CLOUDFLARE_API_TOKEN") || undefined,
      accountId: env("CLOUDFLARE_ACCOUNT_ID") || undefined,
      zoneId: env("CLOUDFLARE_ZONE_ID") || undefined,
      zoneName: env("CLOUDFLARE_ZONE_NAME", env("AUDO_FREE_DOMAIN", "getaudo.com")) || undefined,
      freeSiteTarget: env("CLOUDFLARE_FREE_SITE_TARGET") || undefined,
      originIpv4: env("CLOUDFLARE_ORIGIN_IPV4") || undefined,
      proxied: envBool("CLOUDFLARE_PROXIED", true)
    },
    coolify: {
      baseUrl: env("COOLIFY_BASE_URL") || undefined,
      apiToken: env("COOLIFY_API_TOKEN") || undefined,
      sharedBuilderAppUuid: env("COOLIFY_BUILDER_APP_UUID") || undefined
    },
    backups: {
      webhookUrl: env("BACKUP_WEBHOOK_URL") || undefined
    },
    stripe: {
      secretKey: env("STRIPE_SECRET_KEY") || undefined,
      paidPriceId: env("STRIPE_PAID_PRICE_ID") || undefined
    }
  };
}
