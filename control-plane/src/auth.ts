import type { NextFunction, Request, Response } from "express";
import { getApps, initializeApp, cert, applicationDefault } from "firebase-admin/app";
import { getAuth } from "firebase-admin/auth";
import type { AppConfig } from "./config.js";
import type { AuthUser } from "./types.js";
import { unauthorized } from "./errors.js";

declare global {
  namespace Express {
    interface Request {
      user?: AuthUser;
    }
  }
}

function initFirebaseAdmin(): void {
  if (getApps().length) {
    return;
  }
  const raw = process.env.FIREBASE_SERVICE_ACCOUNT_JSON;
  if (raw) {
    initializeApp({ credential: cert(JSON.parse(raw)) });
    return;
  }
  initializeApp({ credential: applicationDefault() });
}

function previewUser(request: Request): AuthUser {
  const uid = String(request.header("x-audo-preview-user") || "preview");
  return {
    uid,
    email: `${uid}@preview.getaudo.com`,
    name: "Preview user",
    teamId: String(request.header("x-audo-team-id") || `team_${uid}`),
    role: "owner"
  };
}

export function authMiddleware(config: AppConfig) {
  if (config.authMode === "firebase") {
    initFirebaseAdmin();
  }

  return async (request: Request, _response: Response, next: NextFunction) => {
    try {
      if (config.authMode === "preview") {
        if (config.previewApiSecret && request.header("x-audo-preview-secret") !== config.previewApiSecret) {
          throw unauthorized();
        }
        request.user = previewUser(request);
        return next();
      }

      const header = request.header("authorization") || "";
      const match = header.match(/^Bearer\s+(.+)$/i);
      if (!match) {
        throw unauthorized();
      }
      const decoded = await getAuth().verifyIdToken(match[1]);
      const teamIds = Array.isArray(decoded.teamIds) ? decoded.teamIds : [];
      request.user = {
        uid: decoded.uid,
        email: decoded.email,
        name: decoded.name || decoded.email,
        teamId: String(teamIds[0] || decoded.teamId || `team_${decoded.uid}`),
        role: decoded.role === "admin" || decoded.role === "member" ? decoded.role : "owner"
      };
      next();
    } catch (error) {
      next(error);
    }
  };
}

export function requireUser(request: Request): AuthUser {
  if (!request.user) {
    throw unauthorized();
  }
  return request.user;
}
