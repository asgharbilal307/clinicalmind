"""
PDF export for ClinicalMind debate results.
Generates a clean, professional research brief using reportlab.
"""
from io import BytesIO
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor, white, black
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether,
)
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT

from backend.models.schemas import DebateOutput, StanceResult

# --- Palette matching ClinicalMind UI ---
INK        = HexColor("#1A2332")
INK_SOFT   = HexColor("#4A5568")
PAPER      = HexColor("#FAFAF7")
SUPPORT    = HexColor("#0F6E56")
SUPPORT_BG = HexColor("#E8F5F0")
CONTRADICT = HexColor("#B8462F")
CONTRA_BG  = HexColor("#FBEEE9")
NEUTRAL    = HexColor("#8B8578")
VERDICT_BG = HexColor("#FBF1DF")
VERDICT    = HexColor("#9C6B1F")
BORDER     = HexColor("#E2E0D8")


def _styles() -> dict:
    """Return a dict of named ParagraphStyles."""
    base = dict(fontName="Helvetica", textColor=INK, leading=14)
    return {
        "title": ParagraphStyle(
            "title", fontName="Helvetica-Bold", fontSize=18,
            textColor=INK, leading=22, spaceAfter=4,
        ),
        "subtitle": ParagraphStyle(
            "subtitle", fontName="Helvetica", fontSize=10,
            textColor=INK_SOFT, leading=14, spaceAfter=2,
        ),
        "section": ParagraphStyle(
            "section", fontName="Helvetica-Bold", fontSize=9,
            textColor=INK_SOFT, leading=12, spaceBefore=14, spaceAfter=4,
            textTransform="uppercase", letterSpacing=0.8,
        ),
        "body": ParagraphStyle(
            "body", fontName="Helvetica", fontSize=9,
            textColor=INK, leading=14, spaceAfter=4,
        ),
        "mono": ParagraphStyle(
            "mono", fontName="Courier", fontSize=8,
            textColor=INK_SOFT, leading=12,
        ),
        "verdict": ParagraphStyle(
            "verdict", fontName="Helvetica", fontSize=9,
            textColor=INK, leading=14, spaceAfter=0,
            backColor=VERDICT_BG, borderPadding=(6, 8, 6, 8),
        ),
        "warning": ParagraphStyle(
            "warning", fontName="Helvetica", fontSize=9,
            textColor=HexColor("#5C4A0A"), leading=14, spaceAfter=0,
        ),
        "study_title": ParagraphStyle(
            "study_title", fontName="Helvetica-Bold", fontSize=8,
            textColor=INK, leading=11,
        ),
        "study_body": ParagraphStyle(
            "study_body", fontName="Helvetica", fontSize=7.5,
            textColor=INK_SOFT, leading=11,
        ),
        "footer": ParagraphStyle(
            "footer", fontName="Helvetica", fontSize=7,
            textColor=INK_SOFT, leading=10, alignment=TA_CENTER,
        ),
    }


def _study_rows(studies: list[StanceResult], stance: str, styles: dict) -> list:
    """Build table rows for one camp of studies."""
    color = SUPPORT if stance == "SUPPORTS" else CONTRADICT if stance == "CONTRADICTS" else NEUTRAL
    rows = []
    for s in studies:
        pmid_line = f"PMID {s.pmid}"
        if s.year:
            pmid_line += f"  ·  {s.year}"
        if s.journal:
            pmid_line += f"  ·  {s.journal}"
        if s.sample_size:
            pmid_line += f"  ·  n={s.sample_size:,}"
        if s.quality_score and s.quality_score != "unknown":
            pmid_line += f"  ·  {s.quality_score} quality"
        if s.funding_source and s.funding_source != "unknown":
            pmid_line += f"  ·  {s.funding_source}-funded"

        title_para = Paragraph(s.title[:120] + ("…" if len(s.title) > 120 else ""), styles["study_title"])
        claim_para = Paragraph(s.claim[:200] + ("…" if len(s.claim) > 200 else ""), styles["study_body"])
        meta_para  = Paragraph(pmid_line, styles["mono"])
        reason_para = Paragraph(f"Reason: {s.reason[:150]}", styles["study_body"]) if s.reason else Spacer(1, 0)

        conf_pct = f"{round(s.confidence * 100)}%"

        rows.append([
            Paragraph(stance, ParagraphStyle(
                "badge", fontName="Helvetica-Bold", fontSize=7,
                textColor=white, leading=9,
            )),
            [title_para, Spacer(1, 2), claim_para, Spacer(1, 2), meta_para, reason_para],
            Paragraph(conf_pct, ParagraphStyle(
                "conf", fontName="Courier", fontSize=8,
                textColor=INK_SOFT, leading=10, alignment=TA_RIGHT,
            )),
        ])
    return rows


