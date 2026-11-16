#!/usr/bin/env python3
"""Source-level optional-layer regression; does not execute BitBake tasks."""

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def assignments(text, variable):
    """Read literal += assignments, including backslash-continued lines."""
    return re.findall(
        rf'^\s*{re.escape(variable)}\s*\+=\s*"([^"]*)"',
        text.replace("\\\n", " "),
        re.MULTILINE,
    )


def registered_files(collections):
    config = (ROOT / "conf/layer.conf").read_text()
    patterns = " ".join(assignments(config, "BBFILES")).split()
    for entry in " ".join(assignments(config, "BBFILES_DYNAMIC")).split():
        collection, pattern = entry.split(":", 1)
        if collection in collections:
            patterns.append(pattern)
    files = set()
    for pattern in patterns:
        files.update(ROOT.glob(pattern.replace("${LAYERDIR}/", "")))
    return files


class OptionalGodotLayerTest(unittest.TestCase):
    def setUp(self):
        self.append = (
            ROOT / "dynamic-layers/godot-layer/recipes-graphics/godot/godot_%.bbappend"
        )

    def test_absent_without_godot_layer(self):
        self.assertTrue(self.append.is_file())
        self.assertNotIn(self.append, registered_files(set()))
        self.assertFalse((ROOT / "recipes-graphics/godot/godot_%.bbappend").exists())

    def test_present_with_godot_layer(self):
        without = registered_files(set())
        with_godot = registered_files({"godot-layer"})
        self.assertEqual(with_godot - without, {self.append})
        self.assertFalse(without - with_godot)

    def test_unrelated_collection_does_not_enable_godot(self):
        self.assertEqual(registered_files({"gnome-layer"}), registered_files(set()))

    def test_dangling_appends_not_globally_suppressed(self):
        config = (ROOT / "conf/layer.conf").read_text()
        self.assertNotIn("BB_DANGLINGAPPENDS_WARNONLY", config)
        self.assertNotIn("BBMASK", config)


if __name__ == "__main__":
    unittest.main()
