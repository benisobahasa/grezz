"""
Scraper for GEO (Generative Engine Optimization) analysis.
Fetches a page and pulls both raw HTML signals (schema, robots, headings) and
clean readable text (via trafilatura) that an AI answer engine would actually
"read" when deciding whether to cite the page.
"""
import re
from urllib.parse import urljoin, urlparse

import httpx
import trafilatura
from bs4 import BeautifulSoup

from app.security import validate_and_resolve_url, UnsafeURLError

USER_AGENT = "Mozilla/5.0 (compatible; GrezzBot/1.0; +https://grezz.app/bot)"


class ScrapeError(Exception):
    pass


async def fetch(url: str) -> tuple[str, str]:
    try:
        validate_and_resolve_url(url)
    except UnsafeURLError as exc:
        raise ScrapeError(str(exc)) from exc

    headers = {"User-Agent": USER_AGENT}
    max_bytes = 3_000_000  # 3MB cap — plenty for a page's HTML, blocks abuse via huge files
    async with httpx.AsyncClient(timeout=20, follow_redirects=True, headers=headers) as client:
        try:
            async with client.stream("GET", url) as resp:
                if resp.status_code >= 400:
                    raise ScrapeError(f"Website returned status {resp.status_code}")
                chunks = []
                total = 0
                async for chunk in resp.aiter_bytes():
                    total += len(chunk)
                    if total > max_bytes:
                        break
                    chunks.append(chunk)
                html = b"".join(chunks).decode(resp.encoding or "utf-8", errors="replace")
        except httpx.RequestError as exc:
            raise ScrapeError(f"Failed to access URL: {exc}") from exc

        robots_txt = ""
        try:
            parsed = urlparse(url)
            robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
            robots_resp = await client.get(robots_url)
            if robots_resp.status_code == 200:
                robots_txt = robots_resp.text
        except httpx.RequestError:
            pass

    return html, robots_txt


AI_BOT_TOKENS = ["GPTBot", "Google-Extended", "PerplexityBot", "ClaudeBot", "CCBot", "anthropic-ai"]


def analyze_robots(robots_txt: str) -> dict:
    if not robots_txt:
        return {"robots_found": False, "ai_bots_blocked": [], "ai_bots_allowed": AI_BOT_TOKENS}

    blocked = []
    lower = robots_txt.lower()
    blocks = re.split(r"user-agent:", lower)
    for block in blocks:
        for bot in AI_BOT_TOKENS:
            if block.strip().startswith(bot.lower()) and "disallow: /" in block:
                blocked.append(bot)
    allowed = [b for b in AI_BOT_TOKENS if b not in blocked]
    return {"robots_found": True, "ai_bots_blocked": blocked, "ai_bots_allowed": allowed}


def extract_signals(html: str, base_url: str, robots_txt: str) -> dict:
    soup = BeautifulSoup(html, "lxml")

    title = soup.title.string.strip() if soup.title and soup.title.string else ""
    meta_desc_tag = soup.find("meta", attrs={"name": "description"})
    meta_description = meta_desc_tag["content"].strip() if meta_desc_tag and meta_desc_tag.get("content") else ""

    headings = {f"h{i}": [h.get_text(strip=True) for h in soup.find_all(f"h{i}")] for i in range(1, 4)}

    # Structured data (schema.org) — huge signal for AI engines
    json_ld_blocks = soup.find_all("script", attrs={"type": "application/ld+json"})
    schema_types = []
    for block in json_ld_blocks:
        text = block.get_text()
        for match in re.findall(r'"@type"\s*:\s*"([A-Za-z]+)"', text):
            schema_types.append(match)

    has_faq_schema = any(t.lower() == "faqpage" for t in schema_types)
    has_article_schema = any(t.lower() in ("article", "newsarticle", "blogposting") for t in schema_types)
    has_organization_schema = any(t.lower() in ("organization", "localbusiness") for t in schema_types)

    canonical_tag = soup.find("link", attrs={"rel": "canonical"})
    has_canonical = bool(canonical_tag and canonical_tag.get("href"))

    # llms.txt — emerging convention some AI crawlers look for
    llms_txt_link = soup.find("link", attrs={"rel": "llms-txt"})

    # Clean readable text via trafilatura (closest to what an AI engine actually parses)
    clean_text = trafilatura.extract(html, include_comments=False, include_tables=False) or ""
    word_count = len(clean_text.split())
    clean_text_excerpt = clean_text[:600]

    # Q&A style content detection (headings phrased as questions help AI extraction)
    all_headings = headings["h1"] + headings["h2"] + headings["h3"]
    question_headings = [h for h in all_headings if h.strip().endswith("?")]

    # Author / byline / date signals (E-E-A-T-like trust signals AI engines weigh)
    has_author_meta = bool(soup.find("meta", attrs={"name": "author"})) or bool(
        soup.find(attrs={"class": re.compile("author", re.I)})
    )
    has_date_meta = bool(
        soup.find("meta", attrs={"property": "article:published_time"})
        or soup.find("time")
    )

    domain = urlparse(base_url).netloc
    robots_analysis = analyze_robots(robots_txt)

    return {
        "url": base_url,
        "domain": domain,
        "title": title,
        "title_length": len(title),
        "meta_description": meta_description,
        "meta_description_length": len(meta_description),
        "h1_count": len(headings["h1"]),
        "headings": headings,
        "schema_types": list(set(schema_types)),
        "has_faq_schema": has_faq_schema,
        "has_article_schema": has_article_schema,
        "has_organization_schema": has_organization_schema,
        "has_canonical": has_canonical,
        "has_llms_txt_link": bool(llms_txt_link),
        "clean_text_word_count": word_count,
        "clean_text_excerpt": clean_text_excerpt,
        "question_headings_count": len(question_headings),
        "has_author_signal": has_author_meta,
        "has_date_signal": has_date_meta,
        "has_https": base_url.startswith("https://"),
        **robots_analysis,
    }


async def scrape_website(url: str) -> dict:
    html, robots_txt = await fetch(url)
    return extract_signals(html, url, robots_txt)