def generate_pdf(debate: DebateOutput) -> bytes:
    """
    Generate a PDF research brief for a ClinicalMind debate result.
    Returns raw PDF bytes.
    """
    buf = BytesIO()
    margin = 18 * mm
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=margin,
        rightMargin=margin,
        topMargin=margin,
        bottomMargin=margin + 8 * mm,
        title=f"ClinicalMind — {debate.query[:60]}",
        author="ClinicalMind Evidence Intelligence",
    )

    st = _styles()
    story = []
    W = A4[0] - 2 * margin  # usable width

    # ── Header ──────────────────────────────────────────────────────────────
    story.append(Paragraph("ClinicalMind", ParagraphStyle(
        "brand", fontName="Helvetica-Bold", fontSize=11,
        textColor=SUPPORT, leading=14,
    )))
    story.append(Paragraph("Evidence Intelligence Platform", st["subtitle"]))
    story.append(HRFlowable(width="100%", thickness=0.5, color=BORDER, spaceAfter=10))

    # ── Query ────────────────────────────────────────────────────────────────
    story.append(Paragraph(debate.query, st["title"]))
    story.append(Paragraph(
        f"Generated {datetime.now().strftime('%d %B %Y')}  ·  "
        f"{debate.total_studies} studies retrieved",
        st["subtitle"],
    ))
    story.append(Spacer(1, 8))

    # ── Consensus verdict ────────────────────────────────────────────────────
    story.append(Paragraph("Consensus", st["section"]))
    consensus_table = Table(
        [[
            Paragraph(debate.consensus_strength, ParagraphStyle(
                "cs", fontName="Helvetica-Bold", fontSize=11,
                textColor=VERDICT, leading=14,
            )),
            Paragraph(
                f"{len(debate.supporting)} supporting  ·  "
                f"{len(debate.contradicting)} contradicting  ·  "
                f"{len(debate.neutral)} neutral",
                ParagraphStyle("counts", fontName="Helvetica", fontSize=9,
                               textColor=INK_SOFT, leading=12, alignment=TA_RIGHT),
            ),
        ]],
        colWidths=[W * 0.55, W * 0.45],
    )
    consensus_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), VERDICT_BG),
        ("ROUNDEDCORNERS", [4]),
        ("BOX", (0, 0), (-1, -1), 0.5, HexColor("#E8C870")),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(consensus_table)
    story.append(Spacer(1, 8))

    # ── Conflict explanation ─────────────────────────────────────────────────
    if debate.conflict_explanation:
        story.append(Paragraph("Why the evidence disagrees", st["section"]))
        story.append(Paragraph(debate.conflict_explanation, st["body"]))

    # ── Verdict ──────────────────────────────────────────────────────────────
    if debate.verdict:
        story.append(Paragraph("Referee's verdict", st["section"]))
        story.append(Paragraph(debate.verdict, st["body"]))

    # ── Funding bias warning ─────────────────────────────────────────────────
    if getattr(debate, "funding_bias", None) and debate.funding_bias.bias_flag and debate.funding_bias.bias_note:
        story.append(Spacer(1, 4))
        bias_table = Table(
            [[Paragraph(f"⚠ Funding bias: {debate.funding_bias.bias_note}", st["warning"])]],
            colWidths=[W],
        )
        bias_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), HexColor("#FFF8E8")),
            ("BOX", (0, 0), (-1, -1), 0.5, HexColor("#F0D080")),
            ("TOPPADDING", (0, 0), (-1, -1), 7),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ]))
        story.append(bias_table)
        story.append(Spacer(1, 8))

    # ── Study tables ─────────────────────────────────────────────────────────
    def _study_table(studies: list[StanceResult], stance: str, bg: object, border: object):
        if not studies:
            return
        label = "Supporting evidence" if stance == "SUPPORTS" else \
                "Contradicting evidence" if stance == "CONTRADICTS" else "Neutral / inconclusive"
        story.append(Paragraph(label, st["section"]))

        rows = _study_rows(studies, stance, st)
        col_w = [12 * mm, W - 12 * mm - 12 * mm, 12 * mm]
        t = Table(rows, colWidths=col_w, repeatRows=0)
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (0, -1), bg),
            ("TEXTCOLOR", (0, 0), (0, -1), white),
            ("ALIGN", (0, 0), (0, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("LINEBELOW", (0, 0), (-1, -2), 0.3, BORDER),
            ("BOX", (0, 0), (-1, -1), 0.5, border),
            ("ROWBACKGROUNDS", (1, 0), (-1, -1), [white, HexColor("#F8F8F6")]),
        ]))
        story.append(t)
        story.append(Spacer(1, 8))

    _study_table(debate.supporting, "SUPPORTS", SUPPORT, HexColor("#C8E8DF"))
    _study_table(debate.contradicting, "CONTRADICTS", CONTRADICT, HexColor("#F0C8BE"))
    if debate.neutral:
        _study_table(debate.neutral, "NEUTRAL", NEUTRAL, BORDER)

    # ── Footer ────────────────────────────────────────────────────────────────
    story.append(HRFlowable(width="100%", thickness=0.5, color=BORDER, spaceBefore=8))
    story.append(Paragraph(
        "Generated by ClinicalMind · Evidence Intelligence Platform · "
        "This report is for informational purposes only and does not constitute medical advice. "
        "All studies link to PubMed via PMID.",
        st["footer"],
    ))

    doc.build(story)
    return buf.getvalue()