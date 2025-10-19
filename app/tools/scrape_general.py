import sys
import time
import csv
import json
import re
from typing import List, Dict, Optional
from urllib.parse import urlparse, urljoin

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

# ---------- CONFIG ----------
USER_AGENT = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
              "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
HEADLESS = False               # change to True after testing if not blocked
DELAY_BETWEEN_PAGE = 1.0       # polite delay
MAX_PRODUCTS = None            # None or integer
MAX_REVIEWS_PER_PRODUCT = 5
# ----------------------------

def init_driver(headless=HEADLESS):
    """Initialize and return Selenium WebDriver"""
    import os
    
    options = webdriver.ChromeOptions()
    options.add_argument(f"user-agent={USER_AGENT}")
    
    # Essential Docker flags
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-software-rasterizer")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--remote-debugging-port=9222")
    options.add_argument("--window-size=1920,1080")
    
    # Headless mode (always use in Docker)
    if headless or os.path.exists("/.dockerenv"):
        options.add_argument("--headless=new")
        print("🚀 Running in headless mode")
    
    # Set Chromium binary if it exists
    if os.path.exists("/usr/bin/chromium"):
        options.binary_location = "/usr/bin/chromium"
        print("🐳 Using Chromium in Docker")
    
    # Initialize driver
    try:
        driver = webdriver.Chrome(options=options)
        print("✅ Chrome driver initialized successfully")
        return driver
    except Exception as e:
        print(f"❌ Failed to initialize Chrome driver: {e}")
        raise

def get_soup_from_driver(driver, url, wait_seconds=1.0):
    driver.get(url)
    time.sleep(wait_seconds)
    return BeautifulSoup(driver.page_source, "html.parser")

# ------- JSON-LD helpers -------
def parse_jsonld_blocks(soup) -> List[dict]:
    blocks = []
    for tag in soup.select("script[type='application/ld+json']"):
        text = tag.string or tag.get_text() or ""
        text = text.strip()
        if not text:
            continue
        # JSON-LD sometimes contains multiple JSON objects one after another; try safe parsing
        try:
            parsed = json.loads(text)
            if isinstance(parsed, list):
                blocks.extend(parsed)
            else:
                blocks.append(parsed)
        except Exception:
            # attempt to split multiple JSON objects (rare) or fix trailing commas
            # try to find all {...} objects using regex (fallback)
            objs = re.findall(r'\{.*?\}\s*(?=\{|\s*$)', text, flags=re.DOTALL)
            for o in objs:
                try:
                    parsed = json.loads(o)
                    blocks.append(parsed)
                except Exception:
                    continue
    return blocks

def find_jsonld_of_type(blocks: List[dict], typ: str) -> Optional[dict]:
    for blk in blocks:
        if not isinstance(blk, dict):
            continue
        t = blk.get("@type") or blk.get("type")
        if isinstance(t, list):
            if any(typ.lower() in (x or "").lower() for x in t):
                return blk
        elif isinstance(t, str):
            if typ.lower() in t.lower():
                return blk
    return None

# ------- cleaning & parsing helpers -------
CTA_PATTERNS = [
    re.compile(r"(?i)please enter pin"), re.compile(r"(?i)add to bag"), re.compile(r"(?i)buy "),
    re.compile(r"(?i)style id"), re.compile(r"(?i)please check"), re.compile(r"(?i)check delivery")
]

def clean_description_text(text: str) -> str:
    if not text:
        return ""
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    good = []
    for ln in lines:
        low = ln.lower()
        if len(ln) < 15:
            # skip very short lines (usually CTA/UI)
            continue
        if any(p.search(ln) for p in CTA_PATTERNS):
            continue
        # remove repeated 'Please enter PIN code' style lines
        if "pin" in low and ("delivery" in low or "pincode" in low or "pin code" in low):
            continue
        good.append(ln)
    if not good:
        # fallback: return the longest original non-CTA line
        candidates = [ln for ln in lines if not any(p.search(ln) for p in CTA_PATTERNS)]
        if candidates:
            return max(candidates, key=len)
        return ""
    # return the longest meaningful paragraph
    return max(good, key=len)

