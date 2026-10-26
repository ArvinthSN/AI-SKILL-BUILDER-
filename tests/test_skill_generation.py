from __future__ import annotations

import pytest

from app.backend.skill_generation_service import (
    SkillGenerationService,
    SkillGenerationValidator,
    SkillRequirement,
)


class FakeLLMResponse:
    def __init__(self, text: str):
        self.text = text


def test_requirement_analysis_extracts_skill_fields():
    service = SkillGenerationService()

    skill = service.analyze_requirement(
        "Create a skill that helps review Python code for security issues and trigger it when a developer asks for a secure code review."
    )

    assert isinstance(skill, SkillRequirement)
    assert skill.name
    assert "review" in skill.purpose.lower()
    assert "security" in skill.constraints[0].lower()
    assert skill.activation_conditions


def test_generate_skill_creates_valid_skill_files(tmp_path, monkeypatch):
    def fake_generate_text(prompt: str, *, model=None, timeout=None):
        return FakeLLMResponse(
            """---
name: secure-code-review
description: Reviews Python code for security issues.
---
# Secure Code Review
## Purpose
Helps review Python code for security issues.

## Activation
Trigger when a developer asks for a secure code review.

## Instructions
- Review code for authentication, secret handling, and unsafe input validation.
- Provide concise findings and remediation steps.

## Constraints
- Do not invent vulnerabilities.
- Use only the provided code.
"""
        )

    monkeypatch.setattr("app.backend.skill_generation_service.generate_text", fake_generate_text)

    service = SkillGenerationService(base_dir=tmp_path / "generated-skills")
    result = service.generate_skill(
        "Create a skill that reviews Python code for security issues and triggers when a developer asks for a secure code review.",
        skill_name="secure-code-review",
    )

    assert result.skill_name == "secure-code-review"
    assert (tmp_path / "generated-skills" / "secure-code-review" / "SKILL.md").exists()
    assert result.validation.valid is True


def test_generate_skill_rejects_empty_requirement():
    service = SkillGenerationService()

    with pytest.raises(ValueError, match="empty"):
        service.generate_skill("   ")


def test_validation_rejects_unsafe_paths_and_missing_metadata():
    validator = SkillGenerationValidator()

    invalid = {
        "name": "../escape",
        "description": "",
        "instructions": "",
    }

    result = validator.validate_skill_definition(invalid)
    assert result.valid is False
    assert result.errors


def test_generate_skill_rejects_overwrite_without_approval(tmp_path, monkeypatch):
    target_dir = tmp_path / "generated-skills" / "existing-skill"
    target_dir.mkdir(parents=True)
    skill_file = target_dir / "SKILL.md"
    skill_file.write_text("existing", encoding="utf-8")

    def fake_generate_text(prompt: str, *, model=None, timeout=None):
        return FakeLLMResponse("---\nname: existing-skill\ndescription: Example\n---\n# Existing skill\n\n## Instructions\n- Keep it brief.\n")

    monkeypatch.setattr("app.backend.skill_generation_service.generate_text", fake_generate_text)

    service = SkillGenerationService(base_dir=tmp_path / "generated-skills")

    with pytest.raises(ValueError, match="already exists"):
        service.generate_skill("Create an example skill.", skill_name="existing-skill", allow_overwrite=False)
