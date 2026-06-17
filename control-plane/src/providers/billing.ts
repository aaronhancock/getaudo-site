import type { AppConfig } from "../config.js";
import type { BillingProvider, SiteRecord } from "../types.js";

export class StripeBillingProvider implements BillingProvider {
  constructor(private config: AppConfig["stripe"], private publicBaseUrl: string) {}

  async createCheckout(params: {
    site: SiteRecord;
    plan: "paid";
    successUrl?: string;
    cancelUrl?: string;
  }): Promise<{ url: string; mode: "stripe" | "preview" }> {
    if (!this.config.secretKey || !this.config.paidPriceId) {
      const site = encodeURIComponent(params.site.id);
      return {
        url: `${this.publicBaseUrl.replace(/\/+$/, "")}/app?checkout=preview&site=${site}`,
        mode: "preview"
      };
    }

    const body = new URLSearchParams({
      mode: "subscription",
      "line_items[0][price]": this.config.paidPriceId,
      "line_items[0][quantity]": "1",
      success_url: params.successUrl || `${this.publicBaseUrl.replace(/\/+$/, "")}/app?checkout=success`,
      cancel_url: params.cancelUrl || `${this.publicBaseUrl.replace(/\/+$/, "")}/app?checkout=cancelled`,
      client_reference_id: params.site.id,
      "metadata[siteId]": params.site.id,
      "metadata[teamId]": params.site.teamId
    });

    const response = await fetch("https://api.stripe.com/v1/checkout/sessions", {
      method: "POST",
      headers: {
        authorization: `Bearer ${this.config.secretKey}`,
        "content-type": "application/x-www-form-urlencoded"
      },
      body
    });
    const data = await response.json().catch(() => ({}));
    if (!response.ok || !data.url) {
      throw new Error(`Stripe checkout failed: ${response.status} ${JSON.stringify(data)}`);
    }
    return { url: data.url, mode: "stripe" };
  }
}
