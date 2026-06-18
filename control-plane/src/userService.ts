import { getAuth } from "firebase-admin/auth";
import { Firestore, getFirestore } from "firebase-admin/firestore";
import crypto from "node:crypto";
import type { AppConfig } from "./config.js";
import { badRequest, forbidden, notFound } from "./errors.js";
import { initFirebaseAdmin } from "./firebaseAdmin.js";
import type { AuthUser, ManagedUser } from "./types.js";

export interface CreateManagedUserInput {
  email: string;
  password: string;
  name?: string;
  role?: AuthUser["role"];
}

export interface UpdateManagedUserInput {
  name?: string;
  role?: AuthUser["role"];
  disabled?: boolean;
}

function now(): string {
  return new Date().toISOString();
}

function normalizeEmail(email: string): string {
  const value = email.trim().toLowerCase();
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)) {
    throw badRequest("Valid email is required.");
  }
  return value;
}

function normalizeRole(role?: AuthUser["role"]): AuthUser["role"] {
  return role === "admin" || role === "member" ? role : "member";
}

function requireManager(user: AuthUser): void {
  if (user.role !== "owner" && user.role !== "admin") {
    throw forbidden("Owner or admin role required.");
  }
}

export class UserService {
  private db?: Firestore;
  private previewUsers = new Map<string, ManagedUser>();

  constructor(private config: AppConfig) {
    if (this.usesFirebase()) {
      initFirebaseAdmin();
      this.db = getFirestore();
    }
  }

  async ensureCurrentUser(user: AuthUser): Promise<ManagedUser> {
    const timestamp = now();
    const managed: ManagedUser = {
      uid: user.uid,
      email: user.email,
      name: user.name,
      teamId: user.teamId,
      role: user.role,
      disabled: false,
      createdAt: timestamp,
      updatedAt: timestamp,
      lastSeenAt: timestamp
    };

    if (!this.usesFirebase()) {
      const existing = this.previewUsers.get(user.uid);
      const next = { ...managed, ...(existing || {}), lastSeenAt: timestamp, updatedAt: timestamp };
      this.previewUsers.set(user.uid, next);
      return next;
    }

    const teamRef = this.db!.collection("teams").doc(user.teamId);
    const memberRef = teamRef.collection("users").doc(user.uid);
    const profileRef = this.db!.collection("userProfiles").doc(user.uid);
    await this.db!.runTransaction(async (transaction) => {
      const memberDoc = await transaction.get(memberRef);
      const existing = memberDoc.exists ? (memberDoc.data() as ManagedUser) : null;
      const next = {
        ...managed,
        ...(existing || {}),
        email: user.email || existing?.email,
        name: user.name || existing?.name,
        role: existing?.role || user.role,
        lastSeenAt: timestamp,
        updatedAt: timestamp
      };
      transaction.set(teamRef, {
        id: user.teamId,
        ownerUid: existing?.role === "owner" ? existing.uid : user.role === "owner" ? user.uid : undefined,
        updatedAt: timestamp,
        createdAt: existing?.createdAt || timestamp
      }, { merge: true });
      transaction.set(memberRef, next, { merge: true });
      transaction.set(profileRef, next, { merge: true });
    });
    const saved = await memberRef.get();
    return saved.data() as ManagedUser;
  }

  async listUsers(actor: AuthUser): Promise<ManagedUser[]> {
    requireManager(actor);
    await this.ensureCurrentUser(actor);
    if (!this.usesFirebase()) {
      return [...this.previewUsers.values()]
        .filter((user) => user.teamId === actor.teamId)
        .sort((a, b) => a.email?.localeCompare(b.email || "") || 0);
    }
    const snap = await this.db!.collection("teams").doc(actor.teamId).collection("users").orderBy("createdAt", "asc").get();
    return snap.docs.map((doc) => doc.data() as ManagedUser);
  }

  async createUser(actor: AuthUser, input: CreateManagedUserInput): Promise<ManagedUser> {
    requireManager(actor);
    const email = normalizeEmail(input.email);
    if (!input.password || input.password.length < 8) {
      throw badRequest("Password must be at least 8 characters.");
    }
    const role = normalizeRole(input.role);
    const timestamp = now();

    if (!this.usesFirebase()) {
      const uid = `preview_${crypto.randomUUID()}`;
      const user: ManagedUser = {
        uid,
        email,
        name: input.name || email,
        teamId: actor.teamId,
        role,
        disabled: false,
        createdAt: timestamp,
        updatedAt: timestamp
      };
      this.previewUsers.set(uid, user);
      return user;
    }

    const auth = getAuth();
    const record = await auth.createUser({
      email,
      password: input.password,
      displayName: input.name || email,
      disabled: false,
      emailVerified: false
    });
    await auth.setCustomUserClaims(record.uid, { teamId: actor.teamId, role });
    const managed: ManagedUser = {
      uid: record.uid,
      email,
      name: input.name || email,
      teamId: actor.teamId,
      role,
      disabled: false,
      createdAt: timestamp,
      updatedAt: timestamp
    };
    await this.writeUser(managed);
    return managed;
  }

  async updateUser(actor: AuthUser, uid: string, input: UpdateManagedUserInput): Promise<ManagedUser> {
    requireManager(actor);
    const existing = await this.getTeamUser(actor.teamId, uid);
    if (!existing) {
      throw notFound("User not found");
    }
    if (existing.role === "owner" && actor.uid !== uid && input.role && input.role !== "owner") {
      throw forbidden("Only an owner can change their own owner role.");
    }
    const updated: ManagedUser = {
      ...existing,
      name: input.name ?? existing.name,
      role: input.role ? normalizeRole(input.role) : existing.role,
      disabled: input.disabled ?? existing.disabled,
      updatedAt: now()
    };

    if (!this.usesFirebase()) {
      this.previewUsers.set(uid, updated);
      return updated;
    }

    await getAuth().updateUser(uid, {
      displayName: updated.name,
      disabled: updated.disabled
    });
    await getAuth().setCustomUserClaims(uid, { teamId: actor.teamId, role: updated.role });
    await this.writeUser(updated);
    return updated;
  }

  private usesFirebase(): boolean {
    return this.config.authMode === "firebase" && this.config.storeMode === "firestore";
  }

  private async getTeamUser(teamId: string, uid: string): Promise<ManagedUser | null> {
    if (!this.usesFirebase()) {
      const user = this.previewUsers.get(uid);
      return user && user.teamId === teamId ? user : null;
    }
    const doc = await this.db!.collection("teams").doc(teamId).collection("users").doc(uid).get();
    return doc.exists ? (doc.data() as ManagedUser) : null;
  }

  private async writeUser(user: ManagedUser): Promise<void> {
    await Promise.all([
      this.db!.collection("teams").doc(user.teamId).collection("users").doc(user.uid).set(user, { merge: true }),
      this.db!.collection("userProfiles").doc(user.uid).set(user, { merge: true })
    ]);
  }
}
