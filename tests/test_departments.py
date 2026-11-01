"""Unit tests for the construction-company department math.

Covers the pure, runnable Python: materials takeoff, labour, scheduling
(topo sort + CPM + calendar), procurement consolidation, and the project
orchestrator. Run from the repo root:

    python3 -m unittest discover tests

Not covered here (documented in tests/README.md):
- site_anchors.py convex_hull / layout_line: import bpy (Blender), so they
  can't be imported outside Blender. Verified by hand in the math audit.
- Unity C# Fraction / FtIn: run via Unity's Test Runner, not Python.
"""

import math
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _dep in ("materials", "labour", "scheduling", "safety", "procurement"):
    sys.path.insert(0, os.path.join(ROOT, _dep))
sys.path.insert(0, ROOT)

import takeoff as mat
import labour_takeoff as lab
import schedule as sch
import purchase_order as pro
import project as orch


class TestMaterialsTakeoff(unittest.TestCase):
    def test_interior_wall_quantities(self):
        label, kind, waste, rows, total = mat.takeoff("interior_wall_2x4_16oc", 24)
        self.assertEqual(kind, "linear")
        self.assertIsNone(total)  # no prices -> no cost
        d = {name: (qty, unit) for name, qty, unit, _ in rows}
        # studs: (0.75*24 + 1) * 1.10 = 20.9 -> ceil 21, counted whole
        self.assertEqual(d["2x4 stud (precut 92 5/8\")"][0], 21)
        self.assertEqual(d["2x4 stud (precut 92 5/8\")"][1], "ea")
        # plates: 3 runs * 24 ft * 1.10 waste = 79.2 lin ft (not rounded)
        self.assertAlmostEqual(d["2x4 plate (bottom + double top)"][0], 79.2, places=4)

    def test_unknown_assembly_raises(self):
        with self.assertRaises(KeyError):
            mat.takeoff("no_such_assembly", 10)

    def test_area_assembly(self):
        label, kind, waste, rows, total = mat.takeoff("floor_system_ijoist_16oc", 1000)
        self.assertEqual(kind, "area")
        self.assertTrue(any("subfloor" in name.lower() for name, *_ in rows))


class TestLabour(unittest.TestCase):
    def test_hours_positive_and_roles_sum(self):
        r = lab.takeoff("exterior_wall_2x6_16oc", 40)
        self.assertGreater(r["total_lh"], 0)
        self.assertEqual(r["kind"], "linear")
        # role-hours should sum to the total labour-hours
        self.assertAlmostEqual(sum(r["role_lh"].values()), r["total_lh"], places=4)
        # elapsed = total_lh / crew_size
        self.assertAlmostEqual(r["elapsed_hr"], r["total_lh"] / r["crew_size"], places=4)

    def test_factor_scales_linearly(self):
        base = lab.takeoff("interior_wall_2x4_16oc", 20, factor=1.0)
        scaled = lab.takeoff("interior_wall_2x4_16oc", 20, factor=1.5)
        self.assertAlmostEqual(scaled["total_lh"], base["total_lh"] * 1.5, places=4)


class TestScheduling(unittest.TestCase):
    def test_duration_models(self):
        self.assertEqual(sch.duration_days({"type": "fixed", "days": 15}), 15)
        # ceil(350 / (1*150)) = ceil(2.33) = 3
        self.assertEqual(sch.duration_days(
            {"type": "derived", "quantity": 350, "crew": 1, "productivity": 150}), 3)
        # at least 1 day even for tiny quantities
        self.assertEqual(sch.duration_days(
            {"type": "derived", "quantity": 1, "crew": 5, "productivity": 100}), 1)

    def test_cpm_diamond(self):
        # A(2) -> B(5), A -> C(3), B&C -> D(2). Critical path A->B->D, total 9.
        tasks = [
            {"id": "A", "predecessors": [], "duration_model": {"type": "fixed", "days": 2}},
            {"id": "B", "predecessors": ["A"], "duration_model": {"type": "fixed", "days": 5}},
            {"id": "C", "predecessors": ["A"], "duration_model": {"type": "fixed", "days": 3}},
            {"id": "D", "predecessors": ["B", "C"], "duration_model": {"type": "fixed", "days": 2}},
        ]
        order, info, finish = sch.cpm(tasks)
        self.assertEqual(finish, 9)
        self.assertTrue(info["A"]["critical"])
        self.assertTrue(info["B"]["critical"])
        self.assertTrue(info["D"]["critical"])
        self.assertFalse(info["C"]["critical"])   # C has slack (3 < 5)
        self.assertEqual(info["C"]["slack"], 2)
        # topo order: A before B, C before D
        self.assertLess(order.index("A"), order.index("B"))
        self.assertLess(order.index("C"), order.index("D"))

    def test_cycle_detected(self):
        tasks = [
            {"id": "a", "predecessors": ["c"], "duration_model": {"type": "fixed", "days": 1}},
            {"id": "b", "predecessors": ["a"], "duration_model": {"type": "fixed", "days": 1}},
            {"id": "c", "predecessors": ["b"], "duration_model": {"type": "fixed", "days": 1}},
        ]
        with self.assertRaises(sch.CycleError):
            sch.topo_sort(tasks)

    def test_unknown_predecessor(self):
        tasks = [{"id": "a", "predecessors": ["ghost"],
                  "duration_model": {"type": "fixed", "days": 1}}]
        with self.assertRaises(sch.CycleError):
            sch.topo_sort(tasks)

    def test_calendar_skips_weekends(self):
        import datetime
        friday = datetime.date(2026, 4, 3)  # a Friday
        # +1 working day from Friday lands on Monday, not Saturday
        self.assertEqual(sch.add_working_days(friday, 1), datetime.date(2026, 4, 6))