def parse_rating_string(s: str) -> Optional[float]:
    if not s:
        return None
    # handle patterns like "4.5 out of 5", "4/5", "4.5 stars", "4.5/5"
    m = re.search(r'(\d+(?:\.\d+)?)\s*(?:/|out of|stars?|star|/5)\s*(?:5)?', s, flags=re.I)
    if m:
        try:
            return float(m.group(1))
        except:
            return None
    # handle ★★★★★ patterns: count stars
    if '★' in s:
        count = s.count('★')
        # if use full stars maybe 5 scale; return count (may be 4 etc.)
        try:
            return float(count)
        except:
            return None
    return None

# ------- extractors -------
def extract_brand_from_jsonld(json_ld: Optional[dict]) -> str:
    if not json_ld:
        return ""
    # product.brand could be string or dict
    brand = json_ld.get("brand") or json_ld.get("manufacturer") or json_ld.get("maker") or ""
    if isinstance(brand, dict):
        return brand.get("name") or brand.get("@id") or ""
    if isinstance(brand, str):
        return brand
    return ""

def extract_breadcrumbs_from_jsonld(blocks: List[dict]) -> str:
    # Look for BreadcrumbList schema
    bl = find_jsonld_of_type(blocks, "BreadcrumbList")
    if bl:
        items = bl.get("itemListElement") or bl.get("itemList") or []
        names = []
        for it in items:
            # item may be dict or nested
            if isinstance(it, dict):
                if "name" in it:
                    names.append(it["name"])
                else:
                    # some formats: item: { "@id": "...", "name": "..." }
                    item = it.get("item") or it.get("itemListElement")
                    if isinstance(item, dict) and item.get("name"):
                        names.append(item.get("name"))
                    else:
                        # try extract nested 'item'->'name'
                        try:
                            nm = it.get("item", {}).get("name")
                            if nm:
                                names.append(nm)
                        except:
                            pass
        return "/".join([n.strip() for n in names if n])
    return ""

def extract_reviews_from_jsonld(json_ld_prod: Optional[dict], max_reviews=MAX_REVIEWS_PER_PRODUCT):
    if not json_ld_prod:
        return [], None, None
    reviews_raw = json_ld_prod.get("review") or json_ld_prod.get("reviews") or []
    if isinstance(reviews_raw, dict):
        reviews_raw = [reviews_raw]
    collected = []
    for r in reviews_raw[:max_reviews]:
        author = ""
        rating = ""
        body = ""
        if isinstance(r, dict):
            author = r.get("author", "")
            if isinstance(author, dict):
                author = author.get("name") or author.get("@id") or ""
            # rating
            rr = r.get("reviewRating") or r.get("rating")
            if isinstance(rr, dict):
                rating = rr.get("ratingValue") or rr.get("bestRating") or ""
            elif rr:
                rating = str(rr)
            body = r.get("reviewBody") or r.get("description") or r.get("name") or ""
        else:
            body = str(r)
        rating_val = ""
        try:
            rv = parse_rating_string(str(rating))
            if rv is not None:
                rating_val = f"{rv}/5"
        except:
            rating_val = str(rating)
        entry = f"{(author or '').strip()}|{rating_val}|{(body or '').strip()}"
        collected.append(entry)
    # aggregateRating
    agg = json_ld_prod.get("aggregateRating") or {}
    agg_rating = agg.get("ratingValue") or agg.get("rating")
    agg_count = agg.get("reviewCount") or agg.get("reviewCount") or agg.get("ratingCount")
    if agg_rating:
        try:
            agg_rating = float(agg_rating)
            agg_rating_formatted = f"{agg_rating}/5"
        except:
            agg_rating_formatted = str(agg_rating)
    else:
        agg_rating_formatted = None
    return collected, agg_rating_formatted, agg_count

# DOM fallback extractors
def extract_brand_from_dom(soup: BeautifulSoup) -> str:
    # Common selectors
    selectors = [
        "[itemprop='brand']",
        ".brand", ".product-brand", ".brand-name", ".manufacturer", ".product-manufacturer",
        "meta[name='brand']", "meta[property='product:brand']"
    ]
    for sel in selectors:
        el = soup.select_one(sel)
        if el:
            if el.name == "meta":
                val = el.get("content") or ""
            else:
                val = el.get_text(strip=True)
            if val:
                return val
    # heuristic: look for 'by <Brand>' near title
    title = soup.select_one("h1, h1.title, .pdp-title")
    if title:
        text = title.get_text(" ", strip=True)
        m = re.search(r'by\s+([A-Za-z0-9 &\.-]{2,50})$', text, flags=re.I)
        if m:
            return m.group(1).strip()
    return ""

