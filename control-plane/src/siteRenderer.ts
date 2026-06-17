import fs from "node:fs/promises";
import path from "node:path";
import type { BuilderComponent, BuilderDocument, SiteRecord } from "./types.js";

function escapeHtml(value: unknown): string {
  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function splitItems(value?: string): string[] {
  return String(value || "")
    .split("|")
    .map((item) => item.trim())
    .filter(Boolean);
}

function renderComponent(component: BuilderComponent): string {
  const headline = escapeHtml(component.headline || component.brand || component.label || "Section");
  const body = escapeHtml(component.body || "");
  const items = splitItems(component.items);
  const links = splitItems(component.links);
  switch (component.type) {
    case "nav":
      return `<nav class="nav"><strong>${escapeHtml(component.brand || "Website")}</strong><span>${links.map(escapeHtml).join(" · ")}</span></nav>`;
    case "hero":
      return `<header class="hero"><h1>${headline}</h1><p>${body}</p><a href="#contact">${escapeHtml(component.button || "Get started")}</a></header>`;
    case "features":
    case "services":
    case "testimonials":
    case "pricing":
    case "faq":
      return `<section><h2>${headline}</h2><div class="grid">${items.map((item) => `<article><h3>${escapeHtml(item.split(" - ")[0])}</h3><p>${escapeHtml(item.includes(" - ") ? item.split(" - ").slice(1).join(" - ") : "Ready to edit.")}</p></article>`).join("")}</div></section>`;
    case "gallery":
      return `<section><h2>${headline}</h2><div class="gallery"><div></div><div></div><div></div></div></section>`;
    case "contact":
      return `<section id="contact"><h2>${headline}</h2><p>${body}</p><form><input placeholder="Name"><input placeholder="Email"><textarea placeholder="Message"></textarea><button type="button">Send</button></form></section>`;
    case "map":
    case "booking":
      return `<section><h2>${headline}</h2><p>${body}</p><div class="embed"></div></section>`;
    case "footer":
      return `<footer><strong>${escapeHtml(component.brand || "Website")}</strong><p>${body}</p></footer>`;
    default:
      return `<section><h2>${headline}</h2><p>${body}</p></section>`;
  }
}

export function renderSiteHtml(site: SiteRecord): string {
  const ad = site.plan === "free" ? `<div class="ad">Created with Audo free hosting</div>` : "";
  const components = site.builder.components.map(renderComponent).join("\n");
  return `<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>${escapeHtml(site.name)}</title>
  <meta name="description" content="${escapeHtml(site.name)} hosted by Audo.">
  <style>
    *{box-sizing:border-box}body{margin:0;font-family:Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;color:#17211d;background:#fff;letter-spacing:0}.ad{min-height:34px;display:flex;align-items:center;justify-content:center;background:#101815;color:#eff8f2;font-size:13px;font-weight:740}.nav{height:64px;display:flex;align-items:center;justify-content:space-between;padding:0 min(48px,7vw);border-bottom:1px solid #e7eee9}.nav strong{font-size:20px}.nav span{color:#65716a;font-size:14px}.hero{min-height:390px;display:grid;align-content:center;padding:48px min(56px,7vw);background:linear-gradient(120deg,#fafffc,#eef5ff)}.hero h1{max-width:780px;margin:0 0 18px;font-size:clamp(42px,8vw,80px);line-height:.98}.hero p{max-width:640px;margin:0 0 24px;color:#425048;font-size:19px;line-height:1.55}.hero a,button{min-height:42px;display:inline-flex;width:fit-content;align-items:center;justify-content:center;border:0;border-radius:8px;background:#129766;color:#fff;text-decoration:none;font-weight:760;padding:0 16px}section,footer{padding:40px min(56px,7vw);border-bottom:1px solid #edf1ef}h2{font-size:clamp(28px,4vw,44px);line-height:1.06;margin:0 0 20px}.grid,.gallery{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px}article{border:1px solid #e0e7e3;border-radius:8px;padding:18px;min-height:145px}.gallery div,.embed{min-height:160px;border-radius:8px;background:linear-gradient(135deg,#e6f3ec,#e7edf9);border:1px solid #dce6df}form{display:grid;gap:10px;max-width:540px}input,textarea{width:100%;border:1px solid #ccd8d0;border-radius:8px;padding:10px;min-height:42px}textarea{min-height:92px}@media(max-width:760px){.grid,.gallery{grid-template-columns:1fr}.nav{align-items:flex-start;height:auto;min-height:64px;flex-direction:column;justify-content:center;gap:4px}}
  </style>
</head>
<body>
${ad}
${components}
</body>
</html>`;
}

export function defaultBuilderDocument(template = "service"): BuilderDocument {
  const templates: Record<string, { hero: string[]; features: string; services: string }> = {
    service: {
      hero: ["Launch a polished service website", "A clean one-page site with proof, services, and contact paths ready for customers.", "Request a quote"],
      features: "Fast setup|Mobile-ready pages|Clear contact paths",
      services: "Consulting|Implementation|Support"
    },
    portfolio: {
      hero: ["Show the work without clutter", "A refined portfolio for projects, proof, testimonials, and direct inquiries.", "View work"],
      features: "Direction|Design|Delivery",
      services: "Brand systems|Websites|Campaigns"
    },
    restaurant: {
      hero: ["A better front door for your restaurant", "Menu highlights, hours, reservations, location, and contact in one simple page.", "Reserve a table"],
      features: "Hours|Menu|Reservations",
      services: "Dinner|Drinks|Private events"
    },
    saas: {
      hero: ["Turn product interest into demos", "A sharp product page with feature sections, pricing, proof, FAQ, and conversion paths.", "Book a demo"],
      features: "Dashboard|Automation|Reporting",
      services: "Operations|Sales|Leadership"
    }
  };
  const selected = templates[template] || templates.service;
  return {
    version: 1,
    components: [
      { id: "nav", type: "nav", label: "Navigation", brand: "Audo site", links: "Services|Proof|Contact" },
      { id: "hero", type: "hero", label: "Hero", headline: selected.hero[0], body: selected.hero[1], button: selected.hero[2] },
      { id: "features", type: "features", label: "Feature grid", headline: "What customers need", items: selected.features },
      { id: "services", type: "services", label: "Services", headline: "Services", items: selected.services },
      { id: "contact", type: "contact", label: "Contact form", headline: "Start the conversation", body: "Tell us what you need and we will respond soon." },
      { id: "footer", type: "footer", label: "Footer", brand: "Audo site", body: "Built and hosted on Audo." }
    ]
  };
}

export async function writePublishedSite(root: string, site: SiteRecord): Promise<string> {
  const siteDir = path.join(root, site.slug);
  await fs.mkdir(siteDir, { recursive: true });
  const output = path.join(siteDir, "index.html");
  await fs.writeFile(output, renderSiteHtml(site), "utf8");
  return output;
}
