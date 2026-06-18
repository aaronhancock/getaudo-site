import fs from "node:fs/promises";
import path from "node:path";
import type { BuilderComponent, BuilderDesign, BuilderDocument, SiteRecord } from "./types.js";

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

function safeColor(value: unknown, fallback: string): string {
  const color = String(value || "").trim();
  return /^#[0-9a-fA-F]{3}(?:[0-9a-fA-F]{3})?$/.test(color) ? color : fallback;
}

function safeChoice<T extends string>(value: unknown, allowed: readonly T[], fallback: T): T {
  return allowed.includes(value as T) ? (value as T) : fallback;
}

function safeImageUrl(value?: string): string {
  const url = String(value || "").trim();
  return /^(https?:\/\/|\/)[^\s<>"']+$/i.test(url) ? url : "";
}

function fontStack(font?: BuilderDesign["font"]): string {
  switch (font) {
    case "serif":
      return 'ui-serif, Georgia, "Times New Roman", serif';
    case "mono":
      return '"SFMono-Regular", Consolas, "Liberation Mono", monospace';
    case "inter":
      return 'Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif';
    default:
      return 'ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif';
  }
}

function renderImage(imageUrl?: string, alt?: string): string {
  const safeUrl = safeImageUrl(imageUrl);
  if (!safeUrl) {
    return "";
  }
  return `<figure><img src="${escapeHtml(safeUrl)}" alt="${escapeHtml(alt || "")}"></figure>`;
}

function renderComponent(component: BuilderComponent, design: BuilderDesign = {}): string {
  const headline = escapeHtml(component.headline || component.brand || component.label || "Section");
  const body = escapeHtml(component.body || "");
  const items = splitItems(component.items);
  const links = splitItems(component.links);
  const image = renderImage(component.imageUrl || (component.type === "hero" ? design.heroImage : undefined), component.imageAlt || design.heroImageAlt);
  const layoutClass = `section-layout-${safeChoice(component.layout, ["default", "image-left", "image-right", "center"] as const, "default")}`;
  switch (component.type) {
    case "nav":
      return `<nav class="nav"><strong>${escapeHtml(component.brand || "Website")}</strong><span>${links.map(escapeHtml).join(" · ")}</span></nav>`;
    case "hero":
      return `<header class="hero ${layoutClass}"><div><h1>${headline}</h1><p>${body}</p><a href="#contact">${escapeHtml(component.button || "Get started")}</a></div>${image}</header>`;
    case "features":
    case "services":
    case "testimonials":
    case "pricing":
    case "faq":
      return `<section class="${layoutClass}"><h2>${headline}</h2>${image}<div class="grid">${items.map((item) => `<article><h3>${escapeHtml(item.split(" - ")[0])}</h3><p>${escapeHtml(item.includes(" - ") ? item.split(" - ").slice(1).join(" - ") : "Ready to edit.")}</p></article>`).join("")}</div></section>`;
    case "gallery":
      return `<section class="${layoutClass}"><h2>${headline}</h2><div class="gallery">${image || "<div></div>"}<div></div><div></div></div></section>`;
    case "contact":
      return `<section id="contact" class="${layoutClass}"><h2>${headline}</h2>${image}<p>${body}</p><form><input placeholder="Name"><input placeholder="Email"><textarea placeholder="Message"></textarea><button type="button">Send</button></form></section>`;
    case "map":
    case "booking":
      return `<section class="${layoutClass}"><h2>${headline}</h2>${image}<p>${body}</p><div class="embed"></div></section>`;
    case "footer":
      return `<footer><strong>${escapeHtml(component.brand || "Website")}</strong><p>${body}</p></footer>`;
    default:
      return `<section class="${layoutClass}"><h2>${headline}</h2>${image}<p>${body}</p></section>`;
  }
}

export function renderSiteHtml(site: SiteRecord): string {
  const ad = site.plan === "free" ? `<div class="ad">Created with Audo free hosting</div>` : "";
  const design = site.builder.design || {};
  const layout = safeChoice(design.layout, ["classic", "editorial", "compact"] as const, "classic");
  const primaryColor = safeColor(design.primaryColor, "#129766");
  const accentColor = safeColor(design.accentColor, "#406bff");
  const backgroundColor = safeColor(design.backgroundColor, "#ffffff");
  const textColor = safeColor(design.textColor, "#17211d");
  const components = site.builder.components
    .filter((component) => component.enabled !== false)
    .map((component) => renderComponent(component, design))
    .join("\n");
  return `<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>${escapeHtml(site.name)}</title>
  <meta name="description" content="${escapeHtml(site.name)} hosted by Audo.">
  <style>
    *{box-sizing:border-box}body{--primary:${primaryColor};--accent:${accentColor};--bg:${backgroundColor};--text:${textColor};margin:0;font-family:${fontStack(design.font)};color:var(--text);background:var(--bg);letter-spacing:0}.ad{min-height:34px;display:flex;align-items:center;justify-content:center;background:#101815;color:#eff8f2;font-size:13px;font-weight:740}.nav{height:64px;display:flex;align-items:center;justify-content:space-between;padding:0 min(48px,7vw);border-bottom:1px solid color-mix(in srgb,var(--text) 12%,transparent);background:color-mix(in srgb,var(--bg) 94%,white)}.nav strong{font-size:20px}.nav span{color:color-mix(in srgb,var(--text) 65%,transparent);font-size:14px}.hero{min-height:390px;display:grid;grid-template-columns:minmax(0,1fr);gap:28px;align-items:center;padding:48px min(56px,7vw);background:linear-gradient(120deg,color-mix(in srgb,var(--bg) 94%,white),color-mix(in srgb,var(--accent) 16%,var(--bg)))}.hero.section-layout-image-left,.hero.section-layout-image-right{grid-template-columns:minmax(0,1.05fr) minmax(240px,.7fr)}.hero.section-layout-image-left figure{order:-1}.hero h1{max-width:780px;margin:0 0 18px;font-size:clamp(42px,8vw,80px);line-height:.98}.hero p{max-width:640px;margin:0 0 24px;color:color-mix(in srgb,var(--text) 76%,transparent);font-size:19px;line-height:1.55}.hero a,button{min-height:42px;display:inline-flex;width:fit-content;align-items:center;justify-content:center;border:0;border-radius:8px;background:var(--primary);color:#fff;text-decoration:none;font-weight:760;padding:0 16px}section,footer{padding:40px min(56px,7vw);border-bottom:1px solid color-mix(in srgb,var(--text) 10%,transparent)}body[data-layout="editorial"] section:nth-of-type(even){background:color-mix(in srgb,var(--accent) 8%,var(--bg))}body[data-layout="compact"] section,body[data-layout="compact"] footer{padding-block:26px}h2{font-size:clamp(28px,4vw,44px);line-height:1.06;margin:0 0 20px}.grid,.gallery{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px}article{border:1px solid color-mix(in srgb,var(--text) 14%,transparent);border-radius:8px;padding:18px;min-height:145px;background:color-mix(in srgb,var(--bg) 96%,white)}figure{margin:0}img{display:block;width:100%;height:auto;border-radius:8px;object-fit:cover}.hero img{max-height:420px}.gallery figure,.gallery div,.embed{min-height:160px;border-radius:8px;background:linear-gradient(135deg,color-mix(in srgb,var(--primary) 14%,var(--bg)),color-mix(in srgb,var(--accent) 18%,var(--bg)));border:1px solid color-mix(in srgb,var(--text) 12%,transparent);overflow:hidden}.gallery img{height:100%;min-height:160px}.section-layout-center{text-align:center}.section-layout-center form{margin-inline:auto}form{display:grid;gap:10px;max-width:540px}input,textarea{width:100%;border:1px solid color-mix(in srgb,var(--text) 20%,transparent);border-radius:8px;padding:10px;min-height:42px}textarea{min-height:92px}@media(max-width:760px){.grid,.gallery,.hero.section-layout-image-left,.hero.section-layout-image-right{grid-template-columns:1fr}.nav{align-items:flex-start;height:auto;min-height:64px;flex-direction:column;justify-content:center;gap:4px}.hero.section-layout-image-left figure{order:0}}
  </style>
</head>
<body data-layout="${escapeHtml(layout)}">
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
    design: {
      font: "inter",
      primaryColor: "#129766",
      accentColor: "#406bff",
      backgroundColor: "#ffffff",
      textColor: "#17211d",
      layout: template === "portfolio" ? "editorial" : "classic"
    },
    components: [
      { id: "nav", type: "nav", label: "Navigation", brand: "Audo site", links: "Services|Proof|Contact" },
      { id: "hero", type: "hero", label: "Hero", headline: selected.hero[0], body: selected.hero[1], button: selected.hero[2], layout: "image-right" },
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