def extract_aggregate_rating_from_dom(soup: BeautifulSoup):
    # look for aria-labels like "4.5 out of 5 stars" in elements near rating
    els = soup.select("[aria-label], [title], [alt]")
    for el in els:
        for attr in ("aria-label", "title", "alt"):
            v = el.get(attr)
            if not v:
                continue
            rv = parse_rating_string(v)
            if rv is not None:
                return f"{rv}/5", None
    # text patterns e.g. "4.3/5"
    txt = soup.get_text(" ", strip=True)
    m = re.search(r'(\d(?:\.\d)?)\s*(?:/|out of)\s*5', txt)
    if m:
        try:
            return f"{float(m.group(1))}/5", None
        except:
            return m.group(1), None
    return None, None

def extract_reviews_from_dom(soup: BeautifulSoup, max_reviews=MAX_REVIEWS_PER_PRODUCT):
    collected = []
    # try review cards
    card_selectors = [".review", ".reviewCard", ".user-review", ".comment", ".product-review", ".rvw"]
    for sel in card_selectors:
        for el in soup.select(sel):
            text = el.get_text(" ", strip=True)
            if not text or len(text) < 30:
                continue
            # try find a rating inside el
            rating_text = ""
            for attr in ("aria-label", "title", "alt"):
                v = el.get(attr)
                if v:
                    rv = parse_rating_string(v)
                    if rv:
                        rating_text = f"{rv}/5"
                        break
            # try find small rating element inside
            inner = el.select_one("[aria-label], .rating, .stars, .ratingValue")
            if inner and not rating_text:
                v = inner.get("aria-label") or inner.get("title") or inner.get_text(" ", strip=True)
                rv = parse_rating_string(v)
                if rv:
                    rating_text = f"{rv}/5"
            # attempt author
            author = ""
            auth_sel = el.select_one(".author, .user-name, .review-author")
            if auth_sel:
                author = auth_sel.get_text(" ", strip=True)
            entry = f"{author}|{rating_text}|{text}"
            collected.append(entry)
            if len(collected) >= max_reviews:
                break
        if collected:
            break
    return collected

