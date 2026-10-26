from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from app.backend.config import get_llm_settings
from app.backend.llm_service import generate_text
from app.backend.skill_validation_service import SkillValidationService


@dataclass
class SkillRequirement:
    name: str
    description: str
    purpose: str
    use_cases: list[str] = field(default_factory=list)
    activation_conditions: list[str] = field(default_factory=list)
    instructions: list[str] = field(default_factory=list)
    constraints: list[str] = field(default_factory=list)
    required_tools: list[str] = field(default_factory=list)
    required_files: list[str] = field(default_factory=list)
    safety_requirements: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "purpose": self.purpose,
            "use_cases": self.use_cases,
            "activation_conditions": self.activation_conditions,
            "instructions": self.instructions,
            "constraints": self.constraints,
            "required_tools": self.required_tools,
            "required_files": self.required_files,
            "safety_requirements": self.safety_requirements,
        }


@dataclass
class SkillValidationResult:
    valid: bool
    errors: list[str] = field(default_factory=list)


@dataclass
class SkillGenerationResult:
    skill_name: str
    output_dir: Path
    files: list[Path]
    validation: SkillValidationResult


class SkillGenerationValidator:
    def validate_skill_definition(self, skill: dict[str, Any] | SkillRequirement) -> SkillValidationResult:
        payload = skill.to_dict() if isinstance(skill, SkillRequirement) else skill
        errors: list[str] = []

        name = str(payload.get("name") or "").strip()
        if not name:
            errors.append("Skill name is required.")
        elif not re.fullmatch(r"[a-z0-9][a-z0-9-]{1,63}", name):
            errors.append("Skill name must be a lowercase slug using letters, numbers, and hyphen separators.")
        if ".." in name:
            errors.append("Skill name cannot contain path traversal sequences.")

        description = str(payload.get("description") or "").strip()
        if not description:
            errors.append("Skill description is required.")

        purpose = str(payload.get("purpose") or "").strip()
        if not purpose:
            errors.append("Skill purpose is required.")

        instructions = self._as_list(payload.get("instructions"))
        if not instructions:
            errors.append("At least one instruction must be provided.")

        constraints = self._as_list(payload.get("constraints"))
        if not constraints:
            errors.append("At least one constraint must be provided.")

        activation = self._as_list(payload.get("activation_conditions"))
        if not activation:
            errors.append("Activation conditions are required.")

        for field_name, value in {
            "description": description,
            "purpose": purpose,
            "instructions": "\n".join(instructions),
            "constraints": "\n".join(constraints),
        }.items():
            if self._contains_secret(value):
                errors.append(f"{field_name} contains a hardcoded secret or credential-like value.")

        required_files = self._as_list(payload.get("required_files"))
        for ref in required_files:
            if not ref or ".." in ref or ref.startswith("/"):
                errors.append(f"Required file reference '{ref}' is invalid.")

        return SkillValidationResult(valid=not errors, errors=errors)

    @staticmethod
    def validate_skill_markdown(markdown: str) -> SkillValidationResult:
        errors: list[str] = []
        normalized = (markdown or "").strip()
        if not normalized:
            return SkillValidationResult(valid=False, errors=["Generated SKILL.md content is empty."])

        if "# " not in normalized:
            errors.append("SKILL.md must contain a top-level heading.")
        if "## Purpose" not in normalized and "## Instructions" not in normalized:
            errors.append("SKILL.md must include the required purpose or instructions sections.")
        if "---" not in normalized and "name:" not in normalized.lower():
            errors.append("SKILL.md must include the required metadata block.")

        if "api_key" in normalized.lower() or "password" in normalized.lower() or "token" in normalized.lower():
            errors.append("Generated content must not embed credentials or secrets.")

        return SkillValidationResult(valid=not errors, errors=errors)

    @staticmethod
    def _as_list(value: Any) -> list[str]:
        if value is None:
            return []
        if isinstance(value, str):
            return [item.strip() for item in value.splitlines() if item.strip()]
        if isinstance(value, (list, tuple, set)):
            return [str(item).strip() for item in value if str(item).strip()]
        return [str(value).strip()]

    @staticmethod
    def _contains_secret(value: str) -> bool:
        lowered = value.lower()
        secret_patterns = [
            "api_key",
            "apikey",
            "password",
            "passwd",
            "token=",
            "bearer ",
            "client_secret",
            "secret_key",
            "aws_secret",
            "sk_live",
            "sk_test",
            "private_key",
        ]
        return any(pattern in lowered for pattern in secret_patterns)


