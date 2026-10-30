import json
import os
from typing import Any, Dict, Optional, Tuple


class MedicalNormalizer:
    _dictionary_cache: Optional[Dict[str, Any]] = None

    @classmethod
    def get_dictionary(cls) -> Dict[str, Any]:
        """Loads and caches the medical test dictionary."""
        if cls._dictionary_cache is None:
            dict_path = os.path.join(
                os.path.dirname(__file__), "..", "extraction", "medical_test_dictionary.json"
            )
            with open(dict_path, "r", encoding="utf-8") as f:
                cls._dictionary_cache = json.load(f)["tests"]
        return cls._dictionary_cache

    @classmethod
    def match_test_name(cls, raw_name: str) -> Optional[Tuple[str, Dict[str, Any]]]:
        """Matches a raw test name against aliases in the test dictionary."""
        cleaned = raw_name.strip().lower()
        tests = cls.get_dictionary()

        for key, defs in tests.items():
            if cleaned == key or cleaned == defs["display_name"].lower():
                return key, defs
            for alias in defs.get("aliases", []):
                if alias.lower() in cleaned or cleaned in alias.lower():
                    return key, defs

        return None

    @classmethod
    def normalize_unit_and_value(
        cls,
        test_key: str,
        value: float,
        unit: Optional[str],
    ) -> Tuple[float, str, bool]:
        """
        Converts compatible clinical units to standard SI / customary units.
        Returns:
            - normalized_value: float
            - normalized_unit: str
            - is_compatible: bool
        """
        tests = cls.get_dictionary()
        if test_key not in tests:
            return value, unit or "", True

        defs = tests[test_key]
        default_unit = defs["default_unit"]

        if not unit:
            return value, default_unit, True

        clean_unit = unit.strip().lower()

        # 1. Glucose conversions (mmol/L -> mg/dL: multiply by 18.0182)
        if test_key in ["fasting_glucose_mg_dl", "cholesterol_total_mg_dl", "cholesterol_hdl_mg_dl", "cholesterol_ldl_mg_dl"]:
            if "mmol" in clean_unit:
                return round(value * 18.0182, 1), default_unit, True

        # 2. Triglycerides (mmol/L -> mg/dL: multiply by 88.57)
        if test_key == "triglycerides_mg_dl":
            if "mmol" in clean_unit:
                return round(value * 88.57, 1), default_unit, True

        # 3. Serum Creatinine (µmol/L or umol/L -> mg/dL: divide by 88.4)
        if test_key == "serum_creatinine_mg_dl":
            if "umol" in clean_unit or "µmol" in clean_unit:
                return round(value / 88.4, 2), default_unit, True

        # 4. Hemoglobin (g/L -> g/dL: divide by 10)
        if test_key == "hemoglobin_g_dl":
            if clean_unit in ["g/l", "grams/liter"]:
                return round(value / 10.0, 1), default_unit, True

        return value, default_unit, True

    @classmethod
    def validate_biological_plausibility(
        cls, test_key: str, value: float
    ) -> Tuple[bool, Optional[str]]:
        """Validates that a numeric lab value is physically and biologically plausible."""
        tests = cls.get_dictionary()
        if test_key not in tests:
            return True, None

        defs = tests[test_key]
        min_p = defs.get("min_plausible", 0.0)
        max_p = defs.get("max_plausible", 10000.0)

        if value < min_p:
            return False, f"Value {value} is below plausible biological threshold of {min_p} {defs['default_unit']}."
        if value > max_p:
            return False, f"Value {value} exceeds plausible biological threshold of {max_p} {defs['default_unit']}."

        return True, None