# ------- main PDP extraction combining all strategies -------
def extract_product_from_pdp_robust(soup: BeautifulSoup, base_url: str) -> Dict:
    out = {
        "name": "",
        "brand": "",
        "price": "",
        "currency": "",
        "description": "",
        "images": "",
        "breadcrumbs": "",
        "rating": "",
        "review_count": "",
        "reviews": ""
    }

    json_blocks = parse_jsonld_blocks(soup)
    product_json = find_jsonld_of_type(json_blocks, "Product")
    # 1) name
    if product_json:
        out["name"] = product_json.get("name") or out["name"]
    if not out["name"]:
        og = soup.select_one("meta[property='og:title'], meta[name='og:title']")
        if og:
            out["name"] = og.get("content") or ""
    if not out["name"]:
        h1 = soup.select_one("h1")
        if h1:
            out["name"] = h1.get_text(" ", strip=True)

    # 2) brand
    out["brand"] = extract_brand_from_jsonld(product_json) or extract_brand_from_dom(soup) or ""

    # 3) price & currency
    if product_json:
        offers = product_json.get("offers") or {}
        if isinstance(offers, list):
            offers = offers[0] if offers else {}
        if offers:
            out["price"] = offers.get("price") or offers.get("priceSpecification", {}).get("price") or out["price"]
            out["currency"] = offers.get("priceCurrency") or out["currency"]
    if not out["price"]:
        # fallback selectors
        price_sel = soup.select_one("[itemprop='price'], .price, .product-price, .selling-price, .a-price")
        if price_sel:
            out["price"] = price_sel.get("content") or price_sel.get_text(" ", strip=True)

    # 4) description (clean)
    desc = ""
    if product_json:
        desc = product_json.get("description") or ""
    if not desc:
        ogd = soup.select_one("meta[property='og:description'], meta[name='description']")
        if ogd:
            desc = ogd.get("content") or ""
    if not desc:
        ip = soup.select_one("[itemprop='description']")
        if ip:
            desc = ip.get_text(" ", strip=True) or ip.get("content") or ""
    if not desc:
        # common PDP blocks
        for sel in ["div.pdp-description", "div.product-description", "#description", ".pdp-product-more", ".productDescription"]:
            el = soup.select_one(sel)
            if el and el.get_text(strip=True):
                desc = el.get_text(" ", strip=True)
                break
    out["description"] = clean_description_text(desc)

    # 5) images
    imgs = []
    if product_json:
        imgs_json = product_json.get("image") or product_json.get("images") or product_json.get("thumbnailUrl")
        if isinstance(imgs_json, list):
            imgs.extend(imgs_json)
        elif isinstance(imgs_json, str):
            imgs.append(imgs_json)
    if not imgs:
        og_img = soup.select_one("meta[property='og:image']")
        if og_img:
            imgs.append(og_img.get("content"))
    if not imgs:
        for img in soup.select("img"):
            src = img.get("src") or img.get("data-src") or img.get("data-lazy-src")
            if src and len(imgs) < 6:
                imgs.append(urljoin(base_url, src))
    out["images"] = ", ".join(imgs)

    # 6) breadcrumbs: JSON-LD breadcrumblist first
    bc = extract_breadcrumbs_from_jsonld(json_blocks)
    if not bc:
        # dom fallbacks
        for sel in ["nav[aria-label*='breadcrumb']", "nav.breadcrumb", ".breadcrumbs", ".breadcrumb", "ul.breadcrumbs", "ol.breadcrumb"]:
            el = soup.select_one(sel)
            if el:
                texts = [a.get_text(" ", strip=True) for a in el.select("a, li, span") if a.get_text(strip=True)]
                if texts:
                    # remove product/title-like last token if it's same as name
                    if texts and out["name"] and texts[-1].strip() == out["name"].strip():
                        texts = texts[:-1]
                    bc = "/".join([t for t in texts if t])
                    break
    # final clean: remove lines that look like CTA or description
    if bc:
        bc_parts = [p.strip() for p in bc.split("/") if p.strip() and len(p.strip()) < 80 and not any(pat.search(p) for pat in CTA_PATTERNS)]
        out["breadcrumbs"] = "/".join(bc_parts)
    else:
        out["breadcrumbs"] = ""

    # 7) reviews & ratings
    reviews_list = []
    agg_rating = None
    agg_count = None
    if product_json:
        reviews_list, agg_rating, agg_count = extract_reviews_from_jsonld(product_json, max_reviews=MAX_REVIEWS_PER_PRODUCT)
    # if not found, try aggregate rating from JSON-LD blocks (some sites embed aggregateRating separate)
    if not agg_rating:
        agg = find_jsonld_of_type(json_blocks, "AggregateRating")
        if agg:
            rv = agg.get("ratingValue") or agg.get("rating")
            cnt = agg.get("reviewCount") or agg.get("ratingCount")
            agg_rating = f"{rv}/5" if rv else None
            agg_count = cnt
    # DOM fallback for ratings
    if not agg_rating:
        dom_rating, dom_count = extract_aggregate_rating_from_dom(soup)
        if dom_rating:
            agg_rating = dom_rating
            agg_count = dom_count
    # DOM fallback for reviews (if JSON-LD absent)
    if not reviews_list:
        reviews_list = extract_reviews_from_dom(soup, max_reviews=MAX_REVIEWS_PER_PRODUCT)

    out["reviews"] = " || ".join(reviews_list)
    out["rating"] = agg_rating or ""
    out["review_count"] = agg_count or ""
    # final whitespace cleanup
    for k, v in out.items():
        if isinstance(v, str):
            out[k] = " ".join(v.split())
    return out

