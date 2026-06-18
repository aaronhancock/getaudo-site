import cors from "cors";
import express, { type NextFunction, type Request, type Response } from "express";
import fs from "node:fs/promises";
import helmet from "helmet";
import path from "node:path";
import { z } from "zod";
import { authMiddleware, requireUser } from "./auth.js";
import type { AppConfig } from "./config.js";
import { HttpError, badRequest, notFound } from "./errors.js";
import { WebhookBackupProvider } from "./providers/backups.js";
import { StripeBillingProvider } from "./providers/billing.js";
import { CloudflareDnsProvider } from "./providers/cloudflare.js";
import { CoolifyApiProvider } from "./providers/coolify.js";
import { FirestoreSiteStore, MemorySiteStore } from "./store.js";
import { SiteService } from "./siteService.js";
import type { AppServices } from "./types.js";
import { UserService } from "./userService.js";

const createSiteSchema = z.object({
  name: z.string().min(1),
  plan: z.enum(["free", "paid"]).optional(),
  platform: z.enum(["builder", "wordpress"]).optional(),
  template: z.string().optional(),
  builder: z.any().optional()
});

const updateSiteSchema = z.object({
  name: z.string().min(1).optional(),
  builder: z.any().optional()
});

const customDomainSchema = z.object({
  host: z.string().min(1)
});

const githubSchema = z.object({
  installationId: z.string().optional(),
  owner: z.string().min(1),
  repo: z.string().min(1),
  branch: z.string().optional(),
  buildCommand: z.string().optional(),
  outputDirectory: z.string().optional()
});

const checkoutSchema = z.object({
  successUrl: z.string().url().optional(),
  cancelUrl: z.string().url().optional()
});

const createUserSchema = z.object({
  email: z.string().email(),
  password: z.string().min(8),
  name: z.string().optional(),
  role: z.enum(["admin", "member"]).optional()
});

const updateUserSchema = z.object({
  name: z.string().optional(),
  role: z.enum(["admin", "member"]).optional(),
  disabled: z.boolean().optional()
});

function asyncRoute(handler: (request: Request, response: Response) => Promise<void>) {
  return (request: Request, response: Response, next: NextFunction) => {
    handler(request, response).catch(next);
  };
}

function parse<T>(schema: z.ZodSchema<T>, value: unknown): T {
  const result = schema.safeParse(value);
  if (!result.success) {
    throw badRequest("Invalid request body.", { issues: result.error.issues });
  }
  return result.data;
}

function createDefaultServices(config: AppConfig): AppServices {
  const store = config.storeMode === "firestore" ? new FirestoreSiteStore() : new MemorySiteStore();
  return {
    store,
    cloudflare: new CloudflareDnsProvider(config.cloudflare, config.freeDomain),
    coolify: new CoolifyApiProvider(config.coolify),
    backups: new WebhookBackupProvider(config.backups),
    billing: new StripeBillingProvider(config.stripe, config.publicBaseUrl)
  };
}