class SkillGenerationService:
    def __init__(self, *, base_dir: str | Path | None = None, llm_client: Any | None = None):
        self.base_dir = Path(base_dir) if base_dir is not None else Path.cwd() / "generated_skills"
        self.llm_client = llm_client or self._DefaultLLMClient()
        self.validator = SkillGenerationValidator()
        self.validation_service = SkillValidationService()

    def analyze_requirement(self, requirement: str) -> SkillRequirement:
        normalized = (requirement or "").strip()
        if not normalized:
            raise ValueError("Requirement must not be empty.")
        if len(normalized) > get_llm_settings().max_prompt_length:
            raise ValueError(f"Requirement must be {get_llm_settings().max_prompt_length} characters or fewer.")

        name_words = re.findall(r"[a-zA-Z0-9]+", normalized.lower())[:6]
        default_name = "-".join(name_words) if name_words else "generated-skill"
        skill_name = self._slugify(default_name)

        purpose = self._extract_purpose(normalized)
        activation = self._extract_activation_conditions(normalized)
        instructions = self._extract_instructions(normalized)
        constraints = [
            "Review the relevant code paths for security and reliability concerns.",
            "Do not invent facts or claim unsupported behavior.",
            "Use only the user-provided context when forming guidance.",
            "Keep instructions precise, safe, and actionable.",
            "Never embed credentials or hardcoded values.",
        ]
        required_tools = self._extract_tools(normalized)
        required_files = ["references/overview.md"] if "reference" in normalized.lower() else []

        return SkillRequirement(
            name=skill_name,
            description=self._summarize(normalized),
            purpose=purpose,
            use_cases=self._extract_use_cases(normalized),
            activation_conditions=activation,
            instructions=instructions,
            constraints=constraints,
            required_tools=required_tools,
            required_files=required_files,
            safety_requirements=["Do not write outside the approved output directory.", "Do not execute generated scripts automatically."],
        )

    def generate_skill(
        self,
        requirement: str,
        *,
        skill_name: str | None = None,
        output_dir: str | Path | None = None,
        allow_overwrite: bool = False,
    ) -> SkillGenerationResult:
        if requirement is None or not str(requirement).strip():
            raise ValueError("Requirement must not be empty.")

        requirement_obj = self.analyze_requirement(requirement)
        if skill_name:
            requirement_obj.name = self._slugify(skill_name)

        skill_dict = requirement_obj.to_dict()
        validation = self.validator.validate_skill_definition(skill_dict)
        if not validation.valid:
            raise ValueError("; ".join(validation.errors))

        target_dir = self._resolve_output_dir(output_dir or self.base_dir, requirement_obj.name)
        if target_dir.exists() and not allow_overwrite:
            raise ValueError(f"Skill directory '{target_dir.name}' already exists. Set allow_overwrite=True to replace it.")

        if target_dir.exists() and allow_overwrite:
            for path in sorted(target_dir.rglob("*"), reverse=True):
                if path.is_file():
                    path.unlink()
                elif path.is_dir():
                    path.rmdir()

        target_dir.mkdir(parents=True, exist_ok=True)

        llm_prompt = self._build_generation_prompt(requirement_obj)
        raw_response = self.llm_client.generate(llm_prompt)
        markdown = self._extract_text(raw_response)
        if not markdown:
            raise ValueError("The LLM returned an empty response for the skill draft.")

        skill_markdown = self._normalize_skill_markdown(markdown, requirement_obj)
        markdown_validation = self.validator.validate_skill_markdown(skill_markdown)
        if not markdown_validation.valid:
            raise ValueError("; ".join(markdown_validation.errors))

        skill_file = target_dir / "SKILL.md"
        skill_file.write_text(skill_markdown, encoding="utf-8")

        generated_files = [skill_file]
        for ref in requirement_obj.required_files:
            ref_path = self._resolve_output_dir(target_dir, ref)
            ref_path.parent.mkdir(parents=True, exist_ok=True)
            ref_path.write_text(
                "# Reference\n\nThis file was generated as part of the requested skill support material.\n",
                encoding="utf-8",
            )
            generated_files.append(ref_path)

        final_validation = self.validator.validate_skill_definition(requirement_obj.to_dict())
        if not final_validation.valid:
            raise ValueError("; ".join(final_validation.errors))

        validation_result = self.validation_service.validate_generated_skill(
            requirement=requirement,
            skill_definition=requirement_obj.to_dict(),
            generated_files=generated_files,
            output_dir=target_dir,
        )
        if not validation_result.is_valid:
            raise ValueError("; ".join(str(item["message"]) for item in validation_result.errors))

        return SkillGenerationResult(
            skill_name=requirement_obj.name,
            output_dir=target_dir,
            files=generated_files,
            validation=final_validation,
        )

    @staticmethod
    def _build_generation_prompt(skill: SkillRequirement) -> str:
        return (
            "Create a portable GitHub Copilot-style SKILL.md file from the following structured skill definition. "
            "Return markdown with YAML front matter and sections named Purpose, Activation, Instructions, and Constraints. "
            "Do not include secrets or path traversal.\n\n"
            f"Skill name: {skill.name}\n"
            f"Description: {skill.description}\n"
            f"Purpose: {skill.purpose}\n"
            f"Use cases: {', '.join(skill.use_cases) if skill.use_cases else 'General use'}\n"
            f"Activation conditions: {', '.join(skill.activation_conditions) if skill.activation_conditions else 'Triggered by a user request'}\n"
            f"Instructions: {'; '.join(skill.instructions) if skill.instructions else 'Follow the user request carefully.'}\n"
            f"Constraints: {'; '.join(skill.constraints) if skill.constraints else 'Never invent facts.'}\n"
            f"Required tools: {', '.join(skill.required_tools) if skill.required_tools else 'None specified'}\n"
        )

    @staticmethod
    def _extract_text(response: Any) -> str:
        if response is None:
            return ""
        if isinstance(response, str):
            return response
        if hasattr(response, "text"):
            return str(response.text)
        if hasattr(response, "response"):
            return str(response.response)
        if isinstance(response, dict):
            return str(response.get("response") or response.get("text") or response.get("content") or "")
        return str(response)

    @staticmethod
    def _normalize_skill_markdown(markdown: str, skill: SkillRequirement) -> str:
        cleaned = markdown.strip()
        if cleaned.startswith("---"):
            return cleaned

        lines = [
            "---",
            f"name: {skill.name}",
            f"description: {skill.description}",
            "---",
            "",
            f"# {skill.name.replace('-', ' ').title()}",
            "",
            "## Purpose",
            skill.purpose,
            "",
            "## Activation",
            *[f"- {item}" for item in skill.activation_conditions],
            "",
            "## Instructions",
            *[f"- {item}" for item in skill.instructions],
            "",
            "## Constraints",
            *[f"- {item}" for item in skill.constraints],
            "",
        ]
        return "\n".join(lines)

    @staticmethod
    def _summarize(requirement: str) -> str:
        sentence = re.split(r"(?<=[.!?])\s+", requirement.strip())[0]
        if len(sentence) > 140:
            sentence = sentence[:137].rstrip() + "..."
        return sentence or "Generated AI skill."

    @staticmethod
    def _extract_purpose(requirement: str) -> str:
        lowered = requirement.lower()
        if "review" in lowered and "code" in lowered:
            return "Review code for quality, correctness, security, and maintainability concerns."
        if "create" in lowered and "skill" in lowered:
            return "Create a reusable, structured skill based on the user’s stated requirements."
        return "Provide clear, actionable guidance based on the user requirement."

    @staticmethod
    def _extract_use_cases(requirement: str) -> list[str]:
        if "code" in requirement.lower() and "review" in requirement.lower():
            return ["Review code for likely issues and recommended improvements."]
        return ["Respond to user requests that match the described workflow."]

    @staticmethod
    def _extract_activation_conditions(requirement: str) -> list[str]:
        lowered = requirement.lower()
        if "when" in lowered or "trigger" in lowered or "if" in lowered:
            return ["When the user asks for this task or an equivalent request, use the defined workflow."]
        return ["When the user asks for this workflow, follow the instructions in this skill."]

    @staticmethod
    def _extract_instructions(requirement: str) -> list[str]:
        base = [
            "Read the user request carefully and preserve the original intent.",
            "Apply the workflow in a concise and structured way.",
            "Do not invent missing facts or unsupported assumptions.",
        ]
        if "code" in requirement.lower() and "review" in requirement.lower():
            base.append("Assess the code for correctness, maintainability, and security risks.")
        return base

    @staticmethod
    def _extract_tools(requirement: str) -> list[str]:
        lowered = requirement.lower()
        tools: list[str] = []
        if "python" in lowered:
            tools.append("python")
        if "shell" in lowered or "bash" in lowered:
            tools.append("shell")
        if "review" in lowered and "code" in lowered:
            tools.append("code-review")
        return tools or ["general-purpose agent workflow"]

    @staticmethod
    def _slugify(value: str) -> str:
        slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
        return slug or "generated-skill"

    def _resolve_output_dir(self, base: str | Path, skill_name: str) -> Path:
        root = Path(base).resolve()
        candidate = root / self._slugify(skill_name)
        try:
            candidate.relative_to(root)
        except ValueError as exc:
            raise ValueError("Skill output path escapes the designated base directory.") from exc
        return candidate

    class _DefaultLLMClient:
        def generate(self, prompt: str) -> Any:
            return generate_text(prompt)
