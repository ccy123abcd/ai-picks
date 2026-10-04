#!/usr/bin/env python3
"""Generate static product aggregation pages — human/ and ai/ versions.
Usage: python3 generate.py
Reads data/*.json, outputs:
  output/index.html          — Matrix portal landing
  output/human/*.html        — pretty human-readable pages
  output/ai/*.html           — structured AI-readable pages
  output/llms.txt
"""
import json, os, html, re, shutil
from datetime import date
from pathlib import Path

def _valid_amz_link(url):
    """True only for real Amazon product links with a plausible ASIN.
    Rejects placeholder ASINs like B000000000 (protects affiliate account)."""
    if not url or "/dp/" not in url:
        return False
    m = re.search(r"/dp/([A-Z0-9]{10})", url)
    if not m:
        return False
    asin = m.group(1)
    if asin in ("B000000000", "B00000000X", "0000000000"):
        return False
    if re.fullmatch(r"0+", asin):
        return False
    return True

# ASINs manually verified by the user (real product page, purchasable).
# Rule: an Amazon button is ONLY rendered for ASINs in this set.
# Verified 2026-10-04 by user (opened each link, confirmed orderable).
VERIFIED_ASINS = {
    "B093MTSTKD",  # LG 27GP850-B 27" gaming monitor
    "B0002E4Z8M",  # Shure SM7B
    "B07Q8TJ2KL",  # Ergotron LX Single Monitor Arm
    "B07T5SY43L",  # HUANUO FlowLift Dual Monitor Stand
    "B07K986YLL",  # Logitech C920s Pro HD (verified 2026-10-04)
    "B09TQZP9CL",  # Dell U2723QE (verified 2026-10-04)
    "B076VNFZJG",  # BenQ ScreenBar (verified 2026-10-04)
    "B0CW1S7XP5",  # Elgato Facecam MK.2 (verified 2026-10-04)
    # Batch verified by user 2026-10-04 (22 ASINs)
    "B09XSDMT4F",  # Sony WH-1000XM5 (Silver)
    "B0CHFSWM2P",  # Samsung T9 1TB
    "B0C6927XPX",  # Synology DS224+
    "B09GK8LBWS",  # CalDigit TS4
    "B0BQ417K47",  # ASUS RT-AX86U Pro
    "B000OOYECC",  # Rain Design mStand
    "B07DYRS1WH",  # Elgato Stream Deck Mini
    "B0966YYP65",  # ASUS ZenScreen MB16ACV
    "B07CMS5Q6N",  # Logitech G305 Lightspeed (White)
    "B0CR1HHXSN",  # Keychron Q1 Max (assembled, Gateron Brown)
    "B0CPFWXMBL",  # Elgato 4K X
    "B0CFZX734J",  # DJI Mic 2
    "B0BC9Z44BC",  # Secretlab TITAN Evo 2022 (Small, Black)
    "B0D14N2QZF",  # AULA F75 Pro
    "B07L755X9G",  # Elgato Key Light
    "B0BN6RRD5V",  # Corsair TC100 Relaxed (Black)
    "B07B2WLS17",  # Logitech G560
    "B0F3QCXL82",  # Razer DeathAdder V4 Pro (Black)
    "B0DFX42Q1Y",  # SteelSeries Arctis GameBuds (PS/PC, Black)
    "B0BKW3LB2B",  # Logitech MX Keys S (Graphite)
    "B0FFGJ3TWP",  # 8BitDo Pro 3 (Gray)
    "B0GMLBSSTD",  # Razer Viper V4 Pro (Black)
}

def _verified_amz_link(url):
    """True only if the link has a plausible ASIN AND is in VERIFIED_ASINS."""
    if not _valid_amz_link(url):
        return False
    m = re.search(r"/dp/([A-Z0-9]{10})", url)
    return m.group(1) in VERIFIED_ASINS

BASE = Path(__file__).parent.parent
TPL_HUMAN = (BASE / "templates" / "product_human.html").read_text()
TPL_AI = (BASE / "templates" / "product.html").read_text()
TPL_PORTAL = (BASE / "templates" / "portal.html").read_text()
SITE_URL = os.environ.get("SITE_URL", "https://ccy123abcd.github.io/ai-picks")

def esc(s): return html.escape(str(s))

