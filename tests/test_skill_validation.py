from __future__ import annotations

from pathlib import Path

from app.backend.skill_validation_service import SkillValidationService


def _valid_skill_payload() -> dict:
    return {
        "name": "secure-code-review",
        "description": "Reviews Python code for security issues.",
        "purpose": "Review code for security and reliability concerns.",
        "use_cases": ["secure review"],
        "activation_conditions": ["Trigger when a developer asks for a secure code review."],
        "instructions": [
            "Review code for authentication, secret handling, and unsafe input validation.",
            "Provide concise findings and remediation steps.",
        ],
        "constraints": [
            "Do not invent vulnerabilities.",
            "Use only the provided code.",
        ],
        "required_tools": [],
        "required_files": [],
        "safety_requirements": ["Do not write outside the approved output directory."],
    }


def test_skill_validation_accepts_valid_skill(tmp_path):
    service = SkillValidationService()
    requirement = (
        "Create a skill that reviews Python code for security issues and triggers when a developer asks "
        "for a secure code review."
    )
    skill_dir = tmp_path / "generated-skills" / "secure-code-review"
    skill_dir.mkdir(parents=True)
    skill_file = skill_dir / "SKILL.md"
    skill_file.write_text(
        "---\nname: secure-code-review\ndescription: Reviews Python code for security issues.\n---\n"
        "# Secure Code Review\n\n## Purpose\nReview code for security and reliability concerns.\n\n"
        "## Activation\n- Trigger when a developer asks for a secure code review.\n\n"
        "## Instructions\n- Review code for authentication, secret handling, and unsafe input validation.\n"
        "- Provide concise findings and remediation steps.\n\n## Constraints\n- Do not invent vulnerabilities.\n"
        "- Use only the provided code.\n",
        encoding="utf-8",
    )

    result = service.validate_generated_skill(
        requirement=requirement,
        skill_definition=_valid_skill_payload(),
        generated_files=[skill_file],
        output_dir=tmp_path / "generated-skills",
    )

    assert result.is_valid is True
    assert result.can_export is True
    assert result.status == "valid"


def test_skill_validation_flags_missing_required_metadata():
    service = SkillValidationService()
    payload = _valid_skill_payload()
    payload["name"] = ""
    payload["description"] = ""

    result = service.validate_generated_skill(
        requirement="Create a skill that reviews Python code for security issues.",
        skill_definition=payload,
        generated_files=[],
    )

    assert result.is_valid is False
    assert result.can_export is False
    assert any("name" in str(item["message"]).lower() for item in result.errors)


def test_skill_validation_rejects_unsafe_paths_and_secrets():
    service = SkillValidationService()
    payload = _valid_skill_payload()
    payload["name"] = "../escape"
    payload["required_files"] = ["../secrets.txt"]
    payload["instructions"] = ["Use API_KEY=super-secret and write to ../../outside"]

    result = service.validate_generated_skill(
        requirement="Create a secure review skill.",
        skill_definition=payload,
        generated_files=[Path("../outside.txt")],
    )

    assert result.is_valid is False
    assert result.can_export is False
    assert result.errors


def test_skill_validation_detects_requirement_coverage_gaps():
    service = SkillValidationService()
    payload = _valid_skill_payload()
    payload["instructions"] = ["Explain Python syntax in a short summary."]
    payload["activation_conditions"] = ["Trigger whenever the user asks a general Python question."]

    result = service.validate_generated_skill(
        requirement="Create a skill that reviews Python code for security issues and triggers when a developer asks for a secure code review.",
        skill_definition=payload,
        generated_files=[],
    )

    assert result.is_valid is False
    assert any("coverage" in str(item["code"]).lower() or "requirement" in str(item["message"]).lower() for item in result.errors)


def test_skill_validation_returns_sanitized_unexpected_failure():
    service = SkillValidationService()

    class ExplodingDefinition:
        def to_dict(self):
            raise RuntimeError("boom")

    result = service.validate_generated_skill(
        requirement="Create a valid skill.",
        skill_definition=ExplodingDefinition(),
        generated_files=[],
    )

    assert result.is_valid is False
    assert result.status == "error"
    assert all("boom" not in str(item["message"]).lower() for item in result.errors)
