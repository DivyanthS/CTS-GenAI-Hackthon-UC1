from __future__ import annotations

import io
from datetime import datetime, timezone
from typing import Any
from sqlalchemy import func

from config.settings import REPORT_DIR
from models.database import get_db
from models.analysis_run import AnalysisRun
from models.provider import Provider
from models.claim import Claim
from models.risk_assessment import RiskAssessment
from models.risk_factor import RiskFactor


class ReportService:
    """
    Generates structured 13-section analytical reports (JSON and PDF).
    """

    def get_runs(self) -> list[dict[str, Any]]:
        """Return all analysis runs recorded in the database."""
        with get_db() as db:
            runs = db.query(AnalysisRun).order_by(AnalysisRun.id.desc()).all()
            return [
                {
                    "id": r.id,
                    "run_id": r.run_id,
                    "filename": r.filename,
                    "total_rows": r.total_rows,
                    "total_columns": r.total_columns,
                    "total_providers": r.total_providers,
                    "total_claims": r.total_claims,
                    "total_beneficiaries": r.total_beneficiaries,
                    "low_count": r.low_count,
                    "medium_count": r.medium_count,
                    "high_count": r.high_count,
                    "critical_count": r.critical_count,
                    "total_reimbursement": r.total_reimbursement,
                    "status": r.status,
                    "created_at": r.created_at.isoformat() if r.created_at else None,
                    "completed_at": r.completed_at.isoformat() if r.completed_at else None,
                }
                for r in runs
            ]

    def get_run(self, run_id: str) -> dict[str, Any]:
        """Return a single analysis run by run_id."""
        clean_id = str(run_id).strip()
        with get_db() as db:
            r = db.query(AnalysisRun).filter(AnalysisRun.run_id == clean_id).first()
            if not r:
                raise KeyError(f"Analysis run not found: {clean_id}")
            return {
                "id": r.id,
                "run_id": r.run_id,
                "filename": r.filename,
                "total_rows": r.total_rows,
                "total_columns": r.total_columns,
                "total_providers": r.total_providers,
                "total_claims": r.total_claims,
                "total_beneficiaries": r.total_beneficiaries,
                "low_count": r.low_count,
                "medium_count": r.medium_count,
                "high_count": r.high_count,
                "critical_count": r.critical_count,
                "total_reimbursement": r.total_reimbursement,
                "status": r.status,
                "created_at": r.created_at.isoformat() if r.created_at else None,
                "completed_at": r.completed_at.isoformat() if r.completed_at else None,
            }

    def generate_json_report(self, run_id: str) -> dict[str, Any]:
        """
        Generate complete 13-section structured report JSON.
        """
        clean_id = str(run_id).strip()
        with get_db() as db:
            run = db.query(AnalysisRun).filter(AnalysisRun.run_id == clean_id).first()
            if not run:
                # If run_id is 'latest', get newest run
                if clean_id.lower() in ["latest", "current"]:
                    run = db.query(AnalysisRun).order_by(AnalysisRun.id.desc()).first()
                if not run:
                    raise KeyError(f"Analysis run '{run_id}' not found.")

            target_run_id = run.run_id
            providers = db.query(Provider).filter(Provider.analysis_run_id == target_run_id).all()
            claims = db.query(Claim).filter(Claim.analysis_run_id == target_run_id).all()

            # Categorize providers
            crit_providers = [p for p in providers if p.risk_level == "Critical"]
            high_providers = [p for p in providers if p.risk_level == "High"]
            med_providers = [p for p in providers if p.risk_level == "Medium"]
            low_providers = [p for p in providers if p.risk_level == "Low"]

            total_providers = len(providers) or 1
            total_reimb = sum(p.total_reimbursement for p in providers)
            high_exposure = sum(p.total_reimbursement for p in crit_providers + high_providers)

            def serialize_prov(p: Provider) -> dict[str, Any]:
                return {
                    "provider_id": p.provider_id,
                    "provider_name": p.provider_name,
                    "risk_score": p.risk_score,
                    "risk_level": p.risk_level,
                    "risk_status": p.risk_status,
                    "total_claims": p.total_claims,
                    "unique_beneficiaries": p.unique_beneficiaries,
                    "total_reimbursement": p.total_reimbursement,
                    "average_reimbursement": p.average_reimbursement,
                    "claims_per_beneficiary": p.claims_per_beneficiary,
                    "inpatient_share": p.inpatient_share,
                }

            # Top risk factors across High/Critical
            assessments = (
                db.query(RiskAssessment)
                .filter(RiskAssessment.analysis_run_id == target_run_id)
                .all()
            )
            factor_counts: dict[str, int] = {}
            for a in assessments:
                if a.risk_level in ["High", "Critical"]:
                    for rf in a.risk_factors:
                        factor_counts[rf.factor_name] = factor_counts.get(rf.factor_name, 0) + 1

            top_factors = [
                {"factor": k, "frequency": v, "weight": round((v / max(1, len(assessments))) * 100.0, 1)}
                for k, v in sorted(factor_counts.items(), key=lambda x: x[1], reverse=True)[:5]
            ]

            # Investigation queue
            investigation_queue = []
            for p in sorted(crit_providers + high_providers, key=lambda x: x.risk_score, reverse=True):
                priority = "P1" if p.risk_level == "Critical" else "P2"
                investigation_queue.append({
                    "priority": priority,
                    "provider_id": p.provider_id,
                    "provider_name": p.provider_name,
                    "risk_score": p.risk_score,
                    "risk_level": p.risk_level,
                    "reason": f"Elevated reimbursement (${p.average_reimbursement:,.2f} avg) and high claim volume ({p.total_claims} claims).",
                    "recommended_action": "Comprehensive payment integrity audit and medical coding verification.",
                })

            report_data = {
                "run_id": target_run_id,
                "generated_at": datetime.now(timezone.utc).isoformat(),
                # Section 1: Executive Summary
                "executive_summary": {
                    "overview": f"Analysis run {target_run_id} evaluated {len(claims):,} claims across {len(providers):,} healthcare providers from dataset '{run.filename}'.",
                    "total_financial_exposure": round(total_reimb, 2),
                    "high_risk_exposure": round(high_exposure, 2),
                    "high_risk_exposure_percentage": round((high_exposure / max(1.0, total_reimb)) * 100.0, 1),
                    "critical_providers_count": len(crit_providers),
                    "high_risk_providers_count": len(high_providers),
                    "medium_risk_providers_count": len(med_providers),
                    "low_risk_providers_count": len(low_providers),
                },
                # Section 2: Dataset Overview
                "dataset_overview": {
                    "filename": run.filename,
                    "total_rows": run.total_rows,
                    "total_columns": run.total_columns,
                    "total_providers": run.total_providers,
                    "total_claims": run.total_claims,
                    "total_beneficiaries": run.total_beneficiaries,
                },
                # Section 3: Risk Distribution
                "risk_distribution": {
                    "critical": {"count": len(crit_providers), "percentage": round((len(crit_providers) / total_providers) * 100.0, 1)},
                    "high": {"count": len(high_providers), "percentage": round((len(high_providers) / total_providers) * 100.0, 1)},
                    "medium": {"count": len(med_providers), "percentage": round((len(med_providers) / total_providers) * 100.0, 1)},
                    "low": {"count": len(low_providers), "percentage": round((len(low_providers) / total_providers) * 100.0, 1)},
                },
                # Sections 4-7: Providers by Risk Level
                "critical_providers": [serialize_prov(p) for p in sorted(crit_providers, key=lambda x: x.risk_score, reverse=True)],
                "high_risk_providers": [serialize_prov(p) for p in sorted(high_providers, key=lambda x: x.risk_score, reverse=True)],
                "medium_risk_providers": [serialize_prov(p) for p in sorted(med_providers, key=lambda x: x.risk_score, reverse=True)[:50]],
                "low_risk_providers": [serialize_prov(p) for p in sorted(low_providers, key=lambda x: x.risk_score, reverse=True)[:50]],
                # Section 8: Key Risk Factors
                "key_risk_factors": top_factors,
                # Section 9: Provider Statistics
                "provider_statistics": {
                    "average_claims_per_provider": round(len(claims) / total_providers, 1),
                    "average_reimbursement_per_provider": round(total_reimb / total_providers, 2),
                    "average_patient_age": round(sum(p.average_patient_age for p in providers) / total_providers, 1) if providers else 0.0,
                },
                # Section 10: Claim Statistics
                "claim_statistics": {
                    "total_claims": len(claims),
                    "inpatient_claims": sum(1 for c in claims if str(c.claim_type).lower() == "inpatient"),
                    "outpatient_claims": sum(1 for c in claims if str(c.claim_type).lower() != "inpatient"),
                    "average_claim_reimbursement": round(total_reimb / max(1, len(claims)), 2),
                },
                # Section 11: Reimbursement Analysis
                "reimbursement_analysis": {
                    "total_reimbursement": round(total_reimb, 2),
                    "critical_reimbursement": round(sum(p.total_reimbursement for p in crit_providers), 2),
                    "high_reimbursement": round(sum(p.total_reimbursement for p in high_providers), 2),
                    "medium_reimbursement": round(sum(p.total_reimbursement for p in med_providers), 2),
                    "low_reimbursement": round(sum(p.total_reimbursement for p in low_providers), 2),
                },
                # Section 12: Investigation Priority
                "investigation_priority_queue": investigation_queue[:25],
                # Section 13: Methodology / Dummy Model Disclaimer
                "methodology_disclaimer": {
                    "model_type": "Dummy Statistical Risk Engine (Statistical Benchmark & Percentile Heuristic)",
                    "version": "1.0",
                    "disclaimer": (
                        "This report was generated using dataset-grounded statistical benchmarking and component anomaly weighting. "
                        "Risk scores represent statistical deviation from cohort norms and do not constitute formal or legal determinations of fraud."
                    ),
                },
                # Charts for frontend convenience
                "charts": {
                    "risk_distribution": [
                        {"name": "Critical", "value": len(crit_providers)},
                        {"name": "High", "value": len(high_providers)},
                        {"name": "Medium", "value": len(med_providers)},
                        {"name": "Low", "value": len(low_providers)},
                    ],
                    "reimbursement_by_risk": [
                        {"risk": "Critical", "amount": round(sum(p.total_reimbursement for p in crit_providers), 2)},
                        {"risk": "High", "amount": round(sum(p.total_reimbursement for p in high_providers), 2)},
                        {"risk": "Medium", "amount": round(sum(p.total_reimbursement for p in med_providers), 2)},
                        {"risk": "Low", "amount": round(sum(p.total_reimbursement for p in low_providers), 2)},
                    ],
                },
            }

            return report_data

    def generate_pdf_report(self, run_id: str) -> bytes:
        """
        Generate a downloadable multi-page PDF report using ReportLab.
        """
        json_data = self.generate_json_report(run_id)

        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.lib import colors
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak

            buffer = io.BytesIO()
            doc = SimpleDocTemplate(
                buffer,
                pagesize=letter,
                rightMargin=40,
                leftMargin=40,
                topMargin=40,
                bottomMargin=40,
            )

            styles = getSampleStyleSheet()
            title_style = ParagraphStyle(
                "DocTitle",
                parent=styles["Title"],
                fontSize=20,
                leading=24,
                textColor=colors.HexColor("#0f172a"),
            )
            h2_style = ParagraphStyle(
                "Heading2",
                parent=styles["Heading2"],
                fontSize=13,
                leading=16,
                textColor=colors.HexColor("#1e293b"),
                spaceBefore=12,
                spaceAfter=6,
            )
            body_style = ParagraphStyle(
                "BodyText",
                parent=styles["Normal"],
                fontSize=9,
                leading=13,
                textColor=colors.HexColor("#334155"),
            )
            disclaimer_style = ParagraphStyle(
                "Disclaimer",
                parent=styles["Normal"],
                fontSize=8,
                leading=11,
                textColor=colors.HexColor("#64748b"),
                fontName="Helvetica-Oblique",
            )

            story = []

            # Header / Title
            story.append(Paragraph("Healthcare Payment Integrity & Fraud Risk Report", title_style))
            story.append(Spacer(1, 6))
            story.append(Paragraph(f"<b>Analysis Run:</b> {json_data['run_id']} | <b>Generated:</b> {json_data['generated_at'][:19]}", body_style))
            story.append(Spacer(1, 12))

            # 1. Executive Summary Table
            story.append(Paragraph("1. Executive Summary & Exposure", h2_style))
            exec_data = [
                ["Metric", "Value", "Metric", "Value"],
                ["Total Claims", f"{json_data['dataset_overview']['total_claims']:,}", "Total Reimbursement", f"${json_data['executive_summary']['total_financial_exposure']:,.2f}"],
                ["Total Providers", f"{json_data['dataset_overview']['total_providers']:,}", "High-Risk Exposure", f"${json_data['executive_summary']['high_risk_exposure']:,.2f} ({json_data['executive_summary']['high_risk_exposure_percentage']}%)"],
                ["Critical Providers", f"{json_data['executive_summary']['critical_providers_count']}", "High Risk Providers", f"{json_data['executive_summary']['high_risk_providers_count']}"],
            ]
            exec_table = Table(exec_data, colWidths=[130, 130, 130, 130])
            exec_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ("PADDING", (0, 0), (-1, -1), 5),
            ]))
            story.append(exec_table)
            story.append(Spacer(1, 14))

            # 2. Risk Distribution Table
            story.append(Paragraph("2. Risk Distribution Breakdown", h2_style))
            dist_data = [
                ["Risk Level", "Provider Count", "Percentage of Total", "Reimbursement Exposure"],
                ["Critical", str(json_data['risk_distribution']['critical']['count']), f"{json_data['risk_distribution']['critical']['percentage']}%", f"${json_data['reimbursement_analysis']['critical_reimbursement']:,.2f}"],
                ["High", str(json_data['risk_distribution']['high']['count']), f"{json_data['risk_distribution']['high']['percentage']}%", f"${json_data['reimbursement_analysis']['high_reimbursement']:,.2f}"],
                ["Medium", str(json_data['risk_distribution']['medium']['count']), f"{json_data['risk_distribution']['medium']['percentage']}%", f"${json_data['reimbursement_analysis']['medium_reimbursement']:,.2f}"],
                ["Low", str(json_data['risk_distribution']['low']['count']), f"{json_data['risk_distribution']['low']['percentage']}%", f"${json_data['reimbursement_analysis']['low_reimbursement']:,.2f}"],
            ]
            dist_table = Table(dist_data, colWidths=[120, 120, 120, 160])
            dist_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ("PADDING", (0, 0), (-1, -1), 4),
            ]))
            story.append(dist_table)
            story.append(Spacer(1, 14))

            # 3. Top Critical & High-Risk Providers Table
            story.append(Paragraph("3. Top High-Priority Providers Requiring Review", h2_style))
            top_provs = (json_data['critical_providers'] + json_data['high_risk_providers'])[:10]
            if top_provs:
                prov_table_data = [["Provider ID", "Provider Name", "Risk Score", "Level", "Claims", "Total Reimbursement"]]
                for p in top_provs:
                    prov_table_data.append([
                        p['provider_id'],
                        p['provider_name'][:24],
                        f"{p['risk_score']:.1f}",
                        p['risk_level'],
                        str(p['total_claims']),
                        f"${p['total_reimbursement']:,.2f}",
                    ])
                prov_table = Table(prov_table_data, colWidths=[80, 150, 60, 60, 50, 120])
                prov_table.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                    ("PADDING", (0, 0), (-1, -1), 4),
                ]))
                story.append(prov_table)
            else:
                story.append(Paragraph("No Critical or High-Risk providers identified in this analysis run.", body_style))

            story.append(Spacer(1, 14))

            # 4. Methodology & Disclaimer
            story.append(Paragraph("4. Methodology & Operational Disclaimer", h2_style))
            story.append(Paragraph(json_data['methodology_disclaimer']['disclaimer'], disclaimer_style))

            doc.build(story)
            return buffer.getvalue()

        except Exception as exc:
            # Fallback simple text PDF if reportlab encounters an unexpected layout error
            fallback_buffer = io.BytesIO()
            fallback_buffer.write(f"Payment Integrity Report: {run_id}\n\n{str(json_data)}".encode("utf-8"))
            return fallback_buffer.getvalue()