# ------- listing detection and card parsing -------
def find_product_cards_on_listing(soup, base_url) -> List[Dict]:
    card_selectors = [
        "a.product-base", "li.product-base", "a.product-card", ".product", ".s-result-item", ".search-result-item",
        ".product-grid-item", ".grid-item", ".search-result", ".productTile", ".productListItem"
    ]
    seen = set()
    results = []
    for sel in card_selectors:
        nodes = soup.select(sel)
        if not nodes:
            continue
        for n in nodes:
            # find best link inside or n itself
            a = n.find("a", href=True)
            if a:
                link = urljoin(base_url, a.get("href"))
            elif n.name == "a" and n.get("href"):
                link = urljoin(base_url, n.get("href"))
            else:
                continue
            if link in seen:
                continue
            seen.add(link)
            # name: try multiple selectors
            name = ""
            for s in ["h4.product-product", "h3.product-brand", "h3", "h4", ".product-title", ".product-name", ".name"]:
                el = n.select_one(s)
                if el and el.get_text(strip=True):
                    name = el.get_text(strip=True)
                    break
            # price
            price = ""
            for s in [".product-discountedPrice", ".product-price", ".price", ".selling-price", ".a-price", ".price-block"]:
                el = n.select_one(s)
                if el and el.get_text(strip=True):
                    price = el.get_text(strip=True)
                    break
            # image
            img = n.find("img")
            img_url = ""
            if img:
                img_url = img.get("src") or img.get("data-src") or img.get("data-lazy-src") or ""
                if img_url:
                    img_url = urljoin(base_url, img_url)
            results.append({"name": name, "link": link, "price": price, "image": img_url})
        if results:
            break
    return results

# ------- main scrape function -------
def scrape(url: str, output_csv: str):
    driver = init_driver()
    try:
        base = "{uri.scheme}://{uri.netloc}/".format(uri=urlparse(url))
        print("Loading:", url)
        soup = get_soup_from_driver(driver, url, wait_seconds=1.2)

        listing_cards = find_product_cards_on_listing(soup, base)
        rows = []
        if listing_cards and len(listing_cards) >= 4:
            print(f"Detected listing page with {len(listing_cards)} cards (first page).")
            count = 0
            for card in listing_cards:
                if MAX_PRODUCTS and count >= MAX_PRODUCTS:
                    break
                row = {
                    "name": card.get("name", ""),
                    "brand": "",
                    "price": card.get("price", ""),
                    "link": card.get("link", ""),
                    "image": card.get("image", ""),
                    "description": "",
                    "breadcrumbs": "",
                    "rating": "",
                    "review_count": "",
                    "reviews": ""
                }
                print(f" Visiting PDP: {row['link']}")
                try:
                    pdp_soup = get_soup_from_driver(driver, row["link"], wait_seconds=1.0)
                    pdp_data = extract_product_from_pdp_robust(pdp_soup, base)
                    # merge with listing info
                    row.update({
                        "name": row["name"] or pdp_data.get("name", ""),
                        "brand": pdp_data.get("brand", ""),
                        "price": row["price"] or pdp_data.get("price", ""),
                        "description": pdp_data.get("description", ""),
                        "breadcrumbs": pdp_data.get("breadcrumbs", ""),
                        "rating": pdp_data.get("rating", ""),
                        "review_count": pdp_data.get("review_count", ""),
                        "reviews": pdp_data.get("reviews", ""),
                        "image": row["image"] or pdp_data.get("images", "")
                    })
                except Exception as e:
                    print("  PDP visit failed:", e)
                rows.append(row)
                count += 1
                time.sleep(DELAY_BETWEEN_PAGE)
        else:
            print("Detected PDP (direct extraction).")
            pdp_data = extract_product_from_pdp_robust(soup, base)
            rows.append({
                "name": pdp_data.get("name", ""),
                "brand": pdp_data.get("brand", ""),
                "price": pdp_data.get("price", ""),
                "link": url,
                "image": pdp_data.get("images", ""),
                "description": pdp_data.get("description", ""),
                "breadcrumbs": pdp_data.get("breadcrumbs", ""),
                "rating": pdp_data.get("rating", ""),
                "review_count": pdp_data.get("review_count", ""),
                "reviews": pdp_data.get("reviews", "")
            })

        # write CSV
        fieldnames = ["name", "brand", "price", "link", "image", "description", "breadcrumbs", "rating", "review_count", "reviews"]
        with open(output_csv, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for r in rows:
                writer.writerow(r)

        print("Saved", len(rows), "items to", output_csv)
    finally:
        driver.quit()

# # CLI
# if __name__ == "__main__":
#     if len(sys.argv) < 3:
#         print("Usage: python general_ecom_scraper_v2.py <url> <output.csv>")
#         sys.exit(1)
#     url = sys.argv[1]
#     out = sys.argv[2]
#     scrape(url, out)
