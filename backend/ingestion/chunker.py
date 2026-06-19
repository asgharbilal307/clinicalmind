"""
Metadata tagger and text chunker for clinical evidence.
"""
import re
from dataclasses import dataclass
from typing import List, Optional

from backend.config import settings
from backend.models.schemas import EvidenceSource


@dataclass
class Chunk:
    """A chunk of text with metadata."""
    text: str
    pmid: str
    source_title: str
    chunk_index: int
    total_chunks: int
    keywords: List[str]
    section_type: Optional[str] = None


class MetadataTagger:
    """Extracts keywords and identifies section types from clinical text."""

    # Clinical keyword patterns
    KEYWORD_PATTERNS = {
        "study_design": [
            r"\b(randomized|controlled|double-blind|single-blind|"
            r"crossover|parallel|cluster|observational|cohort|case-control|"
            r"cross-sectional|prospective|retrospective)\b",
        ],
        "intervention": [
            r"\b(treatment|therapy|intervention|drug|medication|"
            r"placebo|surgery|procedure|protocol)\b",
        ],
        "outcome": [
            r"\b(outcome|efficacy|safety|effectiveness|response|"
            r"remission|recurrence|survival|mortality)\b",
        ],
        "population": [
            r"\b(patient|subjects|participants|cohort|group|control|"
            r"pediatric|adult|elderly|women|men)\b",
        ],
        "statistics": [
            r"\b(p-value|significance|confidence interval|odds ratio|"
            r"hazard ratio|relative risk|mean|median|standard deviation|"
            r"correlation|regression)\b",
        ],
    }

    # Section patterns commonly found in abstracts
    SECTION_PATTERNS = {
        "background": [
            r"^BACKGROUND[:\s]",
            r"^OBJECTIVE[S]?[:\s]",
        ],
        "methods": [
            r"^METHODS[:\s]",
            r"^MATERIALS? AND METHODS[:\s]",
        ],
        "results": [
            r"^RESULTS[:\s]",
        ],
        "conclusions": [
            r"^CONCLUSIONS?[:\s]",
        ],
    }

    def extract_keywords(self, text: str) -> List[str]:
        """Extract clinical keywords from text."""
        text_lower = text.lower()
        keywords = set()

        for category, patterns in self.KEYWORD_PATTERNS.items():
            for pattern in patterns:
                matches = re.findall(pattern, text_lower, re.IGNORECASE)
                keywords.update(matches)

        return sorted(list(keywords))

    def identify_section(self, text: str) -> Optional[str]:
        """Identify which section of an abstract this text belongs to."""
        text_start = text[:200]  # Check start of chunk

        for section, patterns in self.SECTION_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, text_start, re.IGNORECASE | re.MULTILINE):
                    return section

        return None


class TextChunker:
    """Chunks text into overlapping segments for embedding."""

    def __init__(self):
        self.chunk_size = settings.chunk_size
        self.chunk_overlap = settings.chunk_overlap

    def chunk_text(
        self,
        text: str,
        pmid: str,
        source_title: str,
        metadata_tagger: Optional[MetadataTagger] = None
    ) -> List[Chunk]:
        """
        Chunk text into overlapping segments.

        Args:
            text: Text to chunk
            pmid: PubMed ID of source
            source_title: Title of the source article
            metadata_tagger: Optional tagger for metadata extraction

        Returns:
            List of Chunk objects
        """
        if not text.strip():
            return []

        if metadata_tagger is None:
            metadata_tagger = MetadataTagger()

        # Clean text
        text = self._clean_text(text)

        # Simple chunking by sentences or fixed size
        chunks = []
        start = 0
        text_len = len(text)
        chunk_index = 0

        while start < text_len:
            end = start + self.chunk_size

            # Try to break at sentence boundary
            if end < text_len:
                # Look for sentence ending within the last 100 chars
                sentence_search = text[max(0, end - 100):end]
                last_period = max(
                    sentence_search.rfind('. '),
                    sentence_search.rfind('.')
                )
                if last_period != -1:
                    end = max(0, end - 100) + last_period + 1

            chunk_text = text[start:end].strip()
            if chunk_text:
                keywords = metadata_tagger.extract_keywords(chunk_text)
                section_type = metadata_tagger.identify_section(chunk_text)

                chunks.append(Chunk(
                    text=chunk_text,
                    pmid=pmid,
                    source_title=source_title,
                    chunk_index=chunk_index,
                    total_chunks=0,  # Will be updated after all chunks
                    keywords=keywords,
                    section_type=section_type
                ))
                chunk_index += 1

            start = end - self.chunk_overlap
            if start >= text_len:
                break

        # Update total_chunks
        total = len(chunks)
        for chunk in chunks:
            chunk.total_chunks = total

        return chunks

    def chunk_evidence(
        self,
        evidence: EvidenceSource,
        metadata_tagger: Optional[MetadataTagger] = None
    ) -> List[Chunk]:
        """
        Chunk an EvidenceSource into text chunks.

        Args:
            evidence: EvidenceSource object
            metadata_tagger: Optional tagger for metadata extraction

        Returns:
            List of Chunk objects
        """
        # Combine title and abstract for better context
        full_text = f"{evidence.title}. {evidence.abstract}"

        return self.chunk_text(
            text=full_text,
            pmid=evidence.pmid,
            source_title=evidence.title,
            metadata_tagger=metadata_tagger
        )

    def _clean_text(self, text: str) -> str:
        """Clean and normalize text."""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove special characters but keep punctuation
        text = re.sub(r'[^\w\s.,;:%()\-–—]', '', text)
        return text.strip()


class ClinicalChunker:
    """Combined chunker for clinical evidence pipeline."""

    def __init__(self):
        self.chunker = TextChunker()
        self.tagger = MetadataTagger()

    def chunk_evidence(self, evidence: EvidenceSource) -> List[Chunk]:
        """Chunk evidence with metadata tagging."""
        return self.chunker.chunk_evidence(
            evidence=evidence,
            metadata_tagger=self.tagger
        )

    def chunk_batch(
        self,
        evidence_list: List[EvidenceSource]
    ) -> List[Chunk]:
        """Chunk multiple EvidenceSource objects."""
        all_chunks = []
        for evidence in evidence_list:
            chunks = self.chunk_evidence(evidence)
            all_chunks.extend(chunks)
        return all_chunks