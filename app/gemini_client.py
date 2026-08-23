"""
Gemini integration. The AI acts as a GEO (Generative Engine Optimization)
consultant that explains the Rule Engine's findings in plain language — it
does NOT invent facts about the site, it explains real extracted data and
real rule results. Uses the Google AI Studio free-tier API via the official
google-genai SDK.
"""
import json
import logging

from google import genai

from app.config import settings

logger = logging.getLogger(__name__)
_client = None


def get_client():
    global _client
    if not settings.GEMINI_API_KEY:
        return None
    if _client is None:
        _client = genai.Client(api_key=settings.GEMINI_API_KEY)
    return _client


SUMMARY_PROMPT = """You are a sharp, friendly GEO (Generative Engine Optimization) consultant.
Here is the automated analysis of a website's readiness for AI search engines (ChatGPT, Gemini, Perplexity):

URL: {url}
GEO Score: {score}/100
Category scores: {category_scores}
Main issues found: {issues}
Priority recommendations: {recommendations}

Write a short summary (max 130 words, English) explaining this site's standing in the eyes of
AI search engines, the 2 most critical gaps and why they matter, closing with the single
highest-impact next step. Supportive consultant tone, not a robotic list-reader."""


async def generate_summary(url, score, category_scores, issues, recommendations):
    client = get_client()
    if client is None:
        return _fallback(score, recommendations)
    prompt = SUMMARY_PROMPT.format(
        url=url, score=score,
        category_scores=json.dumps(category_scores, ensure_ascii=False),
        issues=json.dumps([i["title"] for i in issues], ensure_ascii=False),
        recommendations=json.dumps([r["title"] for r in recommendations[:5]], ensure_ascii=False),
    )
    try:
        resp = client.models.generate_content(model=settings.GEMINI_MODEL, contents=prompt)
        return (resp.text or "").strip() or _fallback(score, recommendations)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Gemini error: %s", exc)
        return _fallback(score, recommendations)


def _fallback(score, recommendations):
    top = recommendations[0]["title"] if recommendations else "no major issues detected"
    return f"This site's GEO Score is {score}/100. Top priority: {top}."


REWRITE_PROMPT = """You are an expert SEO/GEO copywriter. This website has a title and meta
description that are underperforming for AI search engines.

URL: {url}
Current title: "{title}"
Current meta description: "{meta_description}"
Page topic/content (short hint of what the page is about): {content_hint}

Write an IMPROVED version in English (unless the domain is clearly non-English, in which case
match that language), with strict rules:
- New title: 10-70 characters, clear, contains the core topic
- New meta description: 50-160 characters, answers "what is this page about" directly in the
  first sentence (this style is easiest for AI search to quote)
Reply ONLY in this exact JSON format, no markdown, no extra explanation:
{{"title": "...", "meta_description": "..."}}"""


async def generate_meta_suggestions(url: str, title: str, meta_description: str, content_hint: str) -> dict | None:
    client = get_client()
    if client is None:
        return None
    prompt = REWRITE_PROMPT.format(
        url=url,
        title=title or "(empty)",
        meta_description=meta_description or "(empty)",
        content_hint=content_hint[:400],
    )
    try:
        resp = client.models.generate_content(model=settings.GEMINI_MODEL, contents=prompt)
        text = (resp.text or "").strip()
        text = text.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        data = json.loads(text)
        if "title" in data and "meta_description" in data:
            return data
    except Exception as exc:  # noqa: BLE001
        logger.warning("Gemini rewrite error: %s", exc)
    return None


FAQ_PROMPT = """You are a GEO consultant helping a website become more citable by AI search engines.
FAQPage structured data is one of the strongest signals for this, and this page doesn't have one yet.

URL: {url}
Page content excerpt: {content_hint}

Based ONLY on the actual content excerpt above, write 3 to 5 genuinely useful FAQ question/answer
pairs this page could add (don't invent facts not supported by the excerpt — if the excerpt is too
thin to support a fact-based answer, write a more general question about the page's topic instead).
Each answer should be 1-2 sentences, direct, and quotable on its own.
Reply ONLY in this exact JSON format, no markdown, no extra explanation:
{{"faqs": [{{"question": "...", "answer": "..."}}, ...]}}"""


async def generate_faq_suggestions(url: str, content_hint: str) -> list[dict] | None:
    client = get_client()
    if client is None or not content_hint.strip():
        return None
    prompt = FAQ_PROMPT.format(url=url, content_hint=content_hint[:1200])
    try:
        resp = client.models.generate_content(model=settings.GEMINI_MODEL, contents=prompt)
        text = (resp.text or "").strip()
        text = text.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        data = json.loads(text)
        faqs = data.get("faqs")
        if faqs and isinstance(faqs, list):
            return faqs[:5]
    except Exception as exc:  # noqa: BLE001
        logger.warning("Gemini FAQ generation error: %s", exc)
    return None


ASK_PROMPT = """You are a GEO (Generative Engine Optimization) consultant named Grezz AI.
You're helping someone understand the GEO Score analysis for this website:

URL: {url}
GEO Score: {score}/100
Category scores: {category_scores}
Issues found: {issues}
Priority recommendations: {recommendations}

User's question: "{question}"

Answer briefly (max 100 words), in English, specifically based on the analysis data above (don't
invent new facts about this website beyond the data given). Friendly tone, like a consultant who
gets straight to the point."""


async def answer_followup(url, score, category_scores, issues, recommendations, question: str) -> str:
    client = get_client()
    if client is None:
        return "The AI Q&A feature requires an active GEMINI_API_KEY. Please contact the site admin."
    prompt = ASK_PROMPT.format(
        url=url, score=score,
        category_scores=json.dumps(category_scores, ensure_ascii=False),
        issues=json.dumps([i["title"] for i in issues], ensure_ascii=False),
        recommendations=json.dumps([r["title"] for r in recommendations[:5]], ensure_ascii=False),
        question=question[:500],
    )
    try:
        resp = client.models.generate_content(model=settings.GEMINI_MODEL, contents=prompt)
        return (resp.text or "").strip() or "Sorry, I can't answer that right now. Try another question?"
    except Exception as exc:  # noqa: BLE001
        logger.warning("Gemini ask error: %s", exc)
        return "Sorry, there was an issue reaching the AI. Please try again shortly."
