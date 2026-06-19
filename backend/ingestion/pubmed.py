import httpx
import asyncio
from lxml import etree
from typing import Optional
from backend.config import PUBMED_BASE_URL, PUBMED_API_KEY, PUBMED_MAX_RESULTS
from backend.models.schemas import Abstract, StudyType
import re


def _detect_study_type(title: str, abstract: str) -> StudyType:
    """Heuristic study type detection from title/abstract text."""
    text = (title + " " + abstract).lower()
    if "meta-analysis" in text or "meta analysis" in text:
        return StudyType.META_ANALYSIS
    if "systematic review" in text:
        return StudyType.SYSTEMATIC_REVIEW
    if ("randomized" in text or "randomised" in text) and (
        "controlled trial" in text or "clinical trial" in text
    ):
        return StudyType.RCT
    if "cohort" in text or "prospective" in text or "longitudinal" in text:
        return StudyType.COHORT
    if "case-control" in text or "case control" in text:
        return StudyType.CASE_CONTROL
    if "case report" in text or "case series" in text:
        return StudyType.CASE_REPORT
    return StudyType.UNKNOWN


def _extract_sample_size(abstract: str) -> Optional[int]:
    """Try to extract sample size from abstract text."""
    patterns = [
        r"n\s*=\s*(\d[\d,]*)",
        r"(\d[\d,]+)\s*(?:patients|participants|subjects|individuals|adults)",
        r"total\s+of\s+(\d[\d,]*)",
        r"enrolled\s+(\d[\d,]*)",
        r"included\s+(\d[\d,]*)\s*(?:patients|participants|subjects)",
    ]
    for pattern in patterns:
        match = re.search(pattern, abstract, re.IGNORECASE)
        if match:
            raw = match.group(1).replace(",", "")
            try:
                return int(raw)
            except ValueError:
                continue
    return None


async def search_pubmed(topic: str, max_results: int = PUBMED_MAX_RESULTS) -> list[str]:
    """Search PubMed and return list of PMIDs."""
    params = {
        "db": "pubmed",
        "term": topic,
        "retmax": max_results,
        "retmode": "json",
        "sort": "relevance",
    }
    if PUBMED_API_KEY:
        params["api_key"] = PUBMED_API_KEY

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(f"{PUBMED_BASE_URL}/esearch.fcgi", params=params)
        resp.raise_for_status()
        data = resp.json()
        return data.get("esearchresult", {}).get("idlist", [])


async def fetch_abstracts(pmids: list[str]) -> list[Abstract]:
    """Fetch full abstracts for a list of PMIDs in batches of 50."""
    abstracts = []
    batch_size = 50

    async with httpx.AsyncClient(timeout=60) as client:
        for i in range(0, len(pmids), batch_size):
            batch = pmids[i : i + batch_size]
            params = {
                "db": "pubmed",
                "id": ",".join(batch),
                "rettype": "abstract",
                "retmode": "xml",
            }
            if PUBMED_API_KEY:
                params["api_key"] = PUBMED_API_KEY

            resp = await client.get(f"{PUBMED_BASE_URL}/efetch.fcgi", params=params)
            resp.raise_for_status()

            parsed = _parse_pubmed_xml(resp.content)
            abstracts.extend(parsed)

            # Respect PubMed rate limit (3 req/sec without key, 10 with)
            await asyncio.sleep(0.4 if not PUBMED_API_KEY else 0.12)

    return abstracts


def _parse_pubmed_xml(xml_bytes: bytes) -> list[Abstract]:
    """Parse PubMed efetch XML response into Abstract objects."""
    root = etree.fromstring(xml_bytes)
    results = []

    for article in root.findall(".//PubmedArticle"):
        try:
            pmid_el = article.find(".//PMID")
            pmid = pmid_el.text if pmid_el is not None else None
            if not pmid:
                continue

            title_el = article.find(".//ArticleTitle")
            title = "".join(title_el.itertext()) if title_el is not None else ""

            abstract_els = article.findall(".//AbstractText")
            abstract = " ".join(
                "".join(el.itertext()) for el in abstract_els
            ).strip()

            if not abstract:
                continue

            year_el = article.find(".//PubDate/Year")
            year = int(year_el.text) if year_el is not None else None

            journal_el = article.find(".//Journal/Title")
            journal = journal_el.text if journal_el is not None else None

            authors = []
            for author in article.findall(".//Author"):
                last = author.findtext("LastName", "")
                fore = author.findtext("ForeName", "")
                if last:
                    authors.append(f"{last} {fore}".strip())

            study_type = _detect_study_type(title, abstract)
            sample_size = _extract_sample_size(abstract)

            results.append(
                Abstract(
                    pmid=pmid,
                    title=title,
                    abstract=abstract,
                    year=year,
                    journal=journal,
                    authors=authors[:5],
                    study_type=study_type,
                    sample_size=sample_size,
                )
            )
        except Exception:
            continue

    return results


async def fetch_topic(
    topic: str, max_results: int = PUBMED_MAX_RESULTS
) -> list[Abstract]:
    """Full pipeline: search → fetch → return abstracts."""
    pmids = await search_pubmed(topic, max_results)
    if not pmids:
        return []
    return await fetch_abstracts(pmids)