from typing import Dict, Any, List, Tuple
from io import BytesIO
import logging

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from docx import Document

logger = logging.getLogger(__name__)

DISCLAIMER = (
    "This report is AI-generated for informational purposes only and is not a "
    "medical diagnosis. Always consult a qualified healthcare professional."
)


class MedicalReportNode:
    async def __call__(self, state: dict) -> dict:
        logger.info("Medical report node called")
        state["current_workflow_stage"] = "generating_medical_report"
        state["medical_report"] = self._build_report_text(state)
        state["current_workflow_stage"] = "workflow_complete"
        return state

    def _build_sections(self, state: Dict[str, Any]) -> List[Tuple[str, str]]:
        """Trace the session as: reported symptoms -> initial assessment -> optional
        follow-up -> overall diagnosis -> severity -> recommended care. No timestamps,
        session IDs, or self-care/referral-timing instructions."""
        overall = state.get("overall_analysis", {}) or {}
        sections: List[Tuple[str, str]] = []

        sections.append(("Reported symptoms", state.get("userInput_symptoms") or "Not provided"))

        initial = (state.get("textual_analysis") or [{}])[0]
        initial_body = (
            f"{initial.get('text_diagnosis', 'Not determined')} "
            f"({(initial.get('diagnosis_confidence', 0.0) or 0.0) * 100:.0f}% confidence)"
        )
        if state.get("initial_diagnosis_reasoning"):
            initial_body += f"\n{state['initial_diagnosis_reasoning']}"
        sections.append(("Initial assessment", initial_body))

        followup_responses = state.get("followup_responses")
        if followup_responses:
            qna = "\n".join(f"Q: {q}\nA: {a}" for q, a in followup_responses.items())
            sections.append(("Follow-up", qna))

        overall_body = (
            f"{overall.get('final_diagnosis', 'Not determined')} "
            f"({(overall.get('final_confidence', 0.0) or 0.0) * 100:.0f}% confidence)"
        )
        if overall.get("user_explanation"):
            overall_body += f"\n{overall['user_explanation']}"
        if overall.get("clinical_reasoning"):
            overall_body += f"\n{overall['clinical_reasoning']}"
        sections.append(("Overall diagnosis", overall_body))

        sections.append(("Severity", (overall.get("final_severity") or "moderate").title()))
        sections.append(("Recommended care", overall.get("recommended_care_path") or "General Practitioner"))

        return sections

    def _build_report_text(self, state: Dict[str, Any]) -> str:
        lines = ["MEDICAL ANALYSIS REPORT", ""]
        for heading, body in self._build_sections(state):
            lines.append(heading.upper())
            lines.append(body)
            lines.append("")
        lines.append(DISCLAIMER)
        return "\n".join(lines)

    #==================================================
    # Medical Report Export Function
    #==================================================

    # Export functionality (only called from API endpoint). include_details is accepted
    # for API-signature compatibility with the caller; the report is already minimal so
    # there is no separate summary rendering.
    async def generate_export_file(self, state: dict, format: str, include_details: bool = True) -> bytes:
        if format == 'pdf':
            return self._generate_pdf_export(state)
        elif format == 'word':
            return self._generate_word_export(state)
        else:
            raise ValueError(f"Unsupported format: {format}")

    def _generate_pdf_export(self, state: Dict[str, Any]) -> bytes:
        try:
            buffer = BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=72, leftMargin=72,
                                     topMargin=72, bottomMargin=18)
            styles = getSampleStyleSheet()
            story = [Paragraph("Medical Analysis Report", styles['Title']), Spacer(1, 12)]

            for heading, body in self._build_sections(state):
                story.append(Paragraph(heading, styles['Heading2']))
                for line in body.split("\n"):
                    if line.strip():
                        story.append(Paragraph(line.strip(), styles['Normal']))
                story.append(Spacer(1, 10))

            story.append(Paragraph("Disclaimer", styles['Heading2']))
            story.append(Paragraph(DISCLAIMER, styles['Normal']))

            doc.build(story)
            buffer.seek(0)
            return buffer.getvalue()
        except Exception as e:
            logger.error(f"PDF generation failed: {e}")
            return self._build_report_text(state).encode('utf-8')

    def _generate_word_export(self, state: Dict[str, Any]) -> bytes:
        try:
            doc = Document()
            title = doc.add_heading('Medical Analysis Report', 0)
            title.alignment = 1  # Center alignment

            for heading, body in self._build_sections(state):
                doc.add_heading(heading, level=1)
                for line in body.split("\n"):
                    if line.strip():
                        doc.add_paragraph(line.strip())

            doc.add_heading('Disclaimer', level=1)
            doc.add_paragraph(DISCLAIMER)

            buffer = BytesIO()
            doc.save(buffer)
            buffer.seek(0)
            return buffer.getvalue()
        except Exception as e:
            logger.error(f"Word generation failed: {e}")
            return self._build_report_text(state).encode('utf-8')