export function createApp(config: AppConfig, services = createDefaultServices(config)): express.Express {
  const app = express();
  const service = new SiteService(config, services);
  const users = new UserService(config);
  const corsOrigins = config.corsOrigin.split(",").map((origin) => origin.trim()).filter(Boolean);

  app.use(helmet({ crossOriginResourcePolicy: false }));
  app.use(cors({ origin: corsOrigins.length ? corsOrigins : true, credentials: true }));
  app.use(express.json({ limit: "1mb" }));

  app.get("/health", (_request, response) => {
    response.json({ ok: true, service: "audo-control-plane" });
  });

  app.use("/api", authMiddleware(config));

  app.get("/api/me", asyncRoute(async (request, response) => {
    const user = requireUser(request);
    response.json({ user, profile: await users.ensureCurrentUser(user) });
  }));

  app.get("/api/users/me", asyncRoute(async (request, response) => {
    response.json({ user: await users.ensureCurrentUser(requireUser(request)) });
  }));

  app.get("/api/users", asyncRoute(async (request, response) => {
    response.json({ users: await users.listUsers(requireUser(request)) });
  }));

  app.post("/api/users", asyncRoute(async (request, response) => {
    response.status(201).json({ user: await users.createUser(requireUser(request), parse(createUserSchema, request.body)) });
  }));

  app.patch("/api/users/:uid", asyncRoute(async (request, response) => {
    response.json({ user: await users.updateUser(requireUser(request), request.params.uid, parse(updateUserSchema, request.body)) });
  }));

  app.get("/api/dns/cloudflare/status", asyncRoute(async (_request, response) => {
    response.json({ cloudflare: await services.cloudflare.verifyConnection() });
  }));

  app.get("/api/sites", asyncRoute(async (request, response) => {
    response.json({ sites: await service.listSites(requireUser(request)) });
  }));

  app.post("/api/sites", asyncRoute(async (request, response) => {
    const site = await service.createSite(requireUser(request), parse(createSiteSchema, request.body));
    response.status(201).json({ site });
  }));

  app.get("/api/sites/:siteId", asyncRoute(async (request, response) => {
    response.json({ site: await service.getSite(requireUser(request), request.params.siteId) });
  }));

  app.patch("/api/sites/:siteId", asyncRoute(async (request, response) => {
    response.json({ site: await service.updateSite(requireUser(request), request.params.siteId, parse(updateSiteSchema, request.body)) });
  }));

  app.post("/api/sites/:siteId/dns/free-subdomain", asyncRoute(async (request, response) => {
    response.json({ site: await service.provisionFreeDomain(requireUser(request), request.params.siteId) });
  }));

  app.post("/api/sites/:siteId/domains", asyncRoute(async (request, response) => {
    const body = parse(customDomainSchema, request.body);
    response.status(201).json({ site: await service.addCustomDomain(requireUser(request), request.params.siteId, body.host) });
  }));

  app.post("/api/sites/:siteId/publish", asyncRoute(async (request, response) => {
    const commit = typeof request.body?.commit === "string" ? request.body.commit : undefined;
    response.json({ site: await service.publishSite(requireUser(request), request.params.siteId, commit) });
  }));

  app.post("/api/sites/:siteId/github", asyncRoute(async (request, response) => {
    response.json({ site: await service.connectGitHub(requireUser(request), request.params.siteId, parse(githubSchema, request.body)) });
  }));

  app.post("/api/sites/:siteId/backups", asyncRoute(async (request, response) => {
    response.status(202).json({ site: await service.requestBackup(requireUser(request), request.params.siteId) });
  }));

  app.post("/api/sites/:siteId/checkout", asyncRoute(async (request, response) => {
    const body = parse(checkoutSchema, request.body || {});
    response.json(await service.createCheckout(requireUser(request), request.params.siteId, body.successUrl, body.cancelUrl));
  }));

  app.get("/api/sites/:siteId/events", asyncRoute(async (request, response) => {
    response.json({ events: await service.listEvents(requireUser(request), request.params.siteId) });
  }));

  app.get("*", asyncRoute(async (request, response) => {
    const host = String(request.headers["x-forwarded-host"] || request.headers.host || "").split(",")[0];
    const site = await service.getPublishedFreeSiteByHost(host);
    if (!site) {
      throw notFound();
    }
    const artifactPath = path.join(config.publishedSiteRoot, site.slug, "index.html");
    try {
      const html = await fs.readFile(artifactPath, "utf8");
      response.type("html").send(html);
    } catch {
      throw notFound("Published site not found");
    }
  }));

  app.use((_request, _response, next) => next(notFound()));
  app.use((error: unknown, _request: Request, response: Response, _next: NextFunction) => {
    if (error instanceof HttpError) {
      response.status(error.status).json({ error: { code: error.code, message: error.message, details: error.details } });
      return;
    }
    const message = error instanceof Error ? error.message : "Unexpected error";
    response.status(500).json({ error: { code: "internal_error", message } });
  });

  return app;
}
