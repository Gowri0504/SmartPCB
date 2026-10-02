import unittest
import os
import subprocess
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BACKEND_DIR = os.path.join(ROOT, "backend")
SERVER_JS = os.path.join(BACKEND_DIR, "server.js")


class TestBackendSyntax(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.node_available = False
        try:
            subprocess.run(["node", "--version"], capture_output=True, check=False, timeout=15)
            cls.node_available = True
        except (FileNotFoundError, OSError):
            cls.node_available = False

    def test_server_js_exists(self):
        self.assertTrue(os.path.isfile(SERVER_JS), f"server.js not found at {SERVER_JS}")

    def test_node_check_backend_server_js_exit_0(self):
        if not self.node_available:
            self.skipTest("node executable not on PATH; cannot run syntax check")
        proc = subprocess.run(
            ["node", "--check", "server.js"],
            cwd=BACKEND_DIR,
            capture_output=True,
            text=True,
            timeout=60,
        )
        combined = (proc.stdout or "") + ("\nSTDERR:\n" + proc.stderr if proc.stderr else "")
        self.assertEqual(proc.returncode, 0,
                         f"node --check server.js non-zero exit {proc.returncode}: {combined}")

    def test_package_json_test_script_honestly_labelled_BLOCKED_for_runtime(self):
        import json
        pj = os.path.join(BACKEND_DIR, "package.json")
        self.assertTrue(os.path.isfile(pj), "backend/package.json missing")
        with open(pj, "r", encoding="utf-8") as f:
            data = json.load(f)
        test_script = data.get("scripts", {}).get("test", "")
        # The test script MUST NOT fake runtime success. It must honestly document that
        # Mongo/FastAPI-backed runtime tests are BLOCKED unless services are live.
        self.assertNotEqual(test_script.strip(), "", "backend package.json test script empty")
        self.assertTrue(
            ("BLOCKED" in test_script) or ("blocked" in test_script.lower()) or ("--check" in test_script),
            f"Backend package.json test script does not honestly label runtime/Mongo BLOCKED "
            f"requirement: {test_script!r}"
        )


if __name__ == "__main__":
    unittest.main()
