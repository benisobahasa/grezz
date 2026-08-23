"""
GEO Rule Engine — checks that determine how "readable" and "citable" a page
is to AI answer engines (ChatGPT, Gemini, Perplexity, etc), distinct from
classic SEO which optimizes for ranking in a list of blue links.
"""
import uuid
from dataclasses import dataclass
from typing import Callable

CATEGORIES = ["AI Crawlability", "Structured Data", "Content Clarity", "Trust Signals", "Technical Basics"]


@dataclass
class Rule:
    id: str
    category: str
    title: str
    weight: int
    check: Callable[[dict], bool]
    severity: str
    description: str
    fix: str


RULES: list[Rule] = [
    Rule("ai_bots_not_blocked", "AI Crawlability", "AI crawlers are not blocked in robots.txt", 30,
         lambda d: len(d["ai_bots_blocked"]) == 0, "critical",
         "robots.txt is blocking one or more AI crawlers (GPTBot, PerplexityBot, etc), so your content can't be indexed by AI search.",
         "Open robots.txt and remove the Disallow rule for the relevant AI crawler user-agents."),
    Rule("llms_txt", "AI Crawlability", "llms.txt is available", 10,
         lambda d: d["has_llms_txt_link"], "info",
         "No llms.txt found — an emerging convention that helps AI understand your site's content structure.",
         "Add an llms.txt file at your domain root with a summary and links to key pages."),
    Rule("https_enabled", "AI Crawlability", "Uses HTTPS", 15,
         lambda d: d["has_https"], "critical",
         "The website isn't using HTTPS.", "Enable SSL/HTTPS on your hosting."),
    Rule("schema_organization", "Structured Data", "Has Organization/LocalBusiness schema", 20,
         lambda d: d["has_organization_schema"], "warning",
         "No Organization structured data found, making it harder for AI to recognize your business identity.",
         "Add JSON-LD Organization schema with your name, logo, and official contact info."),
    Rule("schema_article", "Structured Data", "Has Article/BlogPosting schema (for content pages)", 15,
         lambda d: d["has_article_schema"], "info",
         "Content pages don't use Article schema yet, reducing the chance of being cited by AI with proper attribution.",
         "Add JSON-LD Article schema with headline, author, and datePublished."),
    Rule("schema_faq", "Structured Data", "Has FAQPage schema", 15,
         lambda d: d["has_faq_schema"], "info",
         "No FAQPage schema found — this is the format AI engines favor most for answering questions directly.",
         "Add an FAQ section marked up with JSON-LD FAQPage."),
    Rule("canonical_tag", "Structured Data", "Has canonical tag", 10,
         lambda d: d["has_canonical"], "warning",
         "No canonical tag found, risking source duplication in the eyes of AI crawlers.",
         "Add a <link rel=\"canonical\"> tag on every page."),
    Rule("title_present", "Content Clarity", "Title is clear and well-sized", 15,
         lambda d: bool(d["title"]) and 10 <= d["title_length"] <= 70, "critical",
         "Title is empty or its length isn't ideal.", "Write a 10-70 character title that clearly describes the page."),
    Rule("meta_description", "Content Clarity", "Meta description is clear", 10,
         lambda d: 50 <= d["meta_description_length"] <= 160, "warning",
         "Meta description is empty or outside the ideal range.", "Write a 50-160 character meta description."),
    Rule("single_h1", "Content Clarity", "Correct H1 structure", 10,
         lambda d: d["h1_count"] == 1, "warning",
         "The page doesn't have exactly one H1.", "Make sure every page has exactly one clear H1."),
    Rule("sufficient_content", "Content Clarity", "Content is substantial enough (>= 300 clean words)", 20,
         lambda d: d["clean_text_word_count"] >= 300, "warning",
         "Clean content (excluding nav/ads) is under 300 words — too thin to be cited by AI as a source.",
         "Deepen your content with explanations, data, and clear context."),
    Rule("question_style_headings", "Content Clarity", "Has question-style headings", 15,
         lambda d: d["question_headings_count"] > 0, "info",
         "No question-style headings found, even though this format is the easiest for AI to extract as a direct answer.",
         "Rephrase some subheadings as questions, e.g. 'What is X?', followed by a short answer in the first paragraph."),
    Rule("author_signal", "Trust Signals", "Has an author signal", 15,
         lambda d: d["has_author_signal"], "info",
         "No author information detected.", "Display the writer's name or editorial team on your content."),
    Rule("date_signal", "Trust Signals", "Has a publish/update date", 15,
         lambda d: d["has_date_signal"], "info",
         "No publish date detected.", "Show a publish date or last-updated date."),
    Rule("robots_found", "Technical Basics", "robots.txt is found", 10,
         lambda d: d["robots_found"], "warning",
         "No robots.txt found at this domain.", "Add a robots.txt file at your domain root."),
]


def run_rule_engine(extracted: dict) -> dict:
    cat_max = {c: 0 for c in CATEGORIES}
    cat_earned = {c: 0 for c in CATEGORIES}
    issues = []
    rule_results = []

    for rule in RULES:
        cat_max[rule.category] += rule.weight
        passed = bool(rule.check(extracted))
        rule_results.append({"rule": rule, "passed": passed})
        if passed:
            cat_earned[rule.category] += rule.weight
        else:
            issues.append({
                "id": str(uuid.uuid4())[:8],
                "rule_id": rule.id,
                "category": rule.category,
                "title": rule.title,
                "severity": rule.severity,
                "description": rule.description,
                "fix": rule.fix,
            })

    category_scores = {c: round((cat_earned[c] / (cat_max[c] or 1)) * 100) for c in CATEGORIES}
    return {"category_scores": category_scores, "issues": issues, "rule_results": rule_results}
