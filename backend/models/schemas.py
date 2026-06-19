from pydantic import BaseModel, Field
from typing import Optional, Literal
from enum import Enum


class StudyType(str, Enum):
    META_ANALYSIS = "meta-analysis"
    SYSTEMATIC_REVIEW = "systematic-review"
    RCT = "rct"
    COHORT = "cohort"
    CASE_CONTROL = "case-control"
    CASE_REPORT = "case-report"
    UNKNOWN = "unknown"


# Weight per study type — used in consensus scoring (Phase 2)
STUDY_TYPE_WEIGHTS = {
    StudyType.META_ANALYSIS: 10,
    StudyType.SYSTEMATIC_REVIEW: 9,
    StudyType.RCT: 8,
    StudyType.COHORT: 6,
    StudyType.CASE_CONTROL: 4,
    StudyType.CASE_REPORT: 1,
    StudyType.UNKNOWN: 3,
}


class Abstract(BaseModel):
    pmid: str
    title: str
    abstract: str
    year: Optional[int] = None
    journal: Optional[str] = None
    authors: list[str] = []
    study_type: StudyType = StudyType.UNKNOWN
    sample_size: Optional[int] = None


class Claim(BaseModel):
    pmid: str
    claim: str
    direction: Literal["positive", "negative", "null", "unknown"] = "unknown"
    outcome: Optional[str] = None


class StanceResult(BaseModel):
    pmid: str
    title: str
    year: Optional[int]
    journal: Optional[str]
    study_type: StudyType
    sample_size: Optional[int]
    claim: str
    stance: Literal["SUPPORTS", "CONTRADICTS", "NEUTRAL"]
    confidence: float = Field(ge=0.0, le=1.0)
    reason: str


class ConsensusStrength(str, Enum):
    STRONG_SUPPORT = "Strong support"
    MODERATE_SUPPORT = "Moderate support"
    WEAK_SUPPORT = "Weak support"
    CONTESTED = "Contested"
    INSUFFICIENT = "Insufficient evidence"


class DebateOutput(BaseModel):
    query: str
    consensus_strength: ConsensusStrength
    supporting: list[StanceResult]
    contradicting: list[StanceResult]
    neutral: list[StanceResult]
    conflict_explanation: str
    verdict: str
    total_studies: int


# --- Request / Response schemas for API ---

class IngestRequest(BaseModel):
    topic: str = Field(..., description="Medical topic to search PubMed for")
    max_results: int = Field(default=100, le=200)


class IngestResponse(BaseModel):
    topic: str
    abstracts_fetched: int
    abstracts_stored: int
    claims_extracted: int
    message: str


class DebateRequest(BaseModel):
    query: str = Field(..., description="Clinical question to debate")
    top_k: int = Field(default=20, le=40)