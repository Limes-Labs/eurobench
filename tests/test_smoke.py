import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class EuroBenchSmokeTests(unittest.TestCase):
    def test_v02_shards_have_expected_shape(self):
        shards = sorted((ROOT / "tasks/v0.2").glob("*.json"))
        self.assertEqual(len(shards), 4)

        categories = {}
        total = 0
        for shard in shards:
            suite = json.loads(shard.read_text(encoding="utf-8"))
            self.assertEqual(suite["version"], "0.2.0")
            self.assertEqual(suite["suite_id"], "eurobench-v0.2")
            self.assertIn("shard_id", suite)
            for task in suite["tasks"]:
                total += 1
                categories[task["category"]] = categories.get(task["category"], 0) + 1
                self.assertIn("rubric", task)
                self.assertIn("source", task)

        self.assertEqual(total, 25)
        self.assertEqual(categories["italian_institutional_qa"], 4)
        self.assertEqual(categories["french_institutional_qa"], 6)
        self.assertEqual(categories["german_institutional_qa"], 6)
        self.assertEqual(categories["translation_fidelity"], 3)
        self.assertEqual(categories["constitutional_refusal"], 6)

    def test_validate_tasks(self):
        completed = subprocess.run(
            [
                sys.executable,
                "scripts/validate_tasks.py",
                "--tasks",
                "tasks/v0.2"
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=True,
        )
        self.assertIn("Validated 25 EuroBench tasks", completed.stdout)

    def test_dummy_run_and_summary(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir) / "run.jsonl"
            subprocess.run(
                [
                    sys.executable,
                    "scripts/run_eval.py",
                    "--tasks",
                    "tasks/v0.2",
                    "--backend",
                    "dummy",
                    "--output",
                    str(output_path),
                    "--run-id",
                    "test-run",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=True,
            )

            rows = [
                json.loads(line)
                for line in output_path.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            self.assertEqual(len(rows), 25)
            self.assertEqual({row["run_id"] for row in rows}, {"test-run"})

            completed = subprocess.run(
                [sys.executable, "scripts/summarize_results.py", str(output_path)],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=True,
            )
            self.assertIn("Rows: 25", completed.stdout)
            self.assertIn("not a leaderboard", completed.stdout)

    def test_jsonl_backend_writes_results(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir) / "run.jsonl"
            subprocess.run(
                [
                    sys.executable,
                    "scripts/run_eval.py",
                    "--tasks",
                    "tasks/v0.2",
                    "--backend",
                    "jsonl",
                    "--outputs",
                    "examples/model_outputs/example_outputs.jsonl",
                    "--output",
                    str(output_path),
                    "--run-id",
                    "test-run",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=True,
            )

            rows = [
                json.loads(line)
                for line in output_path.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            self.assertEqual(len(rows), 25)
            self.assertEqual({row["run_id"] for row in rows}, {"test-run"})
            self.assertTrue(all("auto_checks" in row for row in rows))


if __name__ == "__main__":
    unittest.main()
