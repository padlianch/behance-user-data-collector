#!/usr/bin/env python3
"""
Behance User Search Scraper
Mengambil data user dari https://www.behance.net/search/users via GraphQL
Output: JSON

Penggunaan:
  python3 behance_scraper.py -q "designer" -n 48 -o hasil.json
  python3 behance_scraper.py -q "photographer" --country ID -n 100
"""

import asyncio
import json
import sys
from typing import Any
from playwright.async_api import async_playwright


SEARCH_URL = "https://www.behance.net/search/users"
GRAPHQL_URL = "https://www.behance.net/v3/graphql"


def parse_user(node: dict) -> dict:
    """Normalisasi satu user node dari response GraphQL Behance."""
    # Avatar: ambil ukuran terbesar yang tersedia
    avatar = ""
    images = node.get("images") or {}
    all_images = images.get("allAvailable") or []
    if all_images:
        largest = max(all_images, key=lambda x: x.get("width", 0))
        avatar = largest.get("url", "")

    # Social media links
    socials: dict[str, str] = {}
    for ref in node.get("socialReferences") or []:
        service = ref.get("socialService", "").lower()
        url = ref.get("url", "")
        if service and url:
            socials[service] = url

    # Stats
    stats = node.get("stats") or {}

    # Availability info
    avail = node.get("availabilityInfo") or {}

    # Projects (hanya ID dan judul jika tersedia)
    projects_raw = node.get("projects") or {}
    projects = []
    for p in projects_raw.get("nodes") or []:
        projects.append({
            "id": p.get("id"),
            "name": p.get("name") or p.get("title", ""),
            "url": p.get("url", ""),
        })

    return {
        "id": node.get("id"),
        "username": node.get("username", ""),
        "display_name": node.get("displayName") or node.get("firstName", ""),
        "url": node.get("url", ""),
        "avatar": avatar,
        "location": node.get("location") or "",
        "country": node.get("country") or "",
        "company": node.get("company") or "",
        "stats": {
            "followers": stats.get("followers", 0),
            "appreciations": stats.get("appreciations", 0),
            "views": stats.get("views", 0),
        },
        "social_links": socials,
        "availability": {
            "freelance": avail.get("isAvailableFreelance", False),
            "full_time": avail.get("isAvailableFullTime", False),
            "budget_min": avail.get("budgetMin"),
            "hiring_timeline": (avail.get("hiringTimeline") or {}).get("key"),
        },
        "is_pro": (node.get("creatorPro") or {}).get("isActive", False),
        "is_verified_recruiter": node.get("isVerifiedRecruiterOrganization", False),
        "projects": projects,
    }


async def scrape(
    query: str = "",
    country: str = "",
    city: str = "",
    max_users: int = 48,
) -> list[dict[str, Any]]:
    """
    Scrape Behance user search dan kembalikan list user sebagai dict.

    Args:
        query: Kata kunci pencarian (nama, username, atau keahlian)
        country: Kode negara 2-huruf (misal: 'ID', 'US', 'FR')
        city: Nama kota
        max_users: Jumlah maksimal user yang diambil
    """
    results: list[dict] = []
    seen_ids: set[int] = set()

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1280, "height": 900},
            extra_http_headers={
                "Accept-Language": "en-US,en;q=0.9",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            },
        )
        page = await context.new_page()

        async def handle_graphql(response):
            if GRAPHQL_URL not in response.url:
                return
            if response.status != 200:
                return
            try:
                body = await response.json()
                search = (body.get("data") or {}).get("search") or {}
                nodes = search.get("nodes") or []
                for node in nodes:
                    if node.get("__typename") != "User":
                        continue
                    uid = node.get("id")
                    if uid and uid not in seen_ids:
                        seen_ids.add(uid)
                        results.append(parse_user(node))
                        if len(results) >= max_users:
                            return
                page_info = search.get("pageInfo") or {}
                if page_info.get("hasNextPage"):
                    print(
                        f"[*] {len(results)} user terkumpul, ada halaman berikutnya...",
                        file=sys.stderr,
                    )
            except Exception as e:
                print(f"[warn] Gagal parse response: {e}", file=sys.stderr)

        page.on("response", handle_graphql)

        # Bangun URL dengan parameter
        params: list[str] = []
        if query:
            params.append(f"search={query}")
        if country:
            params.append(f"country={country}")
        if city:
            params.append(f"city={city}")

        url = SEARCH_URL
        if params:
            url += "?" + "&".join(params)

        print(f"[*] Membuka: {url}", file=sys.stderr)
        await page.goto(url, wait_until="networkidle", timeout=30000)
        await page.wait_for_timeout(1500)

        # Scroll untuk memuat lebih banyak hasil
        max_scrolls = (max_users // 48) + 5
        prev_count = 0
        stale = 0

        for scroll_i in range(max_scrolls):
            if len(results) >= max_users:
                break
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(2500)
            if len(results) == prev_count:
                stale += 1
                if stale >= 3:
                    print("[*] Tidak ada data baru, berhenti.", file=sys.stderr)
                    break
            else:
                stale = 0
            prev_count = len(results)

        await browser.close()

    return results[:max_users]


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(
        description="Scrape data user dari Behance Search",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Contoh:
  python3 behance_scraper.py -q "ui designer"
  python3 behance_scraper.py -q "photographer" --country ID -n 100 -o hasil.json
  python3 behance_scraper.py --country US --city "New York" -n 50
        """,
    )
    parser.add_argument("-q", "--query", default="", help="Kata kunci pencarian")
    parser.add_argument("--country", default="", help="Kode negara 2-huruf (misal: ID, US)")
    parser.add_argument("--city", default="", help="Nama kota")
    parser.add_argument(
        "-n", "--max-users", type=int, default=48,
        help="Jumlah maksimal user (default: 48, kelipatan 48 disarankan)",
    )
    parser.add_argument("-o", "--output", default="", help="Simpan ke file JSON")
    parser.add_argument("--pretty", action="store_true", help="Format JSON yang mudah dibaca")
    args = parser.parse_args()

    print("[*] Memulai scraping Behance users...", file=sys.stderr)

    users = asyncio.run(
        scrape(
            query=args.query,
            country=args.country,
            city=args.city,
            max_users=args.max_users,
        )
    )

    output = {
        "total": len(users),
        "filter": {
            "query": args.query,
            "country": args.country,
            "city": args.city,
        },
        "users": users,
    }

    indent = 2 if args.pretty or args.output else None
    json_str = json.dumps(output, ensure_ascii=False, indent=indent)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(json_str)
        print(f"[*] Disimpan ke: {args.output}", file=sys.stderr)
        print(f"[*] Total user: {len(users)}", file=sys.stderr)
    else:
        print(json_str)


if __name__ == "__main__":
    main()
