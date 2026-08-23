import logging
from pathlib import Path

from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.config import settings
from app import cache
from app.scraper import scrape_website, ScrapeError
from app.rule_engine import run_rule_engine
from app.scoring import compute_geo_score, score_label
from app.priority_engine import build_recommendations
from app.gemini_client import generate_summary, generate_meta_suggestions, answer_followup, generate_faq_suggestions
from app.security import analyze_rate_limiter, ask_rate_limiter, client_ip

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(title=settings.APP_NAME)
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    forwarded_proto = request.headers.get("x-forwarded-proto", request.url.scheme)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    if forwarded_proto == "https":
        response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' https://cdn.tailwindcss.com https://unpkg.com "
        "https://pagead2.googlesyndication.com https://www.googletagservices.com; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src https://fonts.gstatic.com; "
        "img-src 'self' data: https:; "
        "connect-src 'self'; "
        "frame-src https://googleads.g.doubleclick.net https://tpc.googlesyndication.com;"
    )
    return response


def ad_context() -> dict:
    return {
        "ads_enabled": settings.ADS_ENABLED,
        "adsense_client_id": settings.ADSENSE_CLIENT_ID,
        "ad_slot_header": settings.AD_SLOT_HEADER,
        "ad_slot_sidebar": settings.AD_SLOT_SIDEBAR,
        "ad_slot_incontent": settings.AD_SLOT_INCONTENT,
        "ad_slot_native": settings.AD_SLOT_NATIVE,
        "ad_slot_footer": settings.AD_SLOT_FOOTER,
        "ad_slot_sticky": settings.AD_SLOT_STICKY,
    }


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "app_name": settings.APP_NAME, "tagline": settings.TAGLINE, **ad_context()},
    )


@app.post("/analyze", response_class=HTMLResponse)
async def analyze(request: Request, url: str = Form(...)):
    if not analyze_rate_limiter.check(client_ip(request)):
        return templates.TemplateResponse(
            "partials/error.html",
            {"request": request, "message": "Too many requests. Please try again in a minute."},
        )

    url = url.strip()
    if not url.startswith("http"):
        url = "https://" + url

    cached = cache.get(url)
    if cached:
        extracted, engine_result, score, recommendations = cached
    else:
        try:
            extracted = await scrape_website(url)
        except ScrapeError as exc:
            return templates.TemplateResponse(
                "partials/error.html", {"request": request, "message": str(exc)}
            )
        engine_result = run_rule_engine(extracted)
        score = compute_geo_score(engine_result["category_scores"])
        recommendations = build_recommendations(engine_result["rule_results"])
        cache.set(url, (extracted, engine_result, score, recommendations))

    ai_summary = await generate_summary(
        url, score, engine_result["category_scores"], engine_result["issues"], recommendations
    )

    meta_suggestion = None
    needs_rewrite = extracted["title_length"] == 0 or not (50 <= extracted["meta_description_length"] <= 160)
    if needs_rewrite:
        meta_suggestion = await generate_meta_suggestions(
            url, extracted.get("title", ""), extracted.get("meta_description", ""),
            extracted.get("clean_text_excerpt", ""),
        )

    faq_suggestions = None
    if not extracted.get("has_faq_schema"):
        faq_suggestions = await generate_faq_suggestions(url, extracted.get("clean_text_excerpt", ""))

    return templates.TemplateResponse(
        "partials/results.html",
        {
            "request": request,
            "url": url,
            "score": score,
            "score_label": score_label(score),
            "category_scores": engine_result["category_scores"],
            "issues": engine_result["issues"],
            "recommendations": recommendations,
            "ai_summary": ai_summary,
            "meta_suggestion": meta_suggestion,
            "faq_suggestions": faq_suggestions,
            "content_excerpt": extracted.get("clean_text_excerpt", ""),
            **ad_context(),
        },
    )


@app.post("/ask", response_class=HTMLResponse)
async def ask(request: Request, url: str = Form(...), question: str = Form(...)):
    if not ask_rate_limiter.check(client_ip(request)):
        return templates.TemplateResponse(
            "partials/chat_message.html",
            {"request": request, "question": question, "answer": "Too many questions. Please try again shortly."},
        )

    question = question.strip()[:500]
    cached = cache.get(url)
    if not cached:
        return templates.TemplateResponse(
            "partials/chat_message.html",
            {"request": request, "question": question, "answer": "Analysis data for this URL has expired. Please scan again."},
        )
    extracted, engine_result, score, recommendations = cached
    answer = await answer_followup(
        url, score, engine_result["category_scores"], engine_result["issues"], recommendations, question
    )
    return templates.TemplateResponse(
        "partials/chat_message.html",
        {"request": request, "question": question, "answer": answer},
    )


@app.get("/privacy", response_class=HTMLResponse)
async def privacy(request: Request):
    return templates.TemplateResponse(
        "privacy.html",
        {"request": request, "app_name": settings.APP_NAME, "tagline": settings.TAGLINE, **ad_context()},
    )


@app.get("/terms", response_class=HTMLResponse)
async def terms(request: Request):
    return templates.TemplateResponse(
        "terms.html",
        {"request": request, "app_name": settings.APP_NAME, "tagline": settings.TAGLINE, **ad_context()},
    )


@app.get("/robots.txt", response_class=PlainTextResponse)
async def robots_txt():
    return "User-agent: *\nAllow: /\nSitemap: /sitemap.xml\n"


@app.get("/sitemap.xml", response_class=PlainTextResponse)
async def sitemap_xml(request: Request):
    base = str(request.base_url).rstrip("/")
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        f"<url><loc>{base}/</loc></url>"
        f"<url><loc>{base}/privacy</loc></url>"
        f"<url><loc>{base}/terms</loc></url>"
        "</urlset>"
    )


@app.get("/health")
def health():
    return {"status": "healthy"}
