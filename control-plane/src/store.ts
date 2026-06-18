import { getFirestore, Firestore } from "firebase-admin/firestore";
import type { SiteEvent, SiteRecord, SiteStore } from "./types.js";
import { notFound } from "./errors.js";
import { initFirebaseAdmin } from "./firebaseAdmin.js";

function clone<T>(value: T): T {
  return JSON.parse(JSON.stringify(value)) as T;
}

function stripUndefined<T>(value: T): T {
  if (Array.isArray(value)) {
    return value.map((item) => stripUndefined(item)) as T;
  }
  if (value && typeof value === "object") {
    return Object.fromEntries(
      Object.entries(value)
        .filter(([, item]) => item !== undefined)
        .map(([key, item]) => [key, stripUndefined(item)])
    ) as T;
  }
  return value;
}

export class MemorySiteStore implements SiteStore {
  private sites = new Map<string, SiteRecord>();
  private events = new Map<string, SiteEvent[]>();

  async listSites(teamId: string): Promise<SiteRecord[]> {
    return [...this.sites.values()]
      .filter((site) => site.teamId === teamId && site.status !== "deleted")
      .sort((a, b) => b.createdAt.localeCompare(a.createdAt))
      .map(clone);
  }

  async getSite(teamId: string, siteId: string): Promise<SiteRecord | null> {
    const site = this.sites.get(siteId);
    return site && site.teamId === teamId && site.status !== "deleted" ? clone(site) : null;
  }

  async findSiteBySlug(slug: string): Promise<SiteRecord | null> {
    const site = [...this.sites.values()].find((item) => item.slug === slug && item.status !== "deleted");
    return site ? clone(site) : null;
  }

  async createSite(site: SiteRecord): Promise<SiteRecord> {
    this.sites.set(site.id, clone(site));
    return clone(site);
  }

  async updateSite(teamId: string, siteId: string, patch: Partial<SiteRecord>): Promise<SiteRecord> {
    const existing = this.sites.get(siteId);
    if (!existing || existing.teamId !== teamId) {
      throw notFound("Site not found");
    }
    const updated = { ...existing, ...clone(patch), id: existing.id, teamId: existing.teamId, updatedAt: new Date().toISOString() };
    this.sites.set(siteId, updated);
    return clone(updated);
  }

  async appendEvent(event: SiteEvent): Promise<SiteEvent> {
    const list = this.events.get(event.siteId) || [];
    list.unshift(clone(event));
    this.events.set(event.siteId, list.slice(0, 200));
    return clone(event);
  }

  async listEvents(teamId: string, siteId: string): Promise<SiteEvent[]> {
    const site = this.sites.get(siteId);
    if (!site || site.teamId !== teamId) {
      throw notFound("Site not found");
    }
    return (this.events.get(siteId) || []).map(clone);
  }
}

export class FirestoreSiteStore implements SiteStore {
  private db: Firestore;

  constructor() {
    initFirebaseAdmin();
    this.db = getFirestore();
  }

  async listSites(teamId: string): Promise<SiteRecord[]> {
    const snap = await this.db.collection("sites").where("teamId", "==", teamId).get();
    return snap.docs
      .map((doc) => doc.data() as SiteRecord)
      .filter((site) => site.status !== "deleted")
      .sort((a, b) => b.createdAt.localeCompare(a.createdAt));
  }

  async getSite(teamId: string, siteId: string): Promise<SiteRecord | null> {
    const doc = await this.db.collection("sites").doc(siteId).get();
    if (!doc.exists) {
      return null;
    }
    const site = doc.data() as SiteRecord;
    return site.teamId === teamId && site.status !== "deleted" ? site : null;
  }

  async findSiteBySlug(slug: string): Promise<SiteRecord | null> {
    const snap = await this.db.collection("sites").where("slug", "==", slug).limit(1).get();
    if (snap.empty) {
      return null;
    }
    const site = snap.docs[0].data() as SiteRecord;
    return site.status === "deleted" ? null : site;
  }

  async createSite(site: SiteRecord): Promise<SiteRecord> {
    await this.db.collection("sites").doc(site.id).set(stripUndefined(site));
    return site;
  }

  async updateSite(teamId: string, siteId: string, patch: Partial<SiteRecord>): Promise<SiteRecord> {
    const ref = this.db.collection("sites").doc(siteId);
    const updatedAt = new Date().toISOString();
    const result = await this.db.runTransaction(async (transaction) => {
      const doc = await transaction.get(ref);
      if (!doc.exists) {
        throw notFound("Site not found");
      }
      const existing = doc.data() as SiteRecord;
      if (existing.teamId !== teamId) {
        throw notFound("Site not found");
      }
      const updated = { ...existing, ...patch, id: existing.id, teamId: existing.teamId, updatedAt };
      transaction.set(ref, stripUndefined(updated));
      return updated;
    });
    return result;
  }

  async appendEvent(event: SiteEvent): Promise<SiteEvent> {
    const cleanEvent = stripUndefined(event);
    await this.db.collection("sites").doc(event.siteId).collection("events").doc(event.id).set(cleanEvent);
    await this.db.collection("siteEvents").doc(event.id).set(cleanEvent);
    return event;
  }

  async listEvents(teamId: string, siteId: string): Promise<SiteEvent[]> {
    const site = await this.getSite(teamId, siteId);
    if (!site) {
      throw notFound("Site not found");
    }
    const snap = await this.db.collection("sites").doc(siteId).collection("events").orderBy("createdAt", "desc").limit(100).get();
    return snap.docs.map((doc) => doc.data() as SiteEvent);
  }
}
