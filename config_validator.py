"""Configuration validation CLI for Tongyi Agent."""
from __future__ import annotations

import argparse
import configparser
import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse

import requests


@dataclass
class CheckResult:
    name: str
    status: str
    details: str
    suggestion: Optional[str] = None


@dataclass
class ValidationReport:
    root: str
    checks: List[CheckResult] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return all(ch.status == "PASS" for ch in self.checks if ch.status != "INFO")

    def as_dict(self) -> Dict[str, object]:
        return {
            "root": self.root,
            "passed": self.passed,
            "checks": [
                {
                    "name": ch.name,
                    "status": ch.status,
                    "details": ch.details,
                    "suggestion": ch.suggestion,
                }
                for ch in self.checks
            ],
        }


def validate_models_ini(root: Path) -> Tuple[List[CheckResult], Optional[Dict[str, str]]]:
    checks: List[CheckResult] = []
    config_path = root / "models.ini"
    if not config_path.exists():
        checks.append(
            CheckResult(
                "models.ini",
                "FAIL",
                f"Missing file at {config_path}",
                "Copy models.ini from the repository root or re-run installation steps.",
            )
        )
        return checks, None

    parser = configparser.ConfigParser()
    parser.read(config_path)

    if not parser.has_section("models"):
        checks.append(
            CheckResult(
                "models.ini",
                "FAIL",
                "Missing [models] section",
                "Add a [models] section with primary/fallback entries.",
            )
        )
        return checks, None

    primary = parser.get("models", "primary", fallback="").strip().strip('"')
    fallback = parser.get("models", "fallback", fallback="").strip().strip('"')
    interval_raw = parser.get("models", "fallback_interval", fallback="3")
    base_url = parser.get("openrouter", "base_url", fallback="https://openrouter.ai/api/v1").strip().strip('"')

    if primary:
        checks.append(CheckResult("primary model", "PASS", f"Primary model set to {primary}"))
    else:
        checks.append(
            CheckResult(
                "primary model",
                "FAIL",
                "Primary model is not configured",
                "Set models.primary in models.ini (e.g., alibaba/tongyi-deepresearch-30b-a3b).",
            )
        )

    if fallback:
        checks.append(CheckResult("fallback model", "PASS", f"Fallback model set to {fallback}"))
    else:
        checks.append(
            CheckResult(
                "fallback model",
                "WARN",
                "Fallback model not configured",
                "Set models.fallback to a cheaper/free model for resilience.",
            )
        )

    try:
        interval = int(interval_raw)
        if interval <= 0:
            raise ValueError
        checks.append(CheckResult("fallback interval", "PASS", f"Fallback interval set to {interval}"))
    except ValueError:
        checks.append(
            CheckResult(
                "fallback interval",
                "WARN",
                f"Invalid fallback interval '{interval_raw}'",
                "Set models.fallback_interval to a positive integer (e.g., 3).",
            )
        )

    parsed = urlparse(base_url)
    if parsed.scheme and parsed.netloc:
        checks.append(CheckResult("OpenRouter base URL", "PASS", f"Using {base_url}"))
    else:
        checks.append(
            CheckResult(
                "OpenRouter base URL",
                "FAIL",
                f"Invalid base URL '{base_url}'",
                "Set [openrouter].base_url to a valid https endpoint.",
            )
        )

    return checks, {
        "primary": primary,
        "fallback": fallback,
        "base_url": base_url,
    }


def validate_training_config(root: Path) -> Tuple[List[CheckResult], Optional[Dict[str, str]]]:
    checks: List[CheckResult] = []
    config_path = root / "training_config.ini"
    if not config_path.exists():
        checks.append(
            CheckResult(
                "training_config.ini",
                "WARN",
                f"Missing file at {config_path}",
                "Copy training_config.ini from the repository root if you plan to use Agent Lightning.",
            )
        )
        return checks, None

    parser = configparser.ConfigParser()
    parser.read(config_path)

    if not parser.has_section("training"):
        checks.append(
            CheckResult(
                "training_config.ini",
                "WARN",
                "Missing [training] section",
                "Add a [training] section or regenerate training_config.ini.",
            )
        )
        return checks, None

    mode = parser.get("training", "mode", fallback="prompt").strip().strip('"')
    training_path = parser.get("training", "training_data_path", fallback=".tongyi_training").strip().strip('"')
    auto_save_raw = parser.get("training", "auto_save_interval", fallback="10")

    if mode in {"prompt", "rl", "sft"}:
        checks.append(CheckResult("training mode", "PASS", f"Mode set to {mode}"))
    else:
        checks.append(
            CheckResult(
                "training mode",
                "WARN",
                f"Unsupported mode '{mode}'",
                "Set training.mode to prompt, rl, or sft.",
            )
        )

    try:
        auto_save = int(auto_save_raw)
        if auto_save <= 0:
            raise ValueError
        checks.append(CheckResult("auto save interval", "PASS", f"Auto-save every {auto_save} interactions"))
    except ValueError:
        checks.append(
            CheckResult(
                "auto save interval",
                "WARN",
                f"Invalid auto_save_interval '{auto_save_raw}'",
                "Set training.auto_save_interval to a positive integer.",
            )
        )

    training_dir = (root / training_path).resolve()
    parent_dir = training_dir.parent
    if parent_dir.exists():
        checks.append(CheckResult("training data path", "PASS", f"Training data will be stored in {training_dir}"))
    else:
        checks.append(
            CheckResult(
                "training data path",
                "WARN",
                f"Parent directory {parent_dir} does not exist",
                "Create the directory or update training.training_data_path.",
            )
        )

    return checks, {"training_data_path": training_path}


