#!/usr/bin/env python3
"""Generate Apple-style head-to-head comparison pages (human + AI versions).
Reads data/comparisons.json + product data from data/*.json.
Outputs: output/compare/<slug>.html, output/ai/compare-<slug>.html
"""
import json, os, html, re
from datetime import date
from pathlib import Path

BASE = Path(__file__).parent.parent
TPL_HUMAN = (BASE / "templates" / "compare_human.html").read_text()
TPL_AI = (BASE / "templates" / "compare_ai.html").read_text()
SITE_URL = os.environ.get("SITE_URL", "https://ccy123abcd.github.io/ai-picks")

def _valid_amz_link(url):
    if not url or "/dp/" not in url:
        return False
    m = re.search(r"/dp/([A-Z0-9]{10})", url)
    if not m:
        return False
    asin = m.group(1)
    if asin in ("B000000000", "B00000000X", "0000000000") or re.fullmatch(r"0+", asin):
        return False
    return True

# Import the verified set from generate.py (single source of truth)
import importlib.util
_spec = importlib.util.spec_from_file_location("gen", BASE / "scripts" / "generate.py")
_gen = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_gen)
VERIFIED_ASINS = _gen.VERIFIED_ASINS

def esc(s): return html.escape(str(s))

def find_product(guide_data, name):
    for p in guide_data["products"]:
        if p["name"] == name:
            return p
    raise ValueError(f"Product not found: {name}")

def get_verified_link(guide_data, name):
    """Return verified Amazon link if this product is the guide's top pick with verified ASIN."""
    tp = guide_data["top_pick"]
    if tp["name"] == name:
        link = tp.get("affiliate_link", "")
        m = re.search(r"/dp/([A-Z0-9]{10})", link or "")
        if m and m.group(1) in VERIFIED_ASINS and _valid_amz_link(link):
            return link
    return None

def build_spec_rows(pa, pb):
    """Side-by-side specs. Rows where values are effectively identical get dimmed."""
    keys = []
    for k in pa.get("specs", {}):
        if k not in keys: keys.append(k)
    for k in pb.get("specs", {}):
        if k not in keys: keys.append(k)
    rows = ""
    for k in keys:
        va = pa.get("specs", {}).get(k, "—")
        vb = pb.get("specs", {}).get(k, "—")
        same = va.strip().lower() == vb.strip().lower() or "—" in (va, vb)
        cls = "same" if same else "diff"
        badge = "" if same else '<span class="diff-badge">DIFFERS</span>'
        rows += f'<tr class="{cls}"><td class="spec-name">{esc(k)}{badge}</td><td>{esc(va)}</td><td>{esc(vb)}</td></tr>\n'
    return rows

def build_schema(cmp, pa, pb, guide):
    items = []
    for p in (pa, pb):
        item = {"@type": "Product", "name": p["name"],
                "description": p.get("summary", "")}
        link = get_verified_link(guide, p["name"])
        if link:
            item["offers"] = {"@type": "Offer",
                              "availability": "https://schema.org/InStock"}
        items.append(item)
    schema = {"@context": "https://schema.org", "@type": "ItemList",
              "name": cmp["title"], "itemListElement": items}
    return json.dumps(schema, indent=2)

