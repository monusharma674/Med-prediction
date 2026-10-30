import re
from typing import Any, Dict, List
from app.services.validation.normalizer import MedicalNormalizer


class MedicalValueParser:
    # Regex to capture numeric test values
    NUMBER_PATTERN = re.compile(r"(\d+(?:\.\d+)?)")

    # Common units regex
    UNIT_PATTERN = re.compile(
        r"(mg/d[lL]|mmol/[lL]|%|g/d[lL]|g/[lL]|µmol/[lL]|umol/[lL]|mmHg|mm\s*Hg|uIU/m[lL]|mIU/[lL])",
        re.IGNORECASE,
    )

    # Reference range regex, e.g. "70-99", "70 - 100", "< 200", "> 50", "0.7 - 1.3"
    RANGE_PATTERN = re.compile(
        r"(?:(?:<|>|<=|>=)\s*\d+(?:\.\d+)?|\d+(?:\.\d+)?\s*(?:-|–|to)\s*\d+(?:\.\d+)?)",
        re.IGNORECASE,
    )

    @classmethod
    def parse_report_text(
        cls, raw_text: str, default_confidence: float = 0.95
    ) -> List[Dict[str, Any]]:
        """
        Parses raw text extracted from a clinical lab report.
        Extracts test names, numeric values, units, reference intervals, and normalized values.
        """
        results: List[Dict[str, Any]] = []
        seen_tests = set()

        lines = raw_text.splitlines()
        for line in lines:
            line_str = line.strip()
            if not line_str or len(line_str) < 3:
                continue

            # Check if this line contains any known test alias
            match = MedicalNormalizer.match_test_name(line_str)
            if not match:
                continue

            test_key, test_def = match
            if test_key in seen_tests:
                continue

            # Find the position where the test name / alias appears in the line
            # to only parse numbers AFTER the test name (avoids '1' in HbA1c, '12' in B12, etc.)
            remaining_text = line_str
            for candidate in [test_def["display_name"]] + test_def.get("aliases", []):
                idx = line_str.lower().find(candidate.lower())
                if idx != -1:
                    remaining_text = line_str[idx + len(candidate):]
                    break

            # Find numbers in the text strictly following the test name
            numbers = cls.NUMBER_PATTERN.findall(remaining_text)
            if not numbers:
                continue

            # Extract reference range if present
            ref_range_match = cls.RANGE_PATTERN.search(remaining_text)
            ref_range = ref_range_match.group(0) if ref_range_match else test_def.get("reference_range", "")

            # Value selection heuristic: first number after the test name is the patient's result
            raw_value = float(numbers[0])

            # Extract unit from remaining text or fallback to default
            unit_match = cls.UNIT_PATTERN.search(remaining_text)
            raw_unit = unit_match.group(0) if unit_match else test_def.get("default_unit", "")

            # Normalize unit and value
            norm_val, norm_unit, _ = MedicalNormalizer.normalize_unit_and_value(
                test_key, raw_value, raw_unit
            )

            # Plausibility check
            is_plausible, _ = MedicalNormalizer.validate_biological_plausibility(
                test_key, norm_val
            )

            seen_tests.add(test_key)
            results.append({
                "test_name_raw": test_def["display_name"],
                "test_name_standardized": test_key,
                "value_original": raw_value,
                "value_corrected": None,
                "unit_original": raw_unit,
                "unit_normalized": norm_unit,
                "reference_range": ref_range,
                "ocr_confidence": default_confidence if is_plausible else 0.50,
                "data_source": "ocr",
                "is_manually_corrected": False,
            })

        return results
