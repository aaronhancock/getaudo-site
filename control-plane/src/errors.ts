export class HttpError extends Error {
  constructor(
    public status: number,
    message: string,
    public code = "http_error",
    public details?: Record<string, unknown>
  ) {
    super(message);
  }
}

export function badRequest(message: string, details?: Record<string, unknown>): HttpError {
  return new HttpError(400, message, "bad_request", details);
}

export function unauthorized(message = "Authentication required"): HttpError {
  return new HttpError(401, message, "unauthorized");
}

export function forbidden(message = "Forbidden"): HttpError {
  return new HttpError(403, message, "forbidden");
}

export function notFound(message = "Not found"): HttpError {
  return new HttpError(404, message, "not_found");
}

export function conflict(message: string, details?: Record<string, unknown>): HttpError {
  return new HttpError(409, message, "conflict", details);
}

export function paymentRequired(message = "Paid plan required"): HttpError {
  return new HttpError(402, message, "payment_required");
}