def render(cmp):
    guide = json.load(open(BASE / "data" / f'{cmp["source_guide"]}.json'))
    pa = find_product(guide, cmp["product_a"])
    pb = find_product(guide, cmp["product_b"])
    slug = cmp["slug"]
    winner = cmp["winner"]

    # Buy buttons: only for verified ASINs
    def buy_btn(prod):
        link = get_verified_link(guide, prod["name"])
        if link:
            return f'<a class="btn" href="{esc(link)}" rel="nofollow sponsored noopener" target="_blank">Check Price on Amazon →</a>'
        return '<p class="note">🔍 Purchase link under verification</p>'

    def winner_tag(side):
        if (winner == "a" and side == "a") or (winner == "b" and side == "b"):
            return '<span class="tag">🏆 OUR PICK</span>'
        return ""

    data_json = json.dumps({
        "comparison": cmp["title"],
        "product_a": {"name": pa["name"], "specs": pa.get("specs", {}),
                      "price_range": pa.get("price_range", "")},
        "product_b": {"name": pb["name"], "specs": pb.get("specs", {}),
                      "price_range": pb.get("price_range", "")},
        "key_differences": cmp["key_differences"],
        "verdict": cmp["verdict"],
        "winner": cmp["product_a"] if winner == "a" else cmp["product_b"],
    }, indent=2, ensure_ascii=False)

    # Human version
    out = TPL_HUMAN
    out = out.replace("{{page_title}}", esc(f'{cmp["title"]}: Which Should You Buy in 2026? | AI-PICKS'))
    out = out.replace("{{meta_description}}", esc(f'{cmp["title"]} head-to-head comparison: specs, key differences, and verdict. {cmp["verdict"][:150]}'))
    out = out.replace("{{canonical_url}}", f"{SITE_URL}/compare/{slug}.html")
    out = out.replace("{{schema_json}}", build_schema(cmp, pa, pb, guide))
    out = out.replace("{{h1}}", esc(f'{cmp["title"]}: Which Should You Buy?'))
    out = out.replace("{{category}}", esc(cmp["category"]))
    out = out.replace("{{updated_date}}", date.today().isoformat())
    out = out.replace("{{name_a}}", esc(pa["name"]))
    out = out.replace("{{name_b}}", esc(pb["name"]))
    out = out.replace("{{price_a}}", esc(pa.get("price_range", "")))
    out = out.replace("{{price_b}}", esc(pb.get("price_range", "")))
    out = out.replace("{{summary_a}}", esc(pa.get("summary", "")))
    out = out.replace("{{summary_b}}", esc(pb.get("summary", "")))
    out = out.replace("{{winner_tag_a}}", winner_tag("a"))
    out = out.replace("{{winner_tag_b}}", winner_tag("b"))
    out = out.replace("{{buy_btn_a}}", buy_btn(pa))
    out = out.replace("{{buy_btn_b}}", buy_btn(pb))
    out = out.replace("{{spec_rows}}", build_spec_rows(pa, pb))
    out = out.replace("{{diff_list}}",
                      "".join(f"<li>{esc(x)}</li>\n" for x in cmp["key_differences"]))
    out = out.replace("{{verdict}}", esc(cmp["verdict"]))

    # AI version
    ai = TPL_AI
    ai = ai.replace("{{page_title}}", esc(f'{cmp["title"]} [AI Data] | AI-PICKS'))
    ai = ai.replace("{{meta_description}}", esc(f'Machine-readable comparison data: {cmp["title"]}'))
    ai = ai.replace("{{canonical_url}}", f"{SITE_URL}/ai/compare-{slug}.html")
    ai = ai.replace("{{schema_json}}", build_schema(cmp, pa, pb, guide))
    ai = ai.replace("{{h1}}", esc(cmp["title"]))
    ai = ai.replace("{{slug}}", esc(slug))
    ai = ai.replace("{{data_json}}", esc(data_json))
    ai = ai.replace("{{verdict}}", esc(cmp["verdict"]))

    return out, ai

def main():
    comparisons = json.load(open(BASE / "data" / "comparisons.json"))["comparisons"]
    outdir = BASE / "output" / "compare"
    aidir = BASE / "output" / "ai"
    outdir.mkdir(parents=True, exist_ok=True)
    aidir.mkdir(parents=True, exist_ok=True)
    urls = []
    for cmp in comparisons:
        human_html, ai_html = render(cmp)
        (outdir / f'{cmp["slug"]}.html').write_text(human_html)
        (aidir / f'compare-{cmp["slug"]}.html').write_text(ai_html)
        urls.append(f'{SITE_URL}/compare/{cmp["slug"]}.html')
        print(f'  ✓ {cmp["slug"]}')
    # Append to sitemap
    sm_path = BASE / "output" / "sitemap.xml"
    if sm_path.exists():
        sm = sm_path.read_text()
        for u in urls:
            if u not in sm:
                sm = sm.replace("</urlset>",
                    f'  <url><loc>{u}</loc><lastmod>{date.today().isoformat()}</lastmod></url>\n</urlset>')
        sm_path.write_text(sm)
        print("  sitemap updated")
    print(f"Done: {len(comparisons)} comparisons × 2 versions")

if __name__ == "__main__":
    main()
