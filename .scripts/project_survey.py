#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def replace_marker(text: str, marker: str, body: str) -> str:
    pattern = re.compile(
        rf"(<!--\s*survey:start:{re.escape(marker)}\s*-->)(.*?)(<!--\s*survey:end:{re.escape(marker)}\s*-->)",
        re.DOTALL,
    )
    updated, count = pattern.subn(rf"\1\n{body.rstrip()}\n\3", text, count=1)
    if count != 1:
        raise ValueError(f"Marker not found: {marker}")
    return updated


def update_file(path: Path, marker_map: dict[str, str]) -> None:
    text = read_text(path)
    for marker, body in marker_map.items():
        text = replace_marker(text, marker, body)
    write_text(path, text)


def parse_scalar(value: str):
    value = value.strip()
    if not value:
        return ""
    if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
        return value[1:-1]
    lowered = value.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    if lowered in {"null", "none"}:
        return ""
    return value


def load_config(path: Path) -> dict:
    root: dict = {}
    stack: list[tuple[int, dict]] = [(0, root)]

    for lineno, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue

        indent = len(raw_line) - len(raw_line.lstrip(" "))
        if indent % 2 != 0:
            raise ValueError(f"Indent must be multiples of 2 spaces: line {lineno}")

        line = raw_line.strip()
        if ":" not in line:
            raise ValueError(f"Invalid line: {lineno}")

        key, raw_value = line.split(":", 1)
        key = key.strip()
        raw_value = raw_value.strip()

        while len(stack) > 1 and indent < stack[-1][0]:
            stack.pop()

        current = stack[-1][1]
        if raw_value == "":
            child: dict = {}
            current[key] = child
            stack.append((indent + 2, child))
        else:
            current[key] = parse_scalar(raw_value)

    return root


def get_config(config: dict, dotted_key: str, default: str = "") -> str:
    current = config
    for part in dotted_key.split("."):
        if not isinstance(current, dict):
            return default
        current = current.get(part, default)
    if current in {None, False}:
        return ""
    if current is True:
        return "true"
    return str(current or default)


def major_directories() -> list[str]:
    excluded = {
        ".git",
        ".github",
        ".vscode",
        ".idea",
        ".claude",
        ".agents",
        ".githooks",
        "node_modules",
        "vendor",
        "__pycache__",
    }
    dirs = []
    for path in sorted(ROOT.iterdir()):
        if path.is_dir() and path.name not in excluded and not path.name.startswith("."):
            dirs.append(path.name)
    return dirs


def detect_stack() -> list[str]:
    stack: list[str] = []
    package_json = ROOT / "package.json"
    composer_json = ROOT / "composer.json"
    requirements = ROOT / "requirements.txt"
    gemfile = ROOT / "Gemfile"

    if package_json.exists():
        stack.append("Node.js")
        data = json.loads(read_text(package_json))
        deps = {
            **data.get("dependencies", {}),
            **data.get("devDependencies", {}),
        }
        if "next" in deps:
            stack.append("Next.js")
        elif "react" in deps:
            stack.append("React")
        elif "vue" in deps:
            stack.append("Vue")
        elif "svelte" in deps:
            stack.append("Svelte")
        if "typescript" in deps or (ROOT / "tsconfig.json").exists():
            stack.append("TypeScript")
    if composer_json.exists():
        stack.append("PHP")
    elif any(ROOT.glob("*.php")) or any(ROOT.rglob("*.php")):
        stack.append("PHP")
    if requirements.exists():
        stack.append("Python")
    if gemfile.exists():
        stack.append("Ruby")
    if (ROOT / "wp-content").exists() or (ROOT / "wp-includes").exists():
        stack.append("WordPress")
    if any(ROOT.glob("vite.config.*")):
        stack.append("Vite")
    if any(ROOT.glob("webpack*.js")):
        stack.append("Webpack")
    if (ROOT / "gulpfile.js").exists():
        stack.append("Gulp")
    if (ROOT / "tailwind.config.js").exists() or (ROOT / "tailwind.config.ts").exists():
        stack.append("Tailwind CSS")

    return list(dict.fromkeys(stack))


def detect_css_convention() -> str:
    if (ROOT / "tailwind.config.js").exists() or (ROOT / "tailwind.config.ts").exists():
        return "Tailwind CSS"

    css_files = list(ROOT.rglob("*.css"))[:20] + list(ROOT.rglob("*.scss"))[:20]
    sample = "\n".join(read_text(path)[:4000] for path in css_files[:10] if path.is_file())
    if re.search(r"\.[A-Za-z0-9_-]+__[A-Za-z0-9_-]+", sample) and re.search(
        r"\.[A-Za-z0-9_-]+--[A-Za-z0-9_-]+", sample
    ):
        return "BEM 系の可能性"
    if {"foundation", "layout", "object"}.issubset({path.name for path in ROOT.rglob("*") if path.is_dir()}):
        return "FLOCSS 系の可能性"
    if sample:
        return "独自規約または要確認"
    return "CSS ファイル未検出"


