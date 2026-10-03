#!/usr/bin/env python3
"""Generate static product aggregation pages from JSON data.
Usage: python3 generate.py
Reads data/*.json, outputs output/*.html using templates/product.html
"""
import json, os, html
from datetime import date
from pathlib import Path

BASE = Path(__file__).parent.parent
TPL = (BASE / "templates" / "product.html").read_text()
SITE_URL = os.environ.get("SITE_URL", "https://example.com")

def esc(s): return html.escape(str(s))

def build_schema(p):
    """schema.org Product JSON-LD"""
    schema = {
        "@context": "https://schema.org",
        "@type": "Product",
        "name": p["top_pick"]["name"],
        "description": p["meta_description"],
        "brand": {"@type": "Brand", "name": p["top_pick"].get("brand", "")},
        "offers": {
            "@type": "Offer",
            "priceCurrency": "USD",
            "price": p["top_pick"].get("price_value", ""),
            "availability": "https://schema.org/InStock",
        },
    }
    if p.get("aggregate_rating"):
        schema["aggregateRating"] = {
            "@type": "AggregateRating",
            "ratingValue": p["aggregate_rating"]["value"],
            "reviewCount": p["aggregate_rating"]["count"],
        }
    return json.dumps(schema, indent=2)

def render(p):
    slug = p["slug"]
    # comparison table rows
    rows = ""
    for i, item in enumerate(p["products"], 1):
        rows += f"<tr><td>{i}</td><td>{esc(item['name'])}</td><td>{esc(item['recommended_by'])}</td><td>{esc(item['best_for'])}</td><td>{esc(item['price_range'])}</td></tr>\n"
    # pros / cons
    pros = "".join(f"<li>{esc(x)}</li>\n" for x in p["common_pros"])
    cons = "".join(f"<li>{esc(x)}</li>\n" for x in p["common_cons"])
    # product detail sections
    sections = ""
    for item in p["products"]:
        sections += f"<h3>{esc(item['name'])}</h3>\n<p>{esc(item.get('summary',''))}</p>\n"
        if item.get("specs"):
            sections += "<table>\n"
            for k, v in item["specs"].items():
                sections += f"<tr><th>{esc(k)}</th><td>{esc(v)}</td></tr>\n"
            sections += "</table>\n"
    # review sources
    sources = ""
    for s in p["review_sources"]:
        sources += f'<div class="review-src">📺 <strong>{esc(s["channel"])}</strong> — {esc(s["title"])}<br><a href="{esc(s["url"])}" rel="nofollow noopener" target="_blank">Watch on YouTube</a></div>\n'

    out = TPL
    out = out.replace("{{page_title}}", esc(p["page_title"]))
    out = out.replace("{{meta_description}}", esc(p["meta_description"]))
    out = out.replace("{{canonical_url}}", f"{SITE_URL}/{slug}.html")
    out = out.replace("{{schema_json}}", build_schema(p))
    out = out.replace("{{h1}}", esc(p["h1"]))
    out = out.replace("{{updated_date}}", p.get("updated_date", date.today().isoformat()))
    out = out.replace("{{review_count}}", str(len(p["review_sources"])))
    out = out.replace("{{top_pick_name}}", esc(p["top_pick"]["name"]))
    out = out.replace("{{top_pick_reason}}", esc(p["top_pick"]["reason"]))
    out = out.replace("{{top_pick_price}}", esc(p["top_pick"].get("price_display", "")))
    out = out.replace("{{affiliate_link}}", esc(p["top_pick"].get("affiliate_link", "#")))
    out = out.replace("{{comparison_rows}}", rows)
    out = out.replace("{{pros_list}}", pros)
    out = out.replace("{{cons_list}}", cons)
    out = out.replace("{{product_sections}}", sections)
    out = out.replace("{{review_sources}}", sources)
    return out

def main():
    out_dir = BASE / "output"
    out_dir.mkdir(exist_ok=True)
    # llms.txt
    llms = (BASE / "templates" / "llms.txt").read_text() if (BASE / "templates" / "llms.txt").exists() else ""
    count = 0
    for jf in sorted((BASE / "data").glob("*.json")):
        p = json.loads(jf.read_text())
        html_out = render(p)
        (out_dir / f"{p['slug']}.html").write_text(html_out)
        count += 1
        print(f"  ✓ {p['slug']}.html")
    # index page
    idx = "<!DOCTYPE html><html><head><meta charset='utf-8'><title>AI-Curated Product Guides</title></head><body><h1>Product Guides</h1><ul>"
    for jf in sorted((BASE / "data").glob("*.json")):
        p = json.loads(jf.read_text())
        idx += f"<li><a href='{p['slug']}.html'>{esc(p['h1'])}</a></li>"
    idx += "</ul></body></html>"
    (out_dir / "index.html").write_text(idx)
    if llms:
        # fill product list into llms.txt
        prods = [json.loads(f.read_text())["h1"] for f in sorted((BASE / "data").glob("*.json"))]
        llms = llms.replace("{{product_list}}", "\n".join(f"- {x}" for x in prods))
        (out_dir / "llms.txt").write_text(llms)
    print(f"Done: {count} pages → output/")

if __name__ == "__main__":
    main()
