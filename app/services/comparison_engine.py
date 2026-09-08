"""
Hybrid Fact Comparison Engine implementing the 7-step hierarchical reconciliation pipeline.
Strictly distinguishes Corroborations, Contradictions, Contextual differences, and Unknown relationships.
"""

import json
import uuid
from typing import Optional, List, Tuple
from pathlib import Path

from app.core.config import settings
from app.core.logging import logger
from app.models.fact import Fact
from app.models.evidence import Evidence
from app.models.comparison import FactComparison, RelationshipType
from app.services.evidence_service import EvidenceService


class ComparisonEngine:
    def __init__(self, numeric_tolerance: float = settings.numeric_tolerance):
        self.numeric_tolerance = numeric_tolerance

    def compare_fact_pair(self, fact_a: Fact, fact_b: Fact) -> FactComparison:
        """
        Execute 7-step comparison hierarchy:
        1. Deterministic checks
        2. Unit normalization check
        3. Period compatibility
        4. Scope compatibility
        5. Numeric tolerance check
        6. Semantic equality check
        7. LLM reasoning fallback for ambiguity
        """
        evidence_a = EvidenceService.get_evidence_for_fact(fact_a)
        evidence_b = EvidenceService.get_evidence_for_fact(fact_b)
        comp_id = f"cmp_{uuid.uuid4().hex[:12]}"

        # STEP 1: Deterministic check - Predicate compatibility
        same_predicate = (fact_a.predicate == fact_b.predicate)
        same_subject = (fact_a.subject.lower() == fact_b.subject.lower())

        if not same_subject and not same_predicate:
            return FactComparison(
                comparison_id=comp_id,
                fact_a_id=fact_a.fact_id,
                fact_b_id=fact_b.fact_id,
                relationship=RelationshipType.UNKNOWN,
                confidence=0.5,
                reason=f"The facts discuss different subjects ('{fact_a.subject}' vs '{fact_b.subject}') and metrics ('{fact_a.predicate}' vs '{fact_b.predicate}').",
                differences=["Different subjects", "Different predicates"],
                evidence_a=evidence_a,
                evidence_b=evidence_b,
                fact_a=fact_a,
                fact_b=fact_b
            )

        # STEP 2: Unit normalization check
        unit_a = fact_a.normalized_unit or fact_a.unit or ""
        unit_b = fact_b.normalized_unit or fact_b.unit or ""
        compatible_units = (unit_a.lower() == unit_b.lower()) or (not unit_a and not unit_b)

        # STEP 3: Period compatibility
        period_a = (fact_a.period or "").strip()
        period_b = (fact_b.period or "").strip()
        same_period = (period_a.lower() == period_b.lower()) and bool(period_a)

        # Check for quarter vs full-year context difference (e.g. Q4 FY24 vs FY24)
        is_quarter_vs_fy = (
            ("q" in period_a.lower() and "fy" in period_b.lower() and "q" not in period_b.lower()) or
            ("q" in period_b.lower() and "fy" in period_a.lower() and "q" not in period_a.lower())
        )

        # Check for different fiscal years (e.g. FY23 vs FY24)
        is_different_fy = (
            "fy" in period_a.lower() and "fy" in period_b.lower() and period_a.lower() != period_b.lower()
        )

        if is_quarter_vs_fy or is_different_fy:
            diff_msg = f"Fact A period is '{period_a}' while Fact B period is '{period_b}'"
            reason = (
                f"The reported figures differ because they cover different time windows: "
                f"Fact A refers to {period_a} while Fact B refers to {period_b}. "
                f"This represents a valid contextual distinction rather than a factual contradiction."
            )
            return FactComparison(
                comparison_id=comp_id,
                fact_a_id=fact_a.fact_id,
                fact_b_id=fact_b.fact_id,
                relationship=RelationshipType.CONTEXTUAL,
                confidence=0.95,
                reason=reason,
                differences=[diff_msg],
                evidence_a=evidence_a,
                evidence_b=evidence_b,
                fact_a=fact_a,
                fact_b=fact_b
            )

        # STEP 4: Scope compatibility (e.g. inception vs annual, pro forma vs standalone)
        scope_a = (fact_a.scope or "").strip().lower()
        scope_b = (fact_b.scope or "").strip().lower()
        is_inception_vs_period = (
            ("inception" in scope_a or "inception" in period_a.lower()) !=
            ("inception" in scope_b or "inception" in period_b.lower())
        )
        is_scope_mismatch = bool(scope_a and scope_b and scope_a != scope_b)

        if is_inception_vs_period or is_scope_mismatch:
            reason = (
                f"The values differ due to different operational or reporting scopes: "
                f"Fact A scope is '{fact_a.scope or period_a}', whereas Fact B scope is '{fact_b.scope or period_b}'. "
                f"For example, cumulative metrics since inception naturally exceed single-year operational volume."
            )
            return FactComparison(
                comparison_id=comp_id,
                fact_a_id=fact_a.fact_id,
                fact_b_id=fact_b.fact_id,
                relationship=RelationshipType.CONTEXTUAL,
                confidence=0.93,
                reason=reason,
                differences=["Scope difference: cumulative vs periodic reporting"],
                evidence_a=evidence_a,
                evidence_b=evidence_b,
                fact_a=fact_a,
                fact_b=fact_b
            )

        # STEP 5: Numeric tolerance check (for numerical facts with aligned periods & compatible units)
        if fact_a.is_numerical and fact_b.is_numerical and fact_a.normalized_value is not None and fact_b.normalized_value is not None:
            if not compatible_units:
                return FactComparison(
                    comparison_id=comp_id,
                    fact_a_id=fact_a.fact_id,
                    fact_b_id=fact_b.fact_id,
                    relationship=RelationshipType.UNKNOWN,
                    confidence=0.7,
                    reason=f"Cannot compare numerical values directly because units cannot be safely reconciled ('{unit_a}' vs '{unit_b}').",
                    differences=[f"Incompatible units: {unit_a} vs {unit_b}"],
                    evidence_a=evidence_a,
                    evidence_b=evidence_b,
                    fact_a=fact_a,
                    fact_b=fact_b
                )

            val_a = fact_a.normalized_value
            val_b = fact_b.normalized_value
            denom = max(abs(val_a), abs(val_b), 1.0)
            rel_diff = abs(val_a - val_b) / denom

            if rel_diff <= self.numeric_tolerance:
                # Corroborated!
                pct_str = f"{rel_diff * 100:.2f}%"
                if rel_diff == 0.0:
                    explanation = (
                        f"Both documents report identical values for {fact_a.subject}'s {fact_a.predicate} "
                        f"for {fact_a.period} ({val_a} {unit_a}). Perfectly corroborated."
                    )
                else:
                    explanation = (
                        f"Both documents report {fact_a.subject}'s {fact_a.predicate} for {fact_a.period}. "
                        f"Document '{fact_a.source_document_name}' reports {fact_a.original_value or fact_a.value} {fact_a.original_unit or fact_a.unit}, "
                        f"while '{fact_b.source_document_name}' reports {fact_b.original_value or fact_b.value} {fact_b.original_unit or fact_b.unit}. "
                        f"After unit normalization to {unit_a}, the values ({val_a} vs {val_b}) differ by only {pct_str}, "
                        f"which falls well within standard financial rounding tolerance."
                    )
                return FactComparison(
                    comparison_id=comp_id,
                    fact_a_id=fact_a.fact_id,
                    fact_b_id=fact_b.fact_id,
                    relationship=RelationshipType.CORROBORATED,
                    confidence=0.96,
                    reason=explanation,
                    differences=[],
                    evidence_a=evidence_a,
                    evidence_b=evidence_b,
                    fact_a=fact_a,
                    fact_b=fact_b
                )
            else:
                # Contradiction!
                pct_str = f"{rel_diff * 100:.1f}%"
                explanation = (
                    f"Both documents refer to the same metric ({fact_a.predicate}) and period ({fact_a.period or 'identical'}), "
                    f"but report materially conflicting numbers: {val_a} {unit_a} vs {val_b} {unit_b}. "
                    f"The discrepancy is {pct_str}, which significantly exceeds permissible rounding tolerance ({self.numeric_tolerance * 100}%)."
                )
                return FactComparison(
                    comparison_id=comp_id,
                    fact_a_id=fact_a.fact_id,
                    fact_b_id=fact_b.fact_id,
                    relationship=RelationshipType.CONTRADICTION,
                    confidence=0.94,
                    reason=explanation,
                    differences=[f"Material numerical discrepancy of {pct_str} between normalized values ({val_a} vs {val_b} {unit_a})"],
                    evidence_a=evidence_a,
                    evidence_b=evidence_b,
                    fact_a=fact_a,
                    fact_b=fact_b
                )

        # STEP 6: Qualitative / Semantic equality
        if not fact_a.is_numerical and not fact_b.is_numerical:
            if str(fact_a.value).strip().lower() == str(fact_b.value).strip().lower():
                return FactComparison(
                    comparison_id=comp_id,
                    fact_a_id=fact_a.fact_id,
                    fact_b_id=fact_b.fact_id,
                    relationship=RelationshipType.CORROBORATED,
                    confidence=0.90,
                    reason=f"Both documents qualitatively affirm: '{fact_a.value}'.",
                    differences=[],
                    evidence_a=evidence_a,
                    evidence_b=evidence_b,
                    fact_a=fact_a,
                    fact_b=fact_b
                )

        # STEP 7: Ambiguity remains -> LLM reasoning or UNKNOWN
        if settings.llm_provider in ("anthropic", "openai", "gemini"):
            try:
                return self._compare_with_llm(fact_a, fact_b, evidence_a, evidence_b, comp_id)
            except Exception as e:
                logger.warning(f"LLM comparison failed ({e}), defaulting to UNKNOWN")

        return FactComparison(
            comparison_id=comp_id,
            fact_a_id=fact_a.fact_id,
            fact_b_id=fact_b.fact_id,
            relationship=RelationshipType.UNKNOWN,
            confidence=0.6,
            reason=(
                f"The relationship between '{fact_a.predicate}' ({fact_a.value} {fact_a.unit}) "
                f"and '{fact_b.predicate}' ({fact_b.value} {fact_b.unit}) cannot be determined with certainty "
                f"due to differing categorical definitions, unspecified scopes, or incomplete evidence."
            ),
            differences=["Uncertain metric definition alignment", "Incomplete context"],
            evidence_a=evidence_a,
            evidence_b=evidence_b,
            fact_a=fact_a,
            fact_b=fact_b
        )

    def _compare_with_llm(
        self, 
        fact_a: Fact, 
        fact_b: Fact, 
        evidence_a: Evidence, 
        evidence_b: Evidence,
        comp_id: str
    ) -> FactComparison:
        """Query LLM for reasoning over nuanced or ambiguous fact pairs."""
        prompt_path = Path(__file__).resolve().parent.parent / "prompts" / "fact_comparison.txt"
        with open(prompt_path, "r", encoding="utf-8") as f:
            template = f.read()

        formatted_prompt = template.format(
            subject_a=fact_a.subject,
            predicate_a=fact_a.predicate,
            normalized_value_a=fact_a.normalized_value,
            normalized_unit_a=fact_a.normalized_unit,
            value_a=fact_a.value,
            unit_a=fact_a.unit,
            period_a=fact_a.period,
            scope_a=fact_a.scope,
            doc_a=fact_a.source_document_name,
            page_a=fact_a.page_number,
            evidence_a=fact_a.evidence_text,
            subject_b=fact_b.subject,
            predicate_b=fact_b.predicate,
            normalized_value_b=fact_b.normalized_value,
            normalized_unit_b=fact_b.normalized_unit,
            value_b=fact_b.value,
            unit_b=fact_b.unit,
            period_b=fact_b.period,
            scope_b=fact_b.scope,
            doc_b=fact_b.source_document_name,
            page_b=fact_b.page_number,
            evidence_b=fact_b.evidence_text,
        )

        raw_json_str = ""
        if settings.llm_provider == "anthropic" and settings.anthropic_api_key:
            import anthropic
            client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
            response = client.messages.create(
                model=settings.llm_model,
                max_tokens=1024,
                messages=[{"role": "user", "content": formatted_prompt}]
            )
            raw_json_str = response.content[0].text

        if not raw_json_str:
            raise ValueError("No response from LLM")

        import re
        m = re.search(r"\{.*\}", raw_json_str, re.DOTALL)
        if not m:
            raise ValueError("Malformed JSON from LLM")

        data = json.loads(m.group(0))
        rel_str = data.get("relationship", "UNKNOWN").upper()
        if rel_str not in [r.value for r in RelationshipType]:
            rel_str = "UNKNOWN"

        return FactComparison(
            comparison_id=comp_id,
            fact_a_id=fact_a.fact_id,
            fact_b_id=fact_b.fact_id,
            relationship=RelationshipType(rel_str),
            confidence=float(data.get("confidence", 0.85)),
            reason=data.get("reason", "Determined via LLM contextual comparison."),
            differences=data.get("differences", []),
            evidence_a=evidence_a,
            evidence_b=evidence_b,
            fact_a=fact_a,
            fact_b=fact_b
        )