class TestProcurement(unittest.TestCase):
    def test_consolidation_sums_across_assemblies(self):
        items = [
            {"assembly": "interior_wall_2x4_16oc", "length_ft": 24},
            {"assembly": "interior_wall_2x4_16oc", "length_ft": 20},
        ]
        lines, subtotal = pro.build_po(items, prices=None)
        self.assertIsNone(subtotal)  # no prices
        studs = [l for l in lines if l["name"].startswith("2x4 stud")][0]
        # 24ft -> 21 studs, 20ft -> ceil((0.75*20+1)*1.10)=ceil(17.6)=18; total 39
        self.assertEqual(studs["qty"], 39)


class TestOrchestrator(unittest.TestCase):
    def test_full_package_no_warnings(self):
        intake = {
            "project": "Test", "start_date": "2026-04-06",
            "assemblies": [
                {"assembly": "exterior_wall_2x6_16oc", "length_ft": 40},
                {"assembly": "floor_system_ijoist_16oc", "area_sqft": 800},
            ],
        }
        pkg = orch.build_package(intake)
        self.assertEqual(pkg["warnings"], [])
        for dept in ("estimating", "procurement", "labour", "scheduling", "safety"):
            self.assertIn(dept, pkg["departments"])
            self.assertNotIn("error", pkg["departments"][dept])
        self.assertGreater(pkg["departments"]["scheduling"]["project_working_days"], 0)

    def test_bad_assembly_becomes_warning_not_crash(self):
        intake = {"project": "Test", "assemblies": [{"assembly": "nope", "length_ft": 10}]}
        pkg = orch.build_package(intake)  # must not raise
        self.assertTrue(pkg["warnings"])

    def test_schedule_is_scope_driven(self):
        # framing_walls duration must grow with the actual wall length (labour -> schedule)
        def framing_days(ft):
            pkg = orch.build_package(
                {"project": "x", "assemblies": [{"assembly": "exterior_wall_2x6_16oc", "length_ft": ft}]})
            sc = pkg["departments"]["scheduling"]
            self.assertIn("framing_walls", sc["scope_derived_tasks"])
            return [r["duration"] for r in sc["tasks"] if r["id"] == "framing_walls"][0]
        self.assertLess(framing_days(40), framing_days(2000))

    def test_totals_combine_materials_and_labour(self):
        import json
        import tempfile
        prices = {"unit_prices": {}}
        with open(os.path.join(ROOT, "materials", "prices.example.json")) as fh:
            mat_prices = json.load(fh)
        for k, v in mat_prices["unit_prices"].items():
            prices["unit_prices"][k] = {"price": 1.0}
        with open(os.path.join(ROOT, "labour", "wages.example.json")) as fh:
            wages = json.load(fh)
        hw = wages.get("hourly_wages") or {}
        for r in hw.values():
            if isinstance(r, dict):
                r["wage"] = 50.0
        with tempfile.TemporaryDirectory() as d:
            pf = os.path.join(d, "prices.json")
            wf = os.path.join(d, "wages.json")
            with open(pf, "w") as fh:
                json.dump(prices, fh)
            with open(wf, "w") as fh:
                json.dump(wages, fh)
            pkg = orch.build_package({
                "project": "x", "prices_file": pf, "wages_file": wf,
                "assemblies": [{"assembly": "exterior_wall_2x6_16oc", "length_ft": 40}]})
        t = pkg["totals"]
        self.assertIsNotNone(t["materials_incl_hst"])
        self.assertIsNotNone(t["labour_base_cost"])
        self.assertAlmostEqual(
            t["project_cost_estimate"], t["materials_incl_hst"] + t["labour_base_cost"], places=2)


if __name__ == "__main__":
    unittest.main()
