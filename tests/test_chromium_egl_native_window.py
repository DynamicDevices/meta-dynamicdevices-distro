"""Hermetic C++ ABI fixture, not a Chromium or BitBake task execution.

The relevant EGL branches come from Chromium 147.0.7727.116's
third_party/khronos/EGL/eglplatform.h: __GBM__ selects void*, while USE_OZONE
selects intptr_t. Exercise the actual legacy patch against that distinction.
"""

from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
RECIPE = ROOT / "recipes-browser/chromium/chromium-ozone-wayland_147.0.7727.116.bbappend"
PATCH = (
    ROOT / "recipes-browser/chromium/chromium-ozone-wayland"
    / "0003-gl-Match-GBM-EGL-native-window-type.patch"
)


class NativeWindowABITests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(shutil.which("c++"), "C++ compiler required")
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.tree = Path(self.temp.name)
        self.source = self.tree / "ui/gl/gl_surface_egl.cc"
        self.source.parent.mkdir(parents=True)
        (self.tree / "gbm.h").write_text("#define __GBM__ 1\n")
        (self.tree / "ui/gl/gl_surface_egl.h").write_text(
            "#pragma once\n#include <cstdint>\n#include <memory>\n"
            "#if defined(__GBM__)\n"
            "using EGLNativeWindowType = void*;\n"
            "#elif defined(USE_OZONE)\n"
            "using EGLNativeWindowType = intptr_t;\n"
            "#else\n#error missing native platform\n#endif\n"
            "namespace gfx { struct VSyncProvider {}; }\n"
            "namespace gl {\nstruct GLDisplayEGL {};\n"
            "struct NativeViewGLSurfaceEGL {\n"
            "  NativeViewGLSurfaceEGL(GLDisplayEGL*, EGLNativeWindowType,\n"
            "      std::unique_ptr<gfx::VSyncProvider>);\n};\n}\n"
        )
        # Match upstream's include location so the real patch applies at line 5.
        self.original = (
            "// Fixture\n// for Chromium\n// native window ABI\n\n"
            '#include "ui/gl/gl_surface_egl.h"\n'
            "gl::NativeViewGLSurfaceEGL::NativeViewGLSurfaceEGL(\n"
            "    GLDisplayEGL*, EGLNativeWindowType,\n"
            "    std::unique_ptr<gfx::VSyncProvider>) {}\n"
        )
        self.source.write_text(self.original)
        (self.tree / "caller.cc").write_text(
            '#include "ui/gl/gl_surface_egl.h"\n'
            "int main() {\n"
            "  gl::NativeViewGLSurfaceEGL surface(nullptr, 0, {});\n}\n"
        )

    def apply_patch(self, reverse=False):
        command = ["patch", "-d", str(self.tree), "-p1", "--fuzz=0"]
        if reverse:
            command.append("--reverse")
        with PATCH.open() as patch:
            result = subprocess.run(
                command, stdin=patch, capture_output=True, text=True, timeout=10,
            )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def link(self):
        return subprocess.run(
            ["c++", "-std=c++17", "-DUSE_OZONE", "-I", str(self.tree),
             str(self.source), str(self.tree / "caller.cc"),
             "-o", str(self.tree / "fixture")],
            capture_output=True, text=True, timeout=20,
        )

    def test_fresh_upstream_include_order_links(self):
        result = self.link()
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_legacy_patch_reproduces_failure_and_reversal_fixes_it(self):
        self.apply_patch()
        broken = self.link()
        self.assertNotEqual(broken.returncode, 0)
        self.assertIn("undefined reference", broken.stderr)
        self.assertIn("NativeViewGLSurfaceEGL", broken.stderr)
        self.assertIn("long", broken.stderr)
        self.apply_patch(reverse=True)
        self.assertEqual(self.source.read_text(), self.original)
        fixed = self.link()
        self.assertEqual(fixed.returncode, 0, fixed.stderr)

    def test_recipe_only_reverses_patch_and_preserves_j16_and_streaming(self):
        recipe = RECIPE.read_text()
        self.assertIn("if grep -Fq '#include <gbm.h>'", recipe)
        self.assertNotIn("if ! grep -Fq '#include <gbm.h>'", recipe)
        self.assertIn('patch -d "${S}" -p1 --reverse --fuzz=0', recipe)
        self.assertIn('${DD_CHROMIUM_LEGACY_GBM_PATCH}:True', recipe)
        self.assertIn('PARALLEL_MAKE = "-j 16"', recipe)
        self.assertIn('python3 "${DD_CHROMIUM_LIVE_BUILD}"', recipe)


if __name__ == "__main__":
    unittest.main()
