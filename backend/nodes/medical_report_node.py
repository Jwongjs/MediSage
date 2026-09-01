from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

# PDF/Word imports
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from docx import Document
from io import BytesIO

# Database imports
from supabase import Client
import os
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

class MedicalReportNode:
    def __init__(self, supabase_client: Optional[Client] = None):
        # Initialize Supabase client for database operations
        if supabase_client:
            self.supabase = supabase_client
        else:
            # Create client if not provided
            url = os.getenv("SUPABASE_URL")
            key = os.getenv("SUPABASE_API_KEY")
            if url and key:
                from supabase import create_client
                self.supabase = create_client(url, key)
            else:
                self.supabase = None
                logger.warning("Supabase credentials not found - database features disabled")

    # ================================
    # DATABASE STORAGE METHODS
    # ================================

    async def save_medical_report_to_database(
        self,
        user_id: str,
        session_id: str,
        agent_state: Dict[str, Any],
        report_title: Optional[str] = None
    ) -> Dict[str, Any]:
        """Save a complete medical report to the database"""

        if not self.supabase:
            raise Exception("Database not configured - Supabase client not available")

        try:
            # Extract data from agent state
            report_data = {
                "user_id": user_id,
                "session_id": session_id,
                "report_title": report_title or f"Medical Report - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                "patient_symptoms": agent_state.get("userInput_symptoms"),
                "textual_analysis": agent_state.get("textual_analysis"),
                "followup_data": {
                    "questions": agent_state.get("followup_questions"),
                    "responses": agent_state.get("followup_response"),
                    "qna_overall": agent_state.get("followup_qna_overall"),
                    "diagnosis": agent_state.get("followup_diagnosis")
                } if agent_state.get("followup_questions") else None,
                "image_analysis": agent_state.get("skin_lesion_analysis"),
                "overall_analysis": agent_state.get("overall_analysis"),
                "healthcare_recommendations": agent_state.get("healthcare_recommendation"),
                "medical_report_content": agent_state.get("medical_report"),
                "workflow_path": agent_state.get("workflow_path"),
                "workflow_stages_completed": agent_state.get("current_workflow_stage"),
            }

            # Remove None values
            report_data = {k: v for k, v in report_data.items() if v is not None}

            # Insert into database
            result = self.supabase.table("medical_reports").insert(report_data).execute()

            if result.data:
                logger.info(f"Medical report saved successfully for user {user_id}, session {session_id}")
                return result.data[0]
            else:
                raise Exception("Failed to save medical report")

        except Exception as e:
            logger.error(f"Error saving medical report: {e}")
            raise e

    async def get_user_medical_reports(
        self,
        user_id: str,
        limit: int = 10,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get all medical reports for a user"""

        if not self.supabase:
            raise Exception("Database not configured")

        try:
            result = self.supabase.table("medical_reports")\
                .select("*")\
                .eq("user_id", user_id)\
                .order("created_at", desc=True)\
                .range(offset, offset + limit - 1)\
                .execute()

            return result.data or []

        except Exception as e:
            logger.error(f"Error fetching medical reports: {e}")
            raise e

    async def get_medical_report_by_id(
        self,
        report_id: str,
        user_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get a specific medical report by ID"""

        if not self.supabase:
            raise Exception("Database not configured")

        try:
            result = self.supabase.table("medical_reports")\
                .select("*")\
                .eq("id", report_id)\
                .eq("user_id", user_id)\
                .execute()

            return result.data[0] if result.data else None

        except Exception as e:
            logger.error(f"Error fetching medical report: {e}")
            raise e

    async def delete_medical_report(
        self,
        report_id: str,
        user_id: str
    ) -> bool:
        """Delete a medical report"""

        if not self.supabase:
            raise Exception("Database not configured")

        try:
            result = self.supabase.table("medical_reports")\
                .delete()\
                .eq("id", report_id)\
                .eq("user_id", user_id)\
                .execute()

            return bool(result.data)

        except Exception as e:
            logger.error(f"Error deleting medical report: {e}")
            raise e

    async def update_report_title(
        self,
        report_id: str,
        user_id: str,
        new_title: str
    ) -> Dict[str, Any]:
        """Update medical report title"""

        if not self.supabase:
            raise Exception("Database not configured")

        try:
            result = self.supabase.table("medical_reports")\
                .update({"report_title": new_title})\
                .eq("id", report_id)\
                .eq("user_id", user_id)\
                .execute()

            return result.data[0] if result.data else None

        except Exception as e:
            logger.error(f"Error updating medical report title: {e}")
            raise e

#==================================================
# Medical Report Export Function
#==================================================

    # Export functionality (only called from API endpoint)
    async def generate_export_file(self, state: dict, format: str, include_details: bool = True) -> bytes:
        """Generate PDF or Word export file (separate from main workflow)"""

        if format == 'pdf':
            return await self._generate_pdf_export(state, include_details)
        elif format == 'word':
            return await self._generate_word_export(state, include_details)
        else:
            raise ValueError(f"Unsupported format: {format}")

    async def _generate_pdf_export(self, state: dict, include_details: bool) -> bytes:
        """Generate PDF from the evidence state (ranking/matrix/canonical/judgements)."""
        try:
            buffer = BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=72, leftMargin=72,
                            topMargin=72, bottomMargin=18)
            styles = getSampleStyleSheet()
            story = []

            story.append(Paragraph("MediSage — Differential Summary", styles['Title']))
            story.append(Spacer(1, 12))
            story.append(Paragraph(f"Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}", styles['Normal']))
            story.append(Paragraph(f"Session ID: {state.get('session_id', 'Unknown')}", styles['Normal']))
            story.append(Spacer(1, 12))

            story.append(Paragraph("Reported Information", styles['Heading2']))
            story.append(Paragraph(state.get("patient_text", "(none)"), styles['Normal']))
            story.append(Spacer(1, 12))

            canonical = {c["key"] if isinstance(c, dict) else c.key:
                         (c["label"] if isinstance(c, dict) else c.label)
                         for c in state.get("canonical", [])}
            judgements = state.get("judgements", {})
            matrix = state.get("matrix", {})

            for group in state.get("ranking", []):
                tied = len(group) > 1
                for diagnosis in group:
                    heading_text = f"{diagnosis}  (tied)" if tied else diagnosis
                    story.append(Paragraph(heading_text, styles['Heading2']))

                    for status, heading in (
                        ("supported", "Supported by"),
                        ("contradicted", "Contradicted by"),
                        ("not_mentioned", "Not yet established"),
                    ):
                        rows = [
                            (canonical.get(k, k), importance, judgements.get(k, {}).get("evidence"))
                            for k, importance in matrix.get(diagnosis, {}).items()
                            if judgements.get(k, {}).get("status", "not_mentioned") == status
                        ]
                        if not rows:
                            continue
                        story.append(Paragraph(heading, styles['Heading3']))
                        for label, importance, evidence in rows:
                            story.append(Paragraph(f"[{importance}] {label}", styles['Normal']))
                            if evidence and include_details:
                                story.append(Paragraph(f'Patient said: "{evidence}"', styles['Normal']))
                    story.append(Spacer(1, 12))

            not_evaluated = state.get("not_evaluated", [])
            if not_evaluated:
                story.append(Paragraph("Considered but not assessed", styles['Heading2']))
                story.append(Paragraph(
                    "These candidates could not be evaluated against the available evidence and are not ranked:",
                    styles['Normal']))
                for name in not_evaluated:
                    story.append(Paragraph(f"- {name}", styles['Normal']))
                story.append(Spacer(1, 12))

            summary = state.get("summary") or {}
            if summary:
                story.append(Paragraph("Clinical Summary", styles['Heading2']))
                if summary.get("severity"):
                    story.append(Paragraph(f"Severity: {summary['severity'].title()}", styles['Normal']))
                if summary.get("specialist_recommendation"):
                    story.append(Paragraph(
                        f"Recommended specialist: {summary['specialist_recommendation'].replace('_', ' ').title()}",
                        styles['Normal']))
                if summary.get("user_explanation"):
                    story.append(Paragraph(summary["user_explanation"], styles['Normal']))
                    if summary.get("explanation_source"):
                        source_line = f"Source: {summary['explanation_source']}"
                        if summary.get("explanation_url"):
                            source_line += f" ({summary['explanation_url']})"
                        story.append(Paragraph(source_line, styles['Normal']))
                story.append(Spacer(1, 12))

            # Always include disclaimer
            story.append(Paragraph("Disclaimer", styles['Heading3']))
            story.append(Paragraph(
                "This is not a diagnosis. Share it with a healthcare professional.",
                styles['Normal']))

            doc.build(story)
            buffer.seek(0)
            return buffer.getvalue()

        except Exception as e:
            logger.error(f"PDF generation failed: {e}")
            # Fallback to text
            return self._generate_text_export(state, include_details).encode('utf-8')

    async def _generate_word_export(self, state: Dict[str, Any], include_details: bool) -> bytes:
        """Generate a Word document from the evidence state (ranking/matrix/canonical/judgements)."""
        try:
            doc = Document()

            title = doc.add_heading('MediSage — Differential Summary', 0)
            title.alignment = 1  # Center alignment

            doc.add_paragraph(f"Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}")
            doc.add_paragraph(f"Session ID: {state.get('session_id', 'Unknown')}")

            doc.add_heading('Reported Information', level=1)
            doc.add_paragraph(state.get("patient_text", "(none)"))

            canonical = {c["key"] if isinstance(c, dict) else c.key:
                         (c["label"] if isinstance(c, dict) else c.label)
                         for c in state.get("canonical", [])}
            judgements = state.get("judgements", {})
            matrix = state.get("matrix", {})

            for group in state.get("ranking", []):
                tied = len(group) > 1
                for diagnosis in group:
                    heading_text = f"{diagnosis}  (tied)" if tied else diagnosis
                    doc.add_heading(heading_text, level=1)

                    for status, heading in (
                        ("supported", "Supported by"),
                        ("contradicted", "Contradicted by"),
                        ("not_mentioned", "Not yet established"),
                    ):
                        rows = [
                            (canonical.get(k, k), importance, judgements.get(k, {}).get("evidence"))
                            for k, importance in matrix.get(diagnosis, {}).items()
                            if judgements.get(k, {}).get("status", "not_mentioned") == status
                        ]
                        if not rows:
                            continue
                        doc.add_heading(heading, level=2)
                        for label, importance, evidence in rows:
                            doc.add_paragraph(f"[{importance}] {label}", style='List Bullet')
                            if evidence and include_details:
                                doc.add_paragraph(f'Patient said: "{evidence}"')

            not_evaluated = state.get("not_evaluated", [])
            if not_evaluated:
                doc.add_heading('Considered but not assessed', level=1)
                doc.add_paragraph(
                    "These candidates could not be evaluated against the available evidence and are not ranked:")
                for name in not_evaluated:
                    doc.add_paragraph(name, style='List Bullet')

            summary = state.get("summary") or {}
            if summary:
                doc.add_heading('Clinical Summary', level=1)
                if summary.get("severity"):
                    doc.add_paragraph(f"Severity: {summary['severity'].title()}")
                if summary.get("specialist_recommendation"):
                    doc.add_paragraph(
                        f"Recommended specialist: {summary['specialist_recommendation'].replace('_', ' ').title()}")
                if summary.get("user_explanation"):
                    doc.add_paragraph(summary["user_explanation"])
                    if summary.get("explanation_source"):
                        source_line = f"Source: {summary['explanation_source']}"
                        if summary.get("explanation_url"):
                            source_line += f" ({summary['explanation_url']})"
                        doc.add_paragraph(source_line)

            # Always include disclaimer
            doc.add_heading('Disclaimer', level=2)
            doc.add_paragraph("This is not a diagnosis. Share it with a healthcare professional.")

            # Save to buffer
            buffer = BytesIO()
            doc.save(buffer)
            buffer.seek(0)
            return buffer.getvalue()

        except Exception as e:
            logger.error(f"Word generation failed: {e}")
            # Fallback to text
            return self._generate_text_export(state, include_details).encode('utf-8')

    def _generate_text_export(self, state: dict, include_details: bool = True) -> str:
        lines = ["MEDISAGE — DIFFERENTIAL SUMMARY", "=" * 60, ""]
        lines.append("REPORTED INFORMATION")
        lines.append(state.get("patient_text", "(none)"))
        lines.append("")

        canonical = {c["key"] if isinstance(c, dict) else c.key:
                     (c["label"] if isinstance(c, dict) else c.label)
                     for c in state.get("canonical", [])}
        judgements = state.get("judgements", {})
        matrix = state.get("matrix", {})

        for group in state.get("ranking", []):
            tied = len(group) > 1
            for diagnosis in group:
                lines.append(f"{diagnosis}{'  (tied)' if tied else ''}")
                lines.append("-" * 60)
                for status, heading in (
                    ("supported", "Supported by"),
                    ("contradicted", "Contradicted by"),
                    ("not_mentioned", "Not yet established"),
                ):
                    rows = [
                        (canonical.get(k, k), importance, judgements.get(k, {}).get("evidence"))
                        for k, importance in matrix.get(diagnosis, {}).items()
                        if judgements.get(k, {}).get("status", "not_mentioned") == status
                    ]
                    if not rows:
                        continue
                    lines.append(f"  {heading}:")
                    for label, importance, evidence in rows:
                        lines.append(f"    - [{importance}] {label}")
                        if evidence and include_details:
                            lines.append(f"        patient said: \"{evidence}\"")
                lines.append("")

        not_evaluated = state.get("not_evaluated", [])
        if not_evaluated:
            lines.append("CONSIDERED BUT NOT ASSESSED (not ranked)")
            lines.append("-" * 60)
            lines.append("These candidates could not be evaluated against the available evidence:")
            for name in not_evaluated:
                lines.append(f"  - {name}")
            lines.append("")

        lines.append("This is not a diagnosis. Share it with a healthcare professional.")
        return "\n".join(lines)
