from pathlib import Path

import yaml

KEYWORDS_PATH = Path(__file__).resolve().parent.parent / "config" / "keywords.yaml"


def _load_keywords():
    with open(KEYWORDS_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f)


def test_keywords_yaml_file_exists():
    assert KEYWORDS_PATH.is_file()


def test_keywords_yaml_has_therapeutic_groups():
    data = _load_keywords()

    assert "therapeutic_groups" in data
    assert isinstance(data["therapeutic_groups"], list)
    assert len(data["therapeutic_groups"]) > 0


def test_each_group_has_name_and_active_ingredients():
    data = _load_keywords()

    for group in data["therapeutic_groups"]:
        assert "group" in group
        assert isinstance(group["group"], str) and group["group"].strip()
        assert "active_ingredients" in group
        assert isinstance(group["active_ingredients"], list)
        assert len(group["active_ingredients"]) > 0
        for ingredient in group["active_ingredients"]:
            assert isinstance(ingredient, str) and ingredient.strip()


def test_keywords_yaml_has_minimum_active_ingredients():
    data = _load_keywords()

    total = sum(len(group["active_ingredients"]) for group in data["therapeutic_groups"])
    assert total >= 5


def test_keywords_yaml_has_source_metadata():
    data = _load_keywords()

    assert "source" in data
    assert "official_site" in data["source"]