def detect_editorconfig() -> str:
    editorconfig = ROOT / ".editorconfig"
    if not editorconfig.exists():
        return "要確認"
    text = read_text(editorconfig)
    style = re.search(r"indent_style\s*=\s*(\w+)", text)
    size = re.search(r"indent_size\s*=\s*(\w+)", text)
    parts = []
    if style:
        parts.append(f"indent_style={style.group(1)}")
    if size:
        parts.append(f"indent_size={size.group(1)}")
    return ", ".join(parts) if parts else "あり"


def detect_verification() -> list[str]:
    items: list[str] = []
    package_json = ROOT / "package.json"
    if package_json.exists():
        data = json.loads(read_text(package_json))
        scripts = data.get("scripts", {})
        for key in ["lint", "test", "build", "format", "check"]:
            if key in scripts:
                items.append(f"`npm run {key}`")
    composer_json = ROOT / "composer.json"
    if composer_json.exists():
        data = json.loads(read_text(composer_json))
        scripts = data.get("scripts", {})
        for key in scripts.keys():
            items.append(f"`composer {key}`")
    if (ROOT / "phpunit.xml").exists() or (ROOT / "phpunit.xml.dist").exists():
        items.append("`phpunit`")
    if (ROOT / "pytest.ini").exists() or (ROOT / "pyproject.toml").exists():
        items.append("`pytest`")
    if not items:
        items.append("要確認")
    return list(dict.fromkeys(items))


def detect_commit_style() -> str:
    git_dir = ROOT / ".git"
    if not git_dir.exists():
        return "履歴未確認"
    head_log = ROOT / ".git" / "logs" / "HEAD"
    if not head_log.exists():
        return "履歴未確認"
    lines = head_log.read_text(encoding="utf-8", errors="ignore").splitlines()
    messages = [line.split("\t", 1)[-1] for line in lines if "\t" in line][-5:]
    if not messages:
        return "履歴未確認"
    if any(re.match(r"(機能追加|修正|改善|スタイル|設定|ドキュメント|削除|初期構築|テスト|WIP): ", msg) for msg in messages):
        return "日本語 prefix 形式"
    if any(re.match(r"[a-z]+: ", msg) for msg in messages):
        return "英語 type 形式"
    if any(re.search(r"[ぁ-んァ-ン一-龠]", msg) and ":" not in msg for msg in messages):
        return "具体的な日本語要約形式"
    return "要確認"


def build_project_overview(config: dict) -> str:
    name = get_config(config, "project.name", "要入力")
    client = get_config(config, "project.client", "要入力")
    project_type = get_config(config, "project.type", "要入力") or "要入力"
    dirs = ", ".join(f"`{name}`" for name in major_directories()[:6]) or "要確認"
    return "\n".join(
        [
            f"- プロジェクト名: {name}",
            f"- クライアント: {client}",
            f"- 案件種別: {project_type}",
            "- プロジェクト種別: 既存案件の後付け導入",
            f"- 主要ディレクトリ: {dirs}",
        ]
    )


def build_tech_stack() -> str:
    stack = detect_stack()
    if not stack:
        return "- 要確認"
    return "\n".join(f"- {item}" for item in stack)


def build_directory_structure() -> str:
    dirs = major_directories()
    if not dirs:
        return "- 要確認"
    return "\n".join(f"- `{name}/`" for name in dirs)


def build_detected_conventions() -> str:
    parts = [
        f"- `.editorconfig`: {detect_editorconfig()}",
        f"- CSS 方針: {detect_css_convention()}",
        f"- コミット慣習: {detect_commit_style()}",
    ]
    if (ROOT / ".eslintrc.js").exists() or (ROOT / ".eslintrc.cjs").exists() or (ROOT / ".eslintrc.json").exists():
        parts.append("- ESLint: あり")
    if (ROOT / ".prettierrc").exists() or (ROOT / ".prettierrc.json").exists():
        parts.append("- Prettier: あり")
    if (ROOT / "stylelint.config.js").exists() or (ROOT / ".stylelintrc").exists():
        parts.append("- Stylelint: あり")
    return "\n".join(parts)


def build_available_verification() -> str:
    return "\n".join(f"- {item}" for item in detect_verification())


def build_environment_summary(config: dict) -> str:
    return "\n".join(
        [
            f"- PROD URL: {get_config(config, 'environment.prod_url', '要入力') or '要入力'}",
            f"- STG URL: {get_config(config, 'environment.stg_url', '要入力') or '要入力'}",
            f"- Local URL: {get_config(config, 'environment.local_url', '任意') or '任意'}",
        ]
    )


