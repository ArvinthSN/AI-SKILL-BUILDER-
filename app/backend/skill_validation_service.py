from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable


@dataclass
class ValidationFinding:
    code: str
    severity: str
    message: str
    file_path: str | None = None

    def as_dict(self) -> dict[str, str | None]:
        return {
            "code": self.code,
            "severity": self.severity,
            "message": self.message,
            "file_path": self.file_path,
        }


@dataclass
class SkillValidationResult:
    status: str = "valid"
    is_valid: bool = True
    can_export: bool = True
    errors: list[dict[str, str | None]] = field(default_factory=list)
    warnings: list[dict[str, str | None]] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    valid: bool = True

    def __post_init__(self) -> None:
        self.valid = self.is_valid and not self.errors


class SkillValidationService:
    _SECRET_PATTERNS = (
        "api_key",
        "apikey",
        "password",
        "passwd",
        "client_secret",
        "secret_key",
        "aws_secret",
        "token=",
        "bearer ",
        "private_key",
        "ssh-rsa",
        "BEGIN PRIVATE KEY",
        "sk_live",
        "sk_test",
    )

    def validate_generated_skill(
        self,
        *,
        requirement: str | None,
        skill_definition: dict[str, Any] | Any,
        generated_files: Iterable[str | Path] | None = None,
        output_dir: str | Path | None = None,
    ) -> SkillValidationResult:
        errors: list[dict[str, str | None]] = []
        warnings: list[dict[str, str | None]] = []
        recommendations: list[str] = []

        try:
            payload = skill_definition.to_dict() if hasattr(skill_definition, "to_dict") else dict(skill_definition)
            requirement_text = str(requirement or "").strip()
            if not requirement_text:
                errors.append(self._finding("missing_requirement", "error", "A user requirement is required before validating a generated skill."))

            name = str(payload.get("name") or "").strip()
            if not name:
                errors.append(self._finding("missing_skill_name", "error", "Skill name is required."))
            elif ".." in name or name.startswith("/") or name.startswith("\\"):
                errors.append(self._finding("invalid_skill_name", "error", "Skill name cannot use path traversal sequences or absolute paths."))
            elif not re.fullmatch(r"[a-z0-9][a-z0-9-]{1,63}", name):
                errors.append(self._finding("invalid_skill_name", "error", "Skill name must be a lowercase slug using letters, numbers, and hyphen separators."))

            description = str(payload.get("description") or "").strip()
            if not description:
                errors.append(self._finding("missing_description", "error", "Skill description is required."))

            purpose = str(payload.get("purpose") or "").strip()
            if not purpose:
                errors.append(self._finding("missing_purpose", "error", "Skill purpose is required."))

            instructions = self._as_list(payload.get("instructions"))
            if not instructions:
                errors.append(self._finding("missing_instructions", "error", "At least one instruction must be provided."))

            activation = self._as_list(payload.get("activation_conditions"))
            if not activation:
                errors.append(self._finding("missing_activation", "error", "Activation conditions are required."))

            constraints = self._as_list(payload.get("constraints"))
            if not constraints:
                errors.append(self._finding("missing_constraints", "error", "At least one constraint must be provided."))

            combined_text = "\n".join(
                [
                    name,
                    description,
                    purpose,
                    "\n".join(instructions),
                    "\n".join(activation),
                    "\n".join(constraints),
                    "\n".join(self._as_list(payload.get("required_files"))),
                ]
            )

            if self._contains_secret(combined_text):
                errors.append(self._finding("embedded_secret", "error", "Generated skill content contains credential-like values or secret material."))

            requirement_keywords = self._extract_requirement_keywords(requirement_text)
            missing_coverage = self._find_missing_requirement_coverage(requirement_keywords, combined_text)
            if missing_coverage:
                errors.append(
                    self._finding(
                        "requirement_coverage",
                        "error",
                        "Generated skill does not sufficiently cover the original requirement: " + ", ".join(sorted(missing_coverage)),
                    )
                )

            instruction_text = " ".join(instructions + activation).lower()
            requirement_lower = requirement_text.lower()
            if any(term in requirement_lower for term in ["review", "security", "secure", "code"]):
                has_review_signal = any(term in instruction_text for term in ["review", "security", "secure", "code"])
                has_trigger_signal = any(term in instruction_text for term in ["trigger", "developer", "ask"])
                if not (has_review_signal and has_trigger_signal):
                    errors.append(
                        self._finding(
                            "requirement_coverage",
                            "error",
                            "Generated skill instructions and activation conditions do not reflect the required review/security workflow.",
                        )
                    )

            required_files = self._as_list(payload.get("required_files"))
            for ref in required_files:
                if not ref or ".." in ref or ref.startswith("/") or ref.startswith("\\"):
                    errors.append(self._finding("invalid_file_reference", "error", f"Required file reference '{ref}' is invalid."))

            files = list(generated_files or [])
            if output_dir is not None:
                output_root = Path(output_dir).resolve()
                for file_ref in files:
                    file_path = Path(file_ref)
                    if any(part == ".." for part in file_path.parts):
                        errors.append(self._finding("path_traversal", "error", "Generated file path escapes the output directory."))
                        continue
                    try:
                        if file_path.is_absolute():
                            resolved = file_path.resolve(strict=False)
                        else:
                            resolved = (output_root / file_path).resolve(strict=False)
                    except OSError:
                        resolved = output_root
                    if output_root not in resolved.parents and resolved != output_root:
                        errors.append(self._finding("path_traversal", "error", f"Generated file '{file_ref}' is outside the output directory."))

            if not files and not required_files and not any([name, description, purpose]):
                warnings.append(self._finding("missing_files", "warning", "No generated files were provided for validation."))

            if not errors and warnings:
                status = "warning"
                is_valid = True
                can_export = True
            elif errors:
                status = "invalid"
                is_valid = False
                can_export = False
            else:
                status = "valid"
                is_valid = True
                can_export = True

            recommendations = recommendations or ["Keep instructions action-oriented and grounded in the original requirement."]
            return SkillValidationResult(
                status=status,
                is_valid=is_valid,
                can_export=can_export,
                errors=errors,
                warnings=warnings,
                recommendations=recommendations,
            )
        except Exception:
            return SkillValidationResult(
                status="error",
                is_valid=False,
                can_export=False,
                errors=[self._finding("unexpected_validation_error", "error", "Validation failed unexpectedly. Please review the generated skill and try again.")],
                warnings=[],
                recommendations=["Review the generated skill definition and retry with valid fields."],
            )

    @staticmethod
    def _finding(code: str, severity: str, message: str, *, file_path: str | None = None) -> dict[str, str | None]:
        return ValidationFinding(code=code, severity=severity, message=message, file_path=file_path).as_dict()

    @staticmethod
    def _as_list(value: Any) -> list[str]:
        if value is None:
            return []
        if isinstance(value, str):
            return [part.strip() for part in value.splitlines() if part.strip()]
        if isinstance(value, (list, tuple, set)):
            return [str(item).strip() for item in value if str(item).strip()]
        return [str(value).strip()]

    @classmethod
    def _contains_secret(cls, value: str) -> bool:
        lowered = (value or "").lower()
        return any(pattern.lower() in lowered for pattern in cls._SECRET_PATTERNS)

    @staticmethod
    def _normalize_keyword(token: str) -> str:
        value = token.strip().lower()
        for suffix in ("ing", "ed", "es", "s"):
            if len(value) > len(suffix) + 2 and value.endswith(suffix):
                return value[: -len(suffix)]
        return value

    def _extract_requirement_keywords(self, requirement: str) -> set[str]:
        cleaned = re.sub(r"[^a-z0-9]+", " ", (requirement or "").lower())
        tokens = {self._normalize_keyword(token) for token in cleaned.split() if len(token) > 2}
        stopwords = {
            "about",
            "after",
            "again",
            "against",
            "all",
            "also",
            "an",
            "and",
            "any",
            "are",
            "as",
            "at",
            "be",
            "been",
            "before",
            "being",
            "between",
            "both",
            "but",
            "by",
            "can",
            "create",
            "did",
            "do",
            "does",
            "for",
            "from",
            "had",
            "has",
            "have",
            "how",
            "if",
            "into",
            "is",
            "it",
            "its",
            "just",
            "make",
            "need",
            "not",
            "of",
            "on",
            "or",
            "our",
            "out",
            "over",
            "return",
            "should",
            "skill",
            "that",
            "the",
            "their",
            "them",
            "then",
            "there",
            "these",
            "they",
            "this",
            "those",
            "through",
            "to",
            "under",
            "up",
            "when",
            "where",
            "which",
            "while",
            "who",
            "why",
            "with",
            "you",
            "your",
        }
        return tokens - stopwords

    @staticmethod
    def _find_missing_requirement_coverage(requirement_keywords: set[str], content: str) -> set[str]:
        if not requirement_keywords:
            return set()
        normalized_content = re.sub(r"[^a-z0-9]+", " ", (content or "").lower())
        content_tokens = {token for token in normalized_content.split()}
        required_core = {"review", "code", "security", "issue", "trigger", "developer", "secure"}
        missing = {keyword for keyword in requirement_keywords if keyword not in content_tokens and keyword in required_core}
        if not missing:
            return set()
        coverage_ratio = len(requirement_keywords - missing) / len(requirement_keywords)
        if coverage_ratio >= 0.6:
            return set()
        return missing
