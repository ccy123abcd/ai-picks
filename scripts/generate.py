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
        out += f'<div class="src">📺 <strong>{esc(s["channel"])}</strong> — {esc(s["title"])}<br><a href="{esc(s["url"])}" rel="nofollow noopener" target="_blank">Watch Video</a></div>\n'
    return out


def gen_faq_html(p):
    """从 top_pick 规格生成 FAQ，覆盖用户常搜的参数问题"""
    tp = p["top_pick"]
    specs = tp.get("specs", {})
    name = esc(tp["name"])
    faqs = []
    # 尺寸问题
    for k in specs:
        if any(w in k.lower() for w in ["panel", "size", "screen", "display"]):
            faqs.append((f"What size is the {name}?",
                        f"The {name} features a {esc(specs[k])} panel."))
            break
    # 刷新率问题
    for k in specs:
        if "refresh" in k.lower():
            faqs.append((f"What refresh rate does the {name} support?",
                        f"It supports up to {esc(specs[k])}, making it excellent for smooth gaming."))
            break
    # 延迟问题
    for k in specs:
        if any(w in k.lower() for w in ["response", "latency", "input lag"]):
            faqs.append((f"Is the {name} good for competitive gaming?",
                        f"With {esc(specs[k])} response time, it's one of the fastest options for competitive play."))
            break
    # 分辨率问题
    for k in specs:
        if "resolution" in k.lower():
            faqs.append((f"What resolution is the {name}?",
                        f"It runs at {esc(specs[k])}."))
            break
    # 价格问题
    if tp.get("price_range"):
        faqs.append((f"How much does the {name} cost?",
                    f"It typically sells for {esc(tp['price_range'])}. Check both Amazon and Temu above for the best current price."))
    # 通用：为什么选它
    faqs.append((f"Why is the {name} our top pick?",
                f"It's recommended by {p.get('review_count', 'multiple')} reviewers for its overall balance of performance, features, and value. See the detailed breakdown above."))
    html = ""
    for q, a in faqs:
        html += f'<details><summary>{q}</summary><div class="a">{a}</div></details>'
    return html

def render_human(p, slug):
    rows = ""
    for i, item in enumerate(p["products"], 1):
        rows += f'<tr><td><span class="rank">{i}</span></td><td><strong>{esc(item["name"])}</strong></td><td>{esc(item["recommended_by"])}</td><td>{esc(item["best_for"])}</td><td>{esc(item["price_range"])}</td></tr>\n'
    pros = "".join(f"<li>{esc(x)}</li>\n" for x in p["common_pros"])
    cons = "".join(f"<li>{esc(x)}</li>\n" for x in p["common_cons"])
    cards = ""
    for item in p["products"]:
        specs = "".join(f"<div><b>{esc(k)}:</b> {esc(v)}</div>" for k, v in item.get("specs", {}).items())
        img_tag = f'<img src="{esc(item["image"])}" alt="{esc(item["name"])}" loading="lazy">' if item.get("image") else ""
        # buy link: product's own affiliate link, else Amazon search for the product name
        if item.get("affiliate_link"):
            buy_url = item["affiliate_link"]
        else:
            q = esc(item["name"].replace(" ", "+"))
            buy_url = f"https://www.amazon.com/s?k={q}&tag=aipicks2003-20"
        tq = esc(item["name"].replace(" ", "+"))
        temu_url = f"https://www.temu.com/search_result.html?search_key={tq}"
        cards += f'<div class="card"><h3>{esc(item["name"])}</h3>{img_tag}<a class="btn-sm" href="{buy_url}" rel="nofollow sponsored noopener" target="_blank">🛒 Amazon</a><a class="btn-temu" href="{temu_url}" rel="nofollow sponsored noopener" target="_blank">🛒 Temu</a><p style="margin-top:.75rem">{esc(item.get("summary",""))}</p><div class="specs">{specs}</div><p style="color:#888;font-size:.85rem">Best for: {esc(item["best_for"])} · {esc(item["price_range"])}</p></div>\n'
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
    _tq = esc(p["top_pick"]["name"].replace(" ", "+"))
    out = out.replace("{{temu_link}}", f"https://www.temu.com/search_result.html?search_key={_tq}")
    out = out.replace("{{faq_html}}", gen_faq_html(p))
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
    _tq = esc(p["top_pick"]["name"].replace(" ", "+"))
    out = out.replace("{{temu_link}}", f"https://www.temu.com/search_result.html?search_key={_tq}")
    out = out.replace("{{faq_html}}", gen_faq_html(p))
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
    h_idx = """<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Buying Guides | AI-PICKS</title>
<style>body{background:#0a0e0a;color:#d4d4d4;font-family:sans-serif;max-width:860px;margin:0 auto;padding:2rem 1.25rem}a{color:#00ff41}.card{background:#111611;border:1px solid #1a3a24;border-radius:10px;padding:1.25rem;margin:1rem 0;display:flex;gap:1rem;align-items:center;text-decoration:none}.card:hover{border-color:#00ff41}.card .txt{flex:1}.card h2{color:#00ff41;margin-bottom:.5rem;font-size:1.05rem}.card p{color:#888;font-size:.88rem}.card img{width:110px;height:110px;object-fit:cover;border:2px solid #00ff41;border-radius:8px;box-shadow:0 0 12px rgba(0,255,65,.25);flex-shrink:0;background:#000}@media(max-width:600px){.card img{width:80px;height:80px}}</style></head>
<body><a href="../" style="font-size:.9rem">🔴 Back to Portal</a><h1 style="color:#fff">📖 Buying Guides</h1><p style="color:#888">Aggregated from YouTube reviews, curated for humans</p>"""
    for p in products:
        img = p["top_pick"].get("image", "")
        img_tag = f'<img src="{esc(img)}" alt="{esc(p["top_pick"]["name"])}" loading="lazy">' if img else ""
        h_idx += f'<a class="card" href="{p["slug"]}.html"><div class="txt"><h2>{esc(p["h1"])}</h2><p>{esc(p["meta_description"])}</p></div>{img_tag}</a>'
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
