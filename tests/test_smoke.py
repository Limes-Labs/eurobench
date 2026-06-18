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

    def test_v03_hard_mode_shards_have_expected_shape(self):
        shards = sorted((ROOT / "tasks/v0.3").glob("*.json"))
        self.assertGreaterEqual(len(shards), 1)

        categories = {}
        languages = set()
        total = 0
        for shard in shards:
            suite = json.loads(shard.read_text(encoding="utf-8"))
            self.assertEqual(suite["version"], "0.3.0")
            self.assertEqual(suite["suite_id"], "eurobench-v0.3")
            self.assertIn("hard_mode_strategy", suite)
            for task in suite["tasks"]:
                total += 1
                categories[task["category"]] = categories.get(task["category"], 0) + 1
                languages.add(task["language"])
                self.assertTrue(task.get("synthetic", False))
                self.assertIn("hard_mode", task)
                self.assertIn("difficulty_tags", task)
                self.assertIn("expected_output", task)
                self.assertIn("failure_modes", task)
                self.assertIn("source_ids", task["expected_output"])
                self.assertIn("evidence_sources", task)
                self.assertGreaterEqual(len(task["evidence_sources"]), 2)

        self.assertEqual(total, 30)
        self.assertTrue(
            {
                "institutional_qa_cited",
                "cross_lingual_form_filling",
                "glossary_translation",
                "procurement_procedure_reasoning",
                "ai_act_gdpr_boundary_caution",
                "democratic_integrity_moderation",
                "long_context_evidence_selection",
            }.issubset(categories)
        )
        self.assertTrue({"es", "pl", "nl", "sv", "ro", "el", "pt", "ca-ES"}.issubset(languages))

    def test_validate_v03_tasks(self):
        completed = subprocess.run(
            [
                sys.executable,
                "scripts/validate_tasks.py",
                "--tasks",
                "tasks/v0.3",
                "--min-count",
                "30",
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=True,
        )
        self.assertIn("Validated 30 EuroBench tasks", completed.stdout)
        self.assertIn("hard-mode signals", completed.stdout)

    def test_task_schema_includes_v04_scoring_contract(self):
        schema = json.loads((ROOT / "tasks/schema/eurobench_task.schema.json").read_text(encoding="utf-8"))
        self.assertIn("0.4.0", schema["properties"]["version"]["enum"])
        self.assertIn("eurobench-v0.4", schema["properties"]["suite_id"]["enum"])

        task_properties = schema["$defs"]["task"]["properties"]
        self.assertIn(
            "safe_cybersecurity_assessment",
            task_properties["category"]["enum"],
        )
        self.assertIn("tool_use_planning", task_properties["task_type"]["enum"])
        self.assertIn("scoring", task_properties)
        self.assertIn(
            "distractor_sources",
            task_properties["expected_output"]["properties"],
        )

    def test_v03_dummy_run_and_hard_mode_summary(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir) / "run.jsonl"
            subprocess.run(
                [
                    sys.executable,
                    "scripts/run_eval.py",
                    "--tasks",
                    "tasks/v0.3",
                    "--backend",
                    "dummy",
                    "--output",
                    str(output_path),
                    "--run-id",
                    "test-run-v03",
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
            self.assertEqual(len(rows), 30)
            self.assertEqual({row["run_id"] for row in rows}, {"test-run-v03"})
            self.assertTrue(all(row["suite_id"] == "eurobench-v0.3" for row in rows))
            self.assertTrue(all("failure_modes" in row for row in rows))

            completed = subprocess.run(
                [sys.executable, "scripts/summarize_results.py", str(output_path)],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=True,
            )
            self.assertIn("Hard-mode failure modes:", completed.stdout)
            self.assertIn("unsupported_legal_certainty", completed.stdout)

    def test_v03_generator_is_deterministic(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            first = Path(tmp_dir) / "first.json"
            second = Path(tmp_dir) / "second.json"
            command = [
                sys.executable,
                "scripts/generate_v03_tasks.py",
                "--seed",
                "public-v0.3",
            ]
            subprocess.run(command + ["--output", str(first)], cwd=ROOT, check=True)
            subprocess.run(command + ["--output", str(second)], cwd=ROOT, check=True)

            self.assertEqual(
                json.loads(first.read_text(encoding="utf-8")),
                json.loads(second.read_text(encoding="utf-8")),
            )
            self.assertEqual(
                json.loads(first.read_text(encoding="utf-8")),
                json.loads((ROOT / "tasks/v0.3/hard_public.json").read_text(encoding="utf-8")),
            )

    def test_v04_public_shard_has_harder_categories_and_scoring(self):
        shards = sorted((ROOT / "tasks/v0.4").glob("*.json"))
        self.assertGreaterEqual(len(shards), 1)

        categories = {}
        total = 0
        for shard in shards:
            suite = json.loads(shard.read_text(encoding="utf-8"))
            self.assertEqual(suite["version"], "0.4.0")
            self.assertEqual(suite["suite_id"], "eurobench-v0.4")
            self.assertIn("result_card_template", suite)
            self.assertIn("contamination_controls", suite["hard_mode_strategy"])
            for task in suite["tasks"]:
                total += 1
                categories[task["category"]] = categories.get(task["category"], 0) + 1
                self.assertIn("scoring", task)
                self.assertGreaterEqual(task["scoring"]["max_points"], 5)
                self.assertGreaterEqual(len(task["scoring"]["dimensions"]), 3)
                self.assertIn("critical_failures", task["scoring"])
                self.assertIn("anti_saturation", task["hard_mode"])
                self.assertIn("distractor_sources", task["expected_output"])

        self.assertEqual(total, 12)
        self.assertTrue(
            {
                "european_law_admin_boundary",
                "multilingual_cross_lingual_reasoning",
                "long_context_contradiction_handling",
                "safe_cybersecurity_assessment",
                "math_physics_reasoning",
                "agentic_tool_use_planning",
            }.issubset(categories)
        )

    def test_validate_v04_tasks(self):
        completed = subprocess.run(
            [
                sys.executable,
                "scripts/validate_tasks.py",
                "--tasks",
                "tasks/v0.4",
                "--min-count",
                "12",
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=True,
        )
        self.assertIn("Validated 12 EuroBench tasks", completed.stdout)
        self.assertIn("v0.4 scoring signals", completed.stdout)

    def test_v04_dummy_run_summary_and_result_card(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir) / "run.jsonl"
            card_path = Path(tmp_dir) / "result_card.md"
            subprocess.run(
                [
                    sys.executable,
                    "scripts/run_eval.py",
                    "--tasks",
                    "tasks/v0.4",
                    "--backend",
                    "dummy",
                    "--output",
                    str(output_path),
                    "--run-id",
                    "test-run-v04",
                    "--model-id",
                    "dummy-v04",
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
            self.assertEqual(len(rows), 12)
            self.assertTrue(all(row["suite_id"] == "eurobench-v0.4" for row in rows))
            self.assertTrue(all(row["scoring"]["max_points"] >= 5 for row in rows))

            summary = subprocess.run(
                [sys.executable, "scripts/summarize_results.py", str(output_path)],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=True,
            )
            self.assertIn("Scoring dimensions:", summary.stdout)

            card = subprocess.run(
                [
                    sys.executable,
                    "scripts/generate_result_card.py",
                    str(output_path),
                    "--output",
                    str(card_path),
                    "--status",
                    "fixture",
                    "--contamination-assumption",
                    "Public v0.4 tasks are visible and may be contaminated.",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=True,
            )
            self.assertIn("Wrote result card", card.stdout)
            card_text = card_path.read_text(encoding="utf-8")
            self.assertIn("# EuroBench result card", card_text)
            self.assertIn("Status: fixture", card_text)
            self.assertIn("Contamination assumptions", card_text)

    def test_v04_generator_is_deterministic(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            first = Path(tmp_dir) / "first.json"
            second = Path(tmp_dir) / "second.json"
            command = [
                sys.executable,
                "scripts/generate_v04_tasks.py",
                "--seed",
                "public-v0.4",
            ]
            subprocess.run(command + ["--output", str(first)], cwd=ROOT, check=True)
            subprocess.run(command + ["--output", str(second)], cwd=ROOT, check=True)

            self.assertEqual(
                json.loads(first.read_text(encoding="utf-8")),
                json.loads(second.read_text(encoding="utf-8")),
            )
            self.assertEqual(
                json.loads(first.read_text(encoding="utf-8")),
                json.loads((ROOT / "tasks/v0.4/hard_public.json").read_text(encoding="utf-8")),
            )


if __name__ == "__main__":
    unittest.main()
