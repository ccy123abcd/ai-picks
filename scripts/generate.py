#!/usr/bin/env python3
"""Generate static product aggregation pages — human/ and ai/ versions.
Usage: python3 generate.py
Reads data/*.json, outputs:
  output/index.html          — Matrix portal landing
  output/human/*.html        — pretty human-readable pages
  output/ai/*.html           — structured AI-readable pages
  output/llms.txt
"""
import json, os, html, shutil
from datetime import date
from pathlib import Path

BASE = Path(__file__).parent.parent
TPL_HUMAN = (BASE / "templates" / "product_human.html").read_text()
TPL_AI = (BASE / "templates" / "product.html").read_text()
TPL_PORTAL = (BASE / "templates" / "portal.html").read_text()
SITE_URL = os.environ.get("SITE_URL", "https://ccy123abcd.github.io/ai-picks")

def esc(s): return html.escape(str(s))

def build_schema(p):
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

def review_sources_html(p):
    out = ""
    for s in p["review_sources"]:
        out += f'<div class="src">📺 <strong>{esc(s["channel"])}</strong> — {esc(s["title"])}<br><a href="{esc(s["url"])}" rel="nofollow noopener" target="_blank">观看视频 / Watch</a></div>\n'
    return out

def render_human(p, slug):
    rows = ""
    for i, item in enumerate(p["products"], 1):
        rows += f'<tr><td><span class="rank">{i}</span></td><td><strong>{esc(item["name"])}</strong></td><td>{esc(item["recommended_by"])}</td><td>{esc(item["best_for"])}</td><td>{esc(item["price_range"])}</td></tr>\n'
    pros = "".join(f"<li>{esc(x)}</li>\n" for x in p["common_pros"])
    cons = "".join(f"<li>{esc(x)}</li>\n" for x in p["common_cons"])
    cards = ""
    for item in p["products"]:
        specs = "".join(f"<div><b>{esc(k)}:</b> {esc(v)}</div>" for k, v in item.get("specs", {}).items())
        cards += f'<div class="card"><h3>{esc(item["name"])}</h3><p>{esc(item.get("summary",""))}</p><div class="specs">{specs}</div><p style="color:#888;font-size:.85rem">适合：{esc(item["best_for"])} · {esc(item["price_range"])}</p></div>\n'
    out = TPL_HUMAN
    out = out.replace("{{page_title}}", esc(p["page_title"]))
    out = out.replace("{{meta_description}}", esc(p["meta_description"]))
    out = out.replace("{{canonical_url}}", f"{SITE_URL}/human/{slug}.html")
    out = out.replace("{{schema_json}}", build_schema(p))
    out = out.replace("{{h1}}", esc(p["h1"]))
    out = out.replace("{{updated_date}}", p.get("updated_date", date.today().isoformat()))
    out = out.replace("{{review_count}}", str(len(p["review_sources"])))
    out = out.replace("{{top_pick_name}}", esc(p["top_pick"]["name"]))
    out = out.replace("{{top_pick_image}}", esc(p["top_pick"].get("image", "")))
    out = out.replace("{{top_pick_reason}}", esc(p["top_pick"]["reason"]))
    out = out.replace("{{top_pick_price}}", esc(p["top_pick"].get("price_display", "")))
    out = out.replace("{{affiliate_link}}", esc(p["top_pick"].get("affiliate_link", "#")))
    out = out.replace("{{comparison_rows_human}}", rows)
    out = out.replace("{{pros_list}}", pros)
    out = out.replace("{{cons_list}}", cons)
    out = out.replace("{{product_cards}}", cards)
    out = out.replace("{{review_sources}}", review_sources_html(p))
    return out