def build_deployment_summary(config: dict) -> str:
    method = get_config(config, "deployment.method", "要入力") or "要入力"
    owner_type = get_config(config, "repository.owner_type", "要入力") or "要入力"
    owner_name = get_config(config, "repository.owner_name", "要入力") or "要入力"
    repo_name = get_config(config, "repository.repo_name", "要入力") or "要入力"
    repo_description = get_config(config, "repository.description", "任意") or "任意"
    ensure_remote_repo = get_config(config, "repository.ensure_remote_repo", "false") or "false"
    default_target = get_config(config, "deployment.default_target", "要入力") or "要入力"
    script = get_config(config, "deployment.deploy_script", "任意") or "任意"
    sync_script = get_config(config, "deployment.sync_script", "任意") or "任意"
    rollback_script = get_config(config, "deployment.rollback_script", "任意") or "任意"
    backup_before = get_config(config, "deployment.backup_before_deploy", "true") or "true"
    backup_dir = get_config(config, "deployment.backup_dir", "要入力") or "要入力"
    backup_retention = get_config(config, "deployment.backup_retention", "要入力") or "要入力"
    notes = get_config(config, "deployment.notes", "任意") or "任意"
    return "\n".join(
        [
            f"- 配備方法: {method}",
            f"- GitHub 所有者種別: {owner_type}",
            f"- GitHub 所有者名: {owner_name}",
            f"- GitHub リポジトリ名: {repo_name}",
            f"- GitHub 説明文: {repo_description}",
            f"- GitHub 自動作成: {ensure_remote_repo}",
            f"- 既定ターゲット: {default_target}",
            f"- 配備スクリプト: {script}",
            f"- 同期スクリプト: {sync_script}",
            f"- ロールバックスクリプト: {rollback_script}",
            f"- 反映前バックアップ: {backup_before}",
            f"- バックアップ先: {backup_dir}",
            f"- 保持世代: {backup_retention}",
            f"- 補足: {notes}",
        ]
    )


def build_open_questions(config: dict) -> str:
    questions: list[str] = []
    if not get_config(config, "environment.prod_url"):
        questions.append("PROD URL が未入力")
    if not get_config(config, "environment.stg_url"):
        questions.append("STG URL が未入力")
    if not get_config(config, "deployment.method"):
        questions.append("デプロイ方法が未入力")
    if not get_config(config, "repository.owner_type"):
        questions.append("GitHub の個人 / 組織が未入力")
    if not get_config(config, "repository.owner_name"):
        questions.append("GitHub の所有者名が未入力")
    if not get_config(config, "repository.repo_name"):
        questions.append("GitHub リポジトリ名が未入力")
    if get_config(config, "deployment.backup_before_deploy", "true") == "true" and not get_config(
        config, "deployment.rollback_script"
    ):
        questions.append("ロールバック用スクリプトが未入力")
    if not (ROOT / "README.md").exists():
        questions.append("README.md が見つからないため、運用文書の正本を要確認")
    if not questions:
        questions.append("特になし")
    return "\n".join(f"- {item}" for item in questions)


def build_repo_survey_doc(config: dict) -> str:
    return f"""# Repo Survey

このファイルは `.scripts/project_survey.py` により更新されます。

## Project overview

{build_project_overview(config)}

## Tech stack

{build_tech_stack()}

## Directory structure

{build_directory_structure()}

## Detected conventions

{build_detected_conventions()}

## Available verification

{build_available_verification()}

## Environment summary

{build_environment_summary(config)}

## Deployment summary

{build_deployment_summary(config)}

## Open questions

{build_open_questions(config)}
"""


def main() -> None:
    parser = argparse.ArgumentParser(description="Survey current repository structure and update docs.")
    parser.add_argument("--config", default=".claude/project.config.yaml")
    args = parser.parse_args()

    config = load_config(ROOT / args.config)
    marker_map = {
        "project-overview": build_project_overview(config),
        "tech-stack": build_tech_stack(),
        "directory-structure": build_directory_structure(),
        "detected-conventions": build_detected_conventions(),
        "available-verification": build_available_verification(),
        "environment-summary": build_environment_summary(config),
        "deployment-summary": build_deployment_summary(config),
        "open-questions": build_open_questions(config),
    }

    update_file(ROOT / "CLAUDE.md", marker_map)
    update_file(ROOT / "AGENTS.md", marker_map)
    write_text(ROOT / "doc" / "repo-survey.md", build_repo_survey_doc(config))

    print("Survey updated these files:")
    for file_path in [ROOT / "CLAUDE.md", ROOT / "AGENTS.md", ROOT / "doc" / "repo-survey.md"]:
        print(f"- {file_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
