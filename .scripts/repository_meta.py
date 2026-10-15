#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import unicodedata
from pathlib import Path
from urllib.parse import urlparse


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


def get_value(data: dict, dotted_key: str, default: str = "") -> str:
    current = data
    for part in dotted_key.split("."):
        if not isinstance(current, dict):
            return default
        current = current.get(part, default)
    if current in {None, False}:
        return ""
    if current is True:
        return "true"
    return str(current or default)


def slugify(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).strip().lower()
    normalized = re.sub(r"[／/・\s_]+", "-", normalized)
    normalized = re.sub(r"[^a-z0-9-]", "-", normalized)
    normalized = re.sub(r"-{2,}", "-", normalized)
    return normalized.strip("-")


def normalize_type(value: str) -> str:
    raw = value.strip().lower()
    mapping = {
        "corporate": "corporate",
        "corporate-site": "corporate",
        "corp": "corporate",
        "コーポレート": "corporate",
        "採用": "recruit",
        "recruit": "recruit",
        "lp": "lp",
        "landing-page": "lp",
        "landing": "lp",
        "service": "service",
        "サービス": "service",
        "campaign": "campaign",
        "キャンペーン": "campaign",
        "brand": "brand",
        "ブランド": "brand",
        "wordpress": "wp",
        "wp": "wp",
    }
    if raw in mapping:
        return mapping[raw]
    return slugify(raw)


def humanize_type_ja(value: str) -> str:
    raw = value.strip().lower()
    mapping = {
        "corporate": "コーポレートサイト",
        "corporate-site": "コーポレートサイト",
        "corp": "コーポレートサイト",
        "コーポレート": "コーポレートサイト",
        "採用": "採用サイト",
        "recruit": "採用サイト",
        "lp": "LP",
        "landing-page": "LP",
        "landing": "LP",
        "service": "サービスサイト",
        "サービス": "サービスサイト",
        "campaign": "キャンペーンサイト",
        "キャンペーン": "キャンペーンサイト",
        "brand": "ブランドサイト",
        "ブランド": "ブランドサイト",
        "wordpress": "WordPress サイト",
        "wp": "WordPress サイト",
    }
    if raw in mapping:
        return mapping[raw]
    return value.strip()


def build_project_label(config: dict) -> str:
    project_name = get_value(config, "project.name")
    if project_name and project_name not in {"案件名", "要入力"}:
        return project_name
    return humanize_type_ja(get_value(config, "project.type"))


def apply_rule(rule: str, values: dict[str, str]) -> str:
    result = rule
    for token, value in values.items():
        result = result.replace(token, value)
    return result


_MULTI_PART_TLDS = {
    "co.jp", "or.jp", "ne.jp", "ac.jp", "go.jp", "ed.jp", "gr.jp", "lg.jp",
}


def repo_name_from_url(url: str) -> str:
    """公開 URL からリポジトリ名を導出する。

    www. と TLD を除き、サブドメインがあれば「サブドメイン-ドメイン」で返す。
    例:
        https://www.heim-k.com/   → heim-k
        https://recruit.heim-k.com/ → recruit-heim-k
    """
    parsed = urlparse(url)
    host = parsed.hostname or parsed.path.split("/")[0]
    if not host:
        return ""
    if host.startswith("www."):
        host = host[4:]
    parts = host.split(".")
    if len(parts) >= 3 and ".".join(parts[-2:]) in _MULTI_PART_TLDS:
        parts = parts[:-2]
    elif len(parts) >= 2:
        parts = parts[:-1]
    return "-".join(parts)


def build_repo_name(config: dict) -> str:
    prod_url = get_value(config, "environment.prod_url")
    if prod_url:
        name = repo_name_from_url(prod_url)
        if name:
            return slugify(name)
    rule = get_value(config, "repository.naming_rule", "<client-slug>-<project-slug>") or "<client-slug>-<project-slug>"
    client_slug = get_value(config, "project.client_slug")
    project_slug = get_value(config, "project.slug")
    project_type = normalize_type(get_value(config, "project.type"))
    repo_name = apply_rule(
        rule,
        {
            "<client-slug>": client_slug,
            "<project-slug>": project_slug,
            "<project-type>": project_type,
        },
    )
    repo_name = slugify(repo_name)
    return repo_name


def build_repo_description(config: dict) -> str:
    configured = get_value(config, "repository.description")
    if configured:
        return configured
    rule = get_value(config, "repository.description_rule", "<client>　<project-label>") or "<client>　<project-label>"
    description = apply_rule(
        rule,
        {
            "<client>": get_value(config, "project.client"),
            "<project-name>": get_value(config, "project.name"),
            "<project-label>": build_project_label(config),
            "<project-type-ja>": humanize_type_ja(get_value(config, "project.type")),
        },
    )
    description = re.sub(r"[ \t]{2,}", " ", description)
    return description.strip()


def build_remote_url(config: dict) -> str:
    provider = get_value(config, "repository.provider", "github").lower() or "github"
    if provider != "github":
        return ""
    owner = get_value(config, "repository.owner_name")
    repo_name = get_value(config, "repository.repo_name") or build_repo_name(config)
    protocol = get_value(config, "repository.protocol", "ssh").lower() or "ssh"
    if not owner or not repo_name:
        return ""
    if protocol == "https":
        return f"https://github.com/{owner}/{repo_name}.git"
    return f"git@github.com:{owner}/{repo_name}.git"


def main() -> None:
    parser = argparse.ArgumentParser(description="Build repository metadata from .claude/project.config.yaml")
    parser.add_argument("mode", choices=["repo-name", "remote-url", "repo-description"])
    parser.add_argument("--config", default=".claude/project.config.yaml")
    args = parser.parse_args()

    config = load_config(Path(args.config))
    if args.mode == "repo-name":
        print(build_repo_name(config))
    elif args.mode == "repo-description":
        print(build_repo_description(config))
    else:
        print(build_remote_url(config))


if __name__ == "__main__":
    main()