def validate_api_key() -> CheckResult:
    key = os.getenv("OPENROUTER_API_KEY", "").strip()
    if not key:
        return CheckResult(
            "OPENROUTER_API_KEY",
            "FAIL",
            "Environment variable not set",
            "Add OPENROUTER_API_KEY to your .env file or export it before running the agent.",
        )
    masked = key[:4] + "..." + key[-4:] if len(key) > 8 else "***"
    return CheckResult("OPENROUTER_API_KEY", "PASS", f"Detected key {masked}")


def test_openrouter_connection(base_url: str, api_key: str, timeout: int = 15) -> Tuple[List[CheckResult], Optional[List[str]]]:
    checks: List[CheckResult] = []
    url = f"{base_url.rstrip('/')}/models"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    try:
        resp = requests.get(url, headers=headers, timeout=timeout)
    except requests.RequestException as exc:
        checks.append(
            CheckResult(
                "OpenRouter connectivity",
                "FAIL",
                f"Network error: {exc}",
                "Check your internet connection and proxy settings.",
            )
        )
        return checks, None

    if resp.status_code == 200:
        payload = resp.json()
        raw_models = payload.get("data") or payload.get("models") or []
        names: List[str] = []
        for entry in raw_models:
            if isinstance(entry, dict):
                candidate = entry.get("id") or entry.get("name") or entry.get("slug")
                if candidate:
                    names.append(candidate)
            elif isinstance(entry, str):
                names.append(entry)
        checks.append(
            CheckResult(
                "OpenRouter connectivity",
                "PASS",
                f"Retrieved {len(names)} models from OpenRouter",
            )
        )
        return checks, names

    if resp.status_code == 401:
        checks.append(
            CheckResult(
                "OpenRouter connectivity",
                "FAIL",
                "Authentication failed (401)",
                "Verify OPENROUTER_API_KEY and ensure it has access to the requested models.",
            )
        )
    else:
        checks.append(
            CheckResult(
                "OpenRouter connectivity",
                "FAIL",
                f"OpenRouter returned {resp.status_code}: {resp.text[:200]}",
                "Confirm the base_url in models.ini and retry later.",
            )
        )
    return checks, None


def check_model_availability(models_config: Dict[str, str], available_models: List[str]) -> List[CheckResult]:
    results: List[CheckResult] = []
    model_catalog = set(available_models)
    for label in ("primary", "fallback"):
        model_name = models_config.get(label)
        if not model_name:
            continue
        if model_name in model_catalog:
            results.append(CheckResult(f"{label} model availability", "PASS", f"{model_name} is available"))
        else:
            results.append(
                CheckResult(
                    f"{label} model availability",
                    "WARN",
                    f"{model_name} not reported by OpenRouter",
                    "Run 'tongyi-cli models list' or update models.ini with a supported model.",
                )
            )
    return results


def run_validation(root: Path, check_openrouter: bool = False) -> ValidationReport:
    report = ValidationReport(root=str(root.resolve()))

    models_checks, models_config = validate_models_ini(root)
    report.checks.extend(models_checks)

    training_checks, _ = validate_training_config(root)
    report.checks.extend(training_checks)

    api_key_check = validate_api_key()
    report.checks.append(api_key_check)

    available_models: Optional[List[str]] = None
    base_url = (models_config or {}).get("base_url", "https://openrouter.ai/api/v1")

    if check_openrouter and api_key_check.status == "PASS":
        connection_checks, available_models = test_openrouter_connection(base_url, os.getenv("OPENROUTER_API_KEY", ""))
        report.checks.extend(connection_checks)

    if models_config and available_models:
        report.checks.extend(check_model_availability(models_config, available_models))
    elif models_config and check_openrouter and api_key_check.status == "PASS":
        report.checks.append(
            CheckResult(
                "model availability",
                "WARN",
                "Skipped availability check because the OpenRouter catalog could not be fetched",
                "Retry with --check-openrouter or verify connectivity manually.",
            )
        )

    return report


def print_report(report: ValidationReport) -> None:
    print(f"Configuration validation for {report.root}\n")
    icon_map = {"PASS": "[PASS]", "WARN": "[WARN]", "FAIL": "[FAIL]", "INFO": "[INFO]"}
    suggestions: List[str] = []
    for check in report.checks:
        icon = icon_map.get(check.status, "•")
        print(f"{icon} {check.name}: {check.details}")
        if check.suggestion:
            print(f"    Suggestion: {check.suggestion}")
            if check.status != "PASS":
                suggestions.append(check.suggestion)
    if report.passed:
        print("\nAll critical checks passed.")
    else:
        print("\nSome checks need attention.")
        if suggestions:
            print("Top troubleshooting tips:")
            unique_suggestions = []
            for tip in suggestions:
                if tip not in unique_suggestions:
                    unique_suggestions.append(tip)
            for tip in unique_suggestions[:5]:
                print(f"  - {tip}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate Tongyi Agent configuration")
    parser.add_argument("--root", default=Path(__file__).resolve().parent, help="Project root (default: repository root)")
    parser.add_argument("--check-openrouter", action="store_true", help="Test OpenRouter connectivity and model availability")
    parser.add_argument("--json", action="store_true", help="Output JSON instead of human-readable text")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    report = run_validation(root, check_openrouter=args.check_openrouter)

    if args.json:
        print(json.dumps(report.as_dict(), indent=2))
    else:
        print_report(report)

    if not report.passed:
        has_fail = any(check.status == "FAIL" for check in report.checks)
        raise SystemExit(1 if has_fail else 0)


if __name__ == "__main__":
    main()