def build_schema(p):
    tp = p["top_pick"]
    schema = {
        "@context": "https://schema.org",
        "@type": "Product",
        "name": tp["name"],
        "description": p["meta_description"],
        "brand": {"@type": "Brand", "name": tp.get("brand", "")},
    }
    # Only claim availability for manually verified purchase links.
    # No hardcoded price: prices vary by region/currency and change daily.
    # Unverified products get no offers block (honest structured data for AI readers).
    if _verified_amz_link(tp.get("affiliate_link", "")):
        schema["offers"] = {
            "@type": "Offer",
            "availability": "https://schema.org/InStock",
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
        # MVP decision (2026-10-04): non-Top-Pick products get NO buy buttons.
        # Only the Top Pick has a real, verified purchase link.
        cards += f'<div class="card"><h3>{esc(item["name"])}</h3>{img_tag}<p style="margin-top:.75rem">{esc(item.get("summary",""))}</p><div class="specs">{specs}</div><p style="color:#888;font-size:.85rem">Best for: {esc(item["best_for"])} - {esc(item["price_range"])}</p></div>\n'
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
    # Top Pick Amazon button: only render for verified /dp/ ASIN links.
    # No verified ASIN = no button (protects affiliate account).
    _tp_aff = p["top_pick"].get("affiliate_link", "")
    if _verified_amz_link(_tp_aff):
        _amz_btn_mid = f'<a class="btn-sm" href="{esc(_tp_aff)}" rel="nofollow sponsored noopener" target="_blank">Check Price on Amazon →</a>'
        _amz_btn = f'<a class="btn" href="{esc(_tp_aff)}" rel="nofollow sponsored noopener" target="_blank">Check Price on Amazon →</a>'
        _amz_btn_ai = f'<a class="buy-btn" href="{esc(_tp_aff)}" rel="nofollow sponsored noopener" target="_blank">Check Price on Amazon</a>'
    else:
        _amz_btn_mid = '<span style="color:#888;font-size:.85rem">🔍 Purchase link under manual verification</span>'
        _amz_btn = '<p style="color:#888;font-size:.9rem;margin-top:.5rem">🔍 We\'re manually verifying this product\'s purchase link — check back soon.</p>'
        _amz_btn_ai = '<p style="color:#888;font-size:.9rem">🔍 Purchase link under manual verification — check back soon.</p>'
    out = out.replace("{{affiliate_link}}", esc(_tp_aff) if _verified_amz_link(_tp_aff) else "#")
    out = out.replace("{{amazon_btn_mid}}", _amz_btn_mid)
    out = out.replace("{{amazon_btn}}", _amz_btn)
    out = out.replace("{{amazon_btn_ai}}", _amz_btn_ai)
    _tq = esc(p["top_pick"]["name"].replace(" ", "+"))
    _tp_platforms = p["top_pick"].get("platforms", ["amazon"])
    out = out.replace("{{temu_link}}", f"https://www.temu.com/search_result.html?search_key={_tq}" if "temu" in _tp_platforms else "")
    out = out.replace("{{temu_btn_mid}}", f'<a class="btn-temu" href="https://www.temu.com/search_result.html?search_key={_tq}" rel="nofollow sponsored noopener" target="_blank">Check Price on Temu →</a>' if "temu" in _tp_platforms else "")
    out = out.replace("{{temu_btn_lg}}", f'<a class="btn-temu-lg" href="https://www.temu.com/search_result.html?search_key={_tq}" rel="nofollow sponsored noopener" target="_blank">Temu →</a>' if "temu" in _tp_platforms else "")
    out = out.replace("{{walmart_btn_mid}}", f'<a class="btn-walmart" href="https://www.walmart.com/search?q={_tq}" rel="nofollow sponsored noopener" target="_blank">Check Price on Walmart →</a>' if "walmart" in _tp_platforms else "")
    out = out.replace("{{walmart_btn_lg}}", f'<a class="btn-walmart-lg" href="https://www.walmart.com/search?q={_tq}" rel="nofollow sponsored noopener" target="_blank">Walmart →</a>' if "walmart" in _tp_platforms else "")
    out = out.replace("{{faq_html}}", gen_faq_html(p))
    pass  # walmart_link 已由上方占位符处理
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
    # AI page: same rule - only verified /dp/ links get a button
    _tp_aff2 = p["top_pick"].get("affiliate_link", "")
    if _verified_amz_link(_tp_aff2):
        _amz2 = f'<a class="buy-btn" href="{esc(_tp_aff2)}" rel="nofollow sponsored noopener" target="_blank">Check Price on Amazon</a>'
    else:
        _amz2 = ""
    out = out.replace("{{affiliate_link}}", esc(_tp_aff2) if _verified_amz_link(_tp_aff2) else "#")
    out = out.replace("{{amazon_btn_ai}}", _amz2)
    _tq = esc(p["top_pick"]["name"].replace(" ", "+"))
    _tp_platforms = p["top_pick"].get("platforms", ["amazon"])
    out = out.replace("{{temu_link}}", f"https://www.temu.com/search_result.html?search_key={_tq}" if "temu" in _tp_platforms else "")
    out = out.replace("{{temu_btn_mid}}", f'<a class="btn-temu" href="https://www.temu.com/search_result.html?search_key={_tq}" rel="nofollow sponsored noopener" target="_blank">Check Price on Temu →</a>' if "temu" in _tp_platforms else "")
    out = out.replace("{{temu_btn_lg}}", f'<a class="btn-temu-lg" href="https://www.temu.com/search_result.html?search_key={_tq}" rel="nofollow sponsored noopener" target="_blank">Temu →</a>' if "temu" in _tp_platforms else "")
    out = out.replace("{{walmart_btn_mid}}", f'<a class="btn-walmart" href="https://www.walmart.com/search?q={_tq}" rel="nofollow sponsored noopener" target="_blank">Check Price on Walmart →</a>' if "walmart" in _tp_platforms else "")
    out = out.replace("{{walmart_btn_lg}}", f'<a class="btn-walmart-lg" href="https://www.walmart.com/search?q={_tq}" rel="nofollow sponsored noopener" target="_blank">Walmart →</a>' if "walmart" in _tp_platforms else "")
    out = out.replace("{{faq_html}}", gen_faq_html(p))
    pass  # walmart_link 已由上方占位符处理
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

    # llms.txt — mark guides whose Top Pick has a manually verified buy link
    llms_tpl = (BASE / "templates" / "llms.txt").read_text()
    prods = "\n".join(
        f"- {p['h1']}: {SITE_URL}/ai/{p['slug']}.html"
        + (" [verified buy link]" if _verified_amz_link(p["top_pick"].get("affiliate_link", "")) else "")
        for p in products
    )
    (out / "llms.txt").write_text(llms_tpl.replace("{{product_list}}", prods))
    print("  ✓ llms.txt")
    import shutil

    # sitemap.xml — auto-generated so it never goes stale (was missing 21 guides)
    today = date.today().isoformat()
    sm_urls = [
        f"{SITE_URL}/",
        f"{SITE_URL}/human/",
        f"{SITE_URL}/ai/",
        f"{SITE_URL}/finder.html",
        f"{SITE_URL}/about.html",
        f"{SITE_URL}/privacy.html",
    ]
    for p in products:
        sm_urls.append(f"{SITE_URL}/human/{p['slug']}.html")
        sm_urls.append(f"{SITE_URL}/ai/{p['slug']}.html")
    sm_xml = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    for u in sm_urls:
        sm_xml += f"  <url><loc>{u}</loc><lastmod>{today}</lastmod></url>\n"
    sm_xml += "</urlset>\n"
    (out / "sitemap.xml").write_text(sm_xml)
    print(f"  ✓ sitemap.xml ({len(sm_urls)} urls)")
    # finder-data.json — auto-generated from data/*.json so buy links never go stale.
    # MVP rule: only verified Top Picks get an Amazon button; others get none.
    finder_data = []
    for p in products:
        tp = p["top_pick"]
        tp_aff = tp.get("affiliate_link", "")
        for item in p["products"]:
            is_tp = (item["name"] == tp["name"])
            finder_data.append({
                "name": item["name"],
                "brand": item.get("brand", ""),
                "category": p["h1"],
                "guide": p["slug"],
                "price": item.get("price_range", ""),
                "specs": item.get("specs", {}),
                "summary": item.get("summary", ""),
                "best_for": item.get("best_for", ""),
                "platforms": item.get("platforms", ["amazon"]) if is_tp else [],
                "is_top_pick": is_tp,
                # Only verified Top Pick ASINs get a real buy link
                "affiliate_link": tp_aff if (is_tp and _verified_amz_link(tp_aff)) else "",
            })
    (BASE / "finder-data.json").write_text(json.dumps(finder_data, ensure_ascii=False, indent=1))
    shutil.copy(BASE / "finder-data.json", out / "finder-data.json")
    print(f"  ✓ finder-data.json ({len(finder_data)} products)")
    shutil.copy("templates/portal_zh.html", "output/zh/index.html")
    shutil.copy("templates/finder_zh.html", "output/zh/finder.html")
    print("  ✓ zh/ 中文版")
    shutil.copy("templates/about.html", "output/about.html")
    shutil.copy("templates/privacy.html", "output/privacy.html")
    print("  ✓ about + privacy")
    print("  ✓ finder.html")
    print(f"Done: {len(products)} products × 2 versions")

if __name__ == "__main__":
    main()