def render_ai(p, slug):
    rows = ""
    for i, item in enumerate(p["products"], 1):
        rows += f"<tr><td>{i}</td><td>{esc(item['name'])}</td><td>{esc(item['recommended_by'])}</td><td>{esc(item['best_for'])}</td><td>{esc(item['price_range'])}</td></tr>\n"
    pros = "".join(f"<li>{esc(x)}</li>\n" for x in p["common_pros"])
    cons = "".join(f"<li>{esc(x)}</li>\n" for x in p["common_cons"])
    sections = ""
    for item in p["products"]:
        sections += f"<h3>{esc(item['name'])}</h3>\n<p>{esc(item.get('summary',''))}</p>\n"
        if item.get("specs"):
            sections += "<table>\n"
            for k, v in item["specs"].items():
                sections += f"<tr><th>{esc(k)}</th><td>{esc(v)}</td></tr>\n"
            sections += "</table>\n"
    sources = ""
    for s in p["review_sources"]:
        sources += f'<div class="review-src">📺 <strong>{esc(s["channel"])}</strong> — {esc(s["title"])}<br><a href="{esc(s["url"])}" rel="nofollow noopener" target="_blank">Watch on YouTube</a></div>\n'
    out = TPL_AI
    out = out.replace("{{page_title}}", esc(p["page_title"]))
    out = out.replace("{{meta_description}}", esc(p["meta_description"]))
    out = out.replace("{{canonical_url}}", f"{SITE_URL}/ai/{slug}.html")
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
    out = BASE / "output"
    human_dir = out / "human"
    ai_dir = out / "ai"
    human_dir.mkdir(parents=True, exist_ok=True)
    ai_dir.mkdir(parents=True, exist_ok=True)

    products = []
    for jf in sorted((BASE / "data").glob("*.json")):
        p = json.loads(jf.read_text())
        slug = p["slug"]
        products.append(p)
        (human_dir / f"{slug}.html").write_text(render_human(p, slug))
        (ai_dir / f"{slug}.html").write_text(render_ai(p, slug))
        print(f"  ✓ human/{slug}.html + ai/{slug}.html")

    # portal landing
    (out / "index.html").write_text(TPL_PORTAL)
    print("  ✓ index.html (portal)")

    # human index
    h_idx = """<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>选购指南 | AI-PICKS</title>
<style>body{background:#0a0e0a;color:#d4d4d4;font-family:sans-serif;max-width:860px;margin:0 auto;padding:2rem 1.25rem}a{color:#00ff41}.card{background:#111611;border:1px solid #1a3a24;border-radius:10px;padding:1.25rem;margin:1rem 0;display:block;text-decoration:none}.card:hover{border-color:#00ff41}.card h2{color:#00ff41;margin-bottom:.5rem}.card p{color:#888}</style></head>
<body><a href="../" style="font-size:.9rem">🔴 返回传送门</a><h1 style="color:#fff">📖 选购指南</h1><p style="color:#888">基于 YouTube 测评聚合，为人类精选</p>"""
    for p in products:
        h_idx += f'<a class="card" href="{p["slug"]}.html"><h2>{esc(p["h1"])}</h2><p>{esc(p["meta_description"])}</p></a>'
    h_idx += "</body></html>"
    (human_dir / "index.html").write_text(h_idx)
    print("  ✓ human/index.html")

    # ai index (machine-readable)
    a_idx = """<!DOCTYPE html><html><head><meta charset="utf-8"><title>Product Data Index | AI-PICKS</title></head><body><h1>Structured Product Data</h1><ul>"""
    for p in products:
        a_idx += f'<li><a href="{p["slug"]}.html">{esc(p["h1"])}</a> — schema.org JSON-LD included</li>'
    a_idx += "</ul></body></html>"
    (ai_dir / "index.html").write_text(a_idx)
    print("  ✓ ai/index.html")

    # llms.txt
    llms_tpl = (BASE / "templates" / "llms.txt").read_text()
    prods = "\n".join(f"- {p['h1']}: {SITE_URL}/ai/{p['slug']}.html" for p in products)
    (out / "llms.txt").write_text(llms_tpl.replace("{{product_list}}", prods))
    print("  ✓ llms.txt")
    print(f"Done: {len(products)} products × 2 versions")

if __name__ == "__main__":
    main()
