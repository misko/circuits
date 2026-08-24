#!/usr/bin/env python3
"""Focused green/red fixtures for the source-to-prep board authority core."""
from __future__ import annotations

import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))

from board_authority import (  # noqa: E402
    AuthoritySchemaError,
    AuthorityVerificationError,
    LEGACY_AUTHORITY,
    STACK_ROLE_OWNER,
    adapt_legacy_stack,
    canonical_sha256,
    compile_source_prep_authority,
    inspect_legacy_authority,
    normalize_observed_facts,
    normalize_route_plan,
    normalize_stack_contract,
    normalize_topology_migration,
    physical_copper_order,
    physical_via_span,
    reconcile_topology_migration,
    reopen_authority,
    resolve_route_waves,
    resolve_routing_classes,
    verify_authority,
    verify_authority_structure,
    write_authority,
)


def stack2():
    return {
        "schema": "stackup-v1",
        "copper": [
            {"name": "F.Cu", "thickness_um": 35, "role": "signal"},
            {"name": "B.Cu", "thickness_um": 35, "role": "signal"},
        ],
        "routing_classes": {
            "low_speed": {"allowed_layers": ["F.Cu", "B.Cu"]},
        },
    }


def stack4():
    return {
        "schema": "stackup-v1",
        "copper": [
            {"name": "F.Cu", "thickness_um": 35, "role": "signal"},
            {"name": "In1.Cu", "thickness_um": 18,
             "role": "reference_plane", "plane_net": "GND"},
            {"name": "In2.Cu", "thickness_um": 18, "role": "mixed"},
            {"name": "B.Cu", "thickness_um": 35, "role": "signal"},
        ],
        "routing_classes": {
            "signal": {"allowed_layers": ["F.Cu", "In2.Cu", "B.Cu"]},
        },
    }


def stack6():
    return {
        "schema": "stackup-v1",
        "copper": [
            {"name": "F.Cu", "thickness_um": 35, "role": "signal"},
            {"name": "In1.Cu", "thickness_um": 15.2,
             "role": "reference_plane", "plane_net": "GND"},
            {"name": "In2.Cu", "thickness_um": 15.2,
             "role": "power", "plane_net": "PWR"},
            {"name": "In3.Cu", "thickness_um": 15.2, "role": "mixed"},
            {"name": "In4.Cu", "thickness_um": 15.2,
             "role": "reference_plane", "plane_net": "GND"},
            {"name": "B.Cu", "thickness_um": 35, "role": "signal"},
        ],
        "routing_classes": {
            "usb_hs": {
                "allowed_layers": ["B.Cu", "F.Cu"],
                "references": {"F.Cu": "In1.Cu", "B.Cu": "In4.Cu"},
                "reference_required": True,
            },
            "control": {"allowed_layers": ["In3.Cu"]},
        },
        "via_families": {
            "ordinary_through": {
                "from_layer": "F.Cu", "to_layer": "B.Cu", "kind": "through",
            },
            "top_microvia": {
                "from_layer": "F.Cu", "to_layer": "In1.Cu", "kind": "microvia",
            },
        },
    }


def observed2():
    return {
        "schema": "observed-source-facts-v1",
        "refs": ["J1", "U1"],
        "nets": ["GND", "SIG"],
        "mpns": ["CONN", "MCU"],
    }


def route2():
    return {
        "schema": "route-plan-v1",
        "groups": {"signals": ["SIG"]},
        "waves": [
            {"name": "signals", "group": "signals",
             "routing_class": "low_speed"},
        ],
        "exclusions": [
            {"pattern": "GND", "owner": "reference-plane",
             "why": "ordinary ground pour is not a generic route wave"},
        ],
        "deterministic_owners": [],
    }


def observed6():
    return {
        "schema": "observed-source-facts-v1",
        "refs": ["J_USB", "U_CTRL"],
        "nets": ["CTRL", "GND", "PWR", "USB_N", "USB_P"],
        "mpns": ["CONNECTOR", "CONTROLLER"],
    }


def route6():
    return {
        "schema": "route-plan-v1",
        "groups": {"control": ["CTRL"], "usb": ["USB_P", "USB_N"]},
        "waves": [
            {"name": "usb", "group": "usb", "routing_class": "usb_hs"},
            {"name": "control", "group": "control",
             "routing_class": "control"},
        ],
        "exclusions": [
            {"pattern": "GND", "owner": "reference-plane",
             "why": "GND is plane-owned"},
        ],
        "deterministic_owners": [
            {"net": "PWR", "owner": "source-zone",
             "why": "broad power copper is deterministic"},
        ],
    }


def migration():
    return {
        "schema": "topology-migration-v1",
        "id": "replace-old-regulator",
        "why": "replace the package and its external switch node",
        "remove": {
            "refs": ["L_OLD", "U_OLD"],
            "nets": ["OLD_SW"],
            "mpns": ["OLD-MPN"],
        },
        "add": {
            "refs": ["U_NEW"],
            "nets": ["NEW_SW"],
            "mpns": ["NEW-MPN"],
        },
    }


def migrated_observed(*, remnants=False, historical=True):
    result = {
        "schema": "observed-source-facts-v1",
        "refs": ["J1", "U_NEW"],
        "nets": ["GND", "NEW_SW"],
        "mpns": ["NEW-MPN"],
        "occurrences": [],
    }
    if remnants:
        result["refs"].append("U_OLD")
        result["nets"].append("OLD_SW")
        result["mpns"].append("OLD-MPN")
    if historical:
        result["occurrences"].extend([
            {"kind": "ref", "value": "L_OLD",
             "source": "01_docs/decisions/0007.md", "scope": "historical"},
            {"kind": "net", "value": "OLD_SW",
             "source": "01_docs/decisions/0007.md", "scope": "historical"},
            {"kind": "mpn", "value": "OLD-MPN",
             "source": "01_docs/decisions/0007.md", "scope": "historical"},
        ])
    return result


def rehash(authority):
    payload = copy.deepcopy(authority)
    payload["binding"].pop("authority_sha256", None)
    authority["binding"]["authority_sha256"] = canonical_sha256(payload)


class StackContractTest(unittest.TestCase):
    def test_numeric_kicad_ids_never_define_physical_order(self):
        # The incident ordering trap: sorting these IDs gives F, B, In1, In2.
        ids = {"F.Cu": 0, "B.Cu": 2, "In1.Cu": 4, "In2.Cu": 6}
        self.assertEqual(
            physical_copper_order(stack4(), ids),
            ("F.Cu", "In1.Cu", "In2.Cu", "B.Cu"))
        self.assertEqual(
            physical_via_span(stack4(), "B.Cu", "F.Cu"),
            ("F.Cu", "In1.Cu", "In2.Cu", "B.Cu"))
        self.assertEqual(
            physical_via_span(stack4(), "F.Cu", "In2.Cu"),
            ("F.Cu", "In1.Cu", "In2.Cu"))

    def test_two_layer_stack_passes_without_invented_plane_facts(self):
        authority = compile_source_prep_authority(
            stack=stack2(), observed=observed2(), route_plan=route2())
        self.assertEqual(authority["verdict"], "PASS")
        self.assertEqual(authority["ownership"], {
            "physical_stack": STACK_ROLE_OWNER,
            "semantic_layer_roles": STACK_ROLE_OWNER,
            "legacy_adapters": LEGACY_AUTHORITY,
        })
        self.assertEqual(authority["stack"]["physical_order"], ["F.Cu", "B.Cu"])
        self.assertEqual(authority["defaults"]["reference_plane_checks"], [])
        self.assertEqual(authority["defaults"]["stitch"]["reference_nets"], [])
        self.assertNotIn("via_family", authority["defaults"]["stitch"])
        self.assertNotIn("requires_explicit_via_family",
                         authority["defaults"]["stitch"])
        self.assertGreater(authority["coverage"]["copper_layers"], 0)
        self.assertEqual(authority["findings"], [])
        self.assertTrue(verify_authority_structure(authority)[0])

    def test_six_layer_roles_classes_references_and_vias_resolve(self):
        authority = compile_source_prep_authority(
            stack=stack6(), observed=observed6(), route_plan=route6())
        self.assertEqual(authority["verdict"], "PASS")
        self.assertEqual(authority["stack"]["physical_order"],
                         ["F.Cu", "In1.Cu", "In2.Cu", "In3.Cu",
                          "In4.Cu", "B.Cu"])
        usb = authority["stack"]["routing_classes"]["usb_hs"]
        self.assertEqual(usb["allowed_layers"], ["F.Cu", "B.Cu"])
        self.assertEqual(usb["references"]["F.Cu"]["layer"], "In1.Cu")
        self.assertEqual(usb["references"]["B.Cu"]["net"], "GND")
        control = authority["stack"]["routing_classes"]["control"]
        self.assertEqual(control["references"]["In3.Cu"]["layer"], "In4.Cu")
        through = authority["stack"]["via_families"]["ordinary_through"]
        self.assertEqual(through["copper_layer_count"], 6)
        self.assertEqual(through["physical_edge_count"], 5)
        # Only the explicitly declared through family spans both reference
        # planes, so selecting it is a derivation rather than an invented via.
        self.assertEqual(authority["defaults"]["stitch"]["via_family"],
                         "ordinary_through")

    def test_conflicting_layer_roles_fail_semantically(self):
        source = stack6()
        source["copper"][0]["plane_net"] = "GND"
        source["routing_classes"]["bad_plane_route"] = {
            "allowed_layers": ["In1.Cu"]}
        result = resolve_routing_classes(source)
        codes = {row["code"] for row in result["findings"]}
        self.assertIn("S-PLANE-NET-CONFLICT", codes)
        self.assertIn("S-ROLE-CONFLICT", codes)

    def test_ambiguous_adjacent_references_are_not_invented(self):
        source = {
            "schema": "stackup-v1",
            "copper": [
                {"name": "F.Cu", "thickness_um": 35, "role": "signal"},
                {"name": "In1.Cu", "thickness_um": 18,
                 "role": "reference_plane", "plane_net": "GND"},
                {"name": "In2.Cu", "thickness_um": 18, "role": "mixed"},
                {"name": "In3.Cu", "thickness_um": 18,
                 "role": "reference_plane", "plane_net": "GND"},
                {"name": "B.Cu", "thickness_um": 35, "role": "signal"},
            ],
            "routing_classes": {"inner": {"allowed_layers": ["In2.Cu"]}},
        }
        result = resolve_routing_classes(source)
        self.assertEqual(result["findings"], [])
        self.assertEqual(result["classes"]["inner"]["references"], {})
        self.assertEqual(result["classes"]["inner"]["unresolved_references"],
                         ["In2.Cu"])

    def test_usb_hs_explicitly_required_missing_reference_fails(self):
        source = stack2()
        source["routing_classes"] = {"usb_hs": {
            "allowed_layers": ["F.Cu", "B.Cu"],
            "reference_required": True,
        }}
        result = resolve_routing_classes(source)
        required = [row for row in result["findings"]
                    if row["code"] == "S-REFERENCE-REQUIRED"]
        self.assertEqual(
            {row["subject"] for row in required},
            {"usb_hs:F.Cu", "usb_hs:B.Cu"})

        plan = route2()
        plan["waves"][0]["routing_class"] = "usb_hs"
        authority = compile_source_prep_authority(
            stack=source, observed=observed2(), route_plan=plan)
        self.assertEqual(authority["verdict"], "FAIL")

    def test_stack_and_nested_rows_are_closed(self):
        cases = []
        root = stack2()
        root["numeric_order"] = [0, 2]
        cases.append(root)
        copper = stack2()
        copper["copper"][0]["numeric_id"] = 0
        cases.append(copper)
        route_class = stack2()
        route_class["routing_classes"]["low_speed"]["fallback"] = "F.Cu"
        cases.append(route_class)
        via = stack6()
        via["via_families"]["ordinary_through"]["drill_um"] = 200
        cases.append(via)
        for source in cases:
            with self.subTest(source=source):
                with self.assertRaises(AuthoritySchemaError):
                    normalize_stack_contract(source)

    def test_duplicate_layer_with_conflicting_role_is_rejected(self):
        source = stack2()
        source["copper"].insert(
            1, {"name": "F.Cu", "thickness_um": 18,
                "role": "reference_plane", "plane_net": "GND"})
        with self.assertRaisesRegex(AuthoritySchemaError,
                                    "multiple physical positions/roles"):
            normalize_stack_contract(source)

    def test_normalized_dynamic_map_key_collisions_are_rejected(self):
        class_names = stack2()
        class_names["routing_classes"][" low_speed "] = {
            "allowed_layers": ["F.Cu"]}
        reference_names = stack6()
        reference_names["routing_classes"]["usb_hs"]["references"][
            " F.Cu "] = "In1.Cu"
        via_names = stack6()
        via_names["via_families"][" ordinary_through "] = {
            "from_layer": "F.Cu", "to_layer": "B.Cu", "kind": "through"}
        for source in (class_names, reference_names, via_names):
            with self.subTest(source=source):
                with self.assertRaisesRegex(AuthoritySchemaError,
                                            "normalize to duplicate"):
                    normalize_stack_contract(source)

        route = route2()
        route["groups"][" signals "] = ["SIG"]
        with self.assertRaisesRegex(AuthoritySchemaError,
                                    "normalize to duplicate"):
            normalize_route_plan(route)


class MigrationContractTest(unittest.TestCase):
    def test_delta_only_migration_passes_and_ignores_historical_text(self):
        result = reconcile_topology_migration(migration(), migrated_observed())
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["findings"], [])
        self.assertEqual(result["coverage"]["delta_items"], 7)
        self.assertEqual(result["coverage"]["historical_occurrences_excluded"], 3)
        self.assertTrue(all(row["scope"] == "historical"
                            for row in result["historical_occurrences_excluded"]))

    def test_old_ref_net_and_mpn_remnants_fail(self):
        result = reconcile_topology_migration(
            migration(), migrated_observed(remnants=True))
        remnants = {row["subject"] for row in result["findings"]
                    if row["code"] == "M-REMNANT"}
        self.assertEqual(result["status"], "FAIL")
        self.assertEqual(remnants, {"ref:U_OLD", "net:OLD_SW", "mpn:OLD-MPN"})

    def test_missing_added_population_fails_without_requiring_full_inventory(self):
        facts = migrated_observed()
        facts["refs"].remove("U_NEW")
        result = reconcile_topology_migration(migration(), facts)
        self.assertIn("ref:U_NEW", {row["subject"] for row in result["findings"]
                                    if row["code"] == "M-ADDED-MISSING"})
        # J1 is intentionally not in the delta and remains legal.
        self.assertIn("J1", facts["refs"])

    def test_observation_migration_and_route_schemas_are_closed(self):
        bad_observed = migrated_observed()
        bad_observed["historical_text"] = "OLD_SW"
        bad_migration = migration()
        bad_migration["full_inventory"] = {"refs": ["J1"]}
        bad_route = route2()
        bad_route["waves"][0]["layers"] = ["F.Cu"]
        for function, value in (
                (normalize_observed_facts, bad_observed),
                (normalize_topology_migration, bad_migration),
                (normalize_route_plan, bad_route)):
            with self.subTest(function=function.__name__):
                with self.assertRaisesRegex(AuthoritySchemaError, "unknown key"):
                    function(value)


class WaveOwnershipTest(unittest.TestCase):
    def _classes(self):
        return resolve_routing_classes(stack2())["classes"]

    def test_zero_net_wave_and_removed_group_member_fail(self):
        plan = route2()
        plan["groups"] = {"gone": ["REMOVED_NET"]}
        plan["waves"] = [{"name": "gone", "group": "gone",
                          "routing_class": "low_speed"}]
        result = resolve_route_waves(
            plan, live_nets=["GND"], routing_classes=self._classes())
        codes = {row["code"] for row in result["findings"]}
        self.assertIn("W-EMPTY", codes)
        self.assertIn("W-REMOVED", codes)

    def test_two_waves_cannot_own_one_live_net(self):
        plan = route2()
        plan["groups"] = {"a": ["SIG"], "b": ["SIG"]}
        plan["waves"] = [
            {"name": "a", "group": "a", "routing_class": "low_speed"},
            {"name": "b", "group": "b", "routing_class": "low_speed"},
        ]
        result = resolve_route_waves(
            plan, live_nets=["GND", "SIG"], routing_classes=self._classes())
        self.assertIn("SIG", {row["subject"] for row in result["findings"]
                              if row["code"] == "W-MULTIPLE"})

    def test_deterministic_owner_and_wave_cannot_both_own_net(self):
        plan = route2()
        plan["deterministic_owners"] = [
            {"net": "SIG", "owner": "source-stub",
             "why": "authored escape owns the whole net"},
        ]
        result = resolve_route_waves(
            plan, live_nets=["GND", "SIG"], routing_classes=self._classes())
        self.assertIn("SIG", {row["subject"] for row in result["findings"]
                              if row["code"] == "W-MULTIPLE"})

    def test_duplicate_same_label_owners_do_not_collapse(self):
        plan = route2()
        plan["groups"] = {}
        plan["waves"] = []
        plan["deterministic_owners"] = [
            {"net": "SIG", "owner": "source-stub", "why": "first claim"},
            {"net": "SIG", "owner": "source-stub", "why": "second claim"},
        ]
        result = resolve_route_waves(
            plan, live_nets=["GND", "SIG"], routing_classes=self._classes())
        self.assertIn("SIG", {row["subject"] for row in result["findings"]
                              if row["code"] == "W-MULTIPLE"})

    def test_uncovered_live_net_fails(self):
        result = resolve_route_waves(
            route2(), live_nets=["AUX", "GND", "SIG"],
            routing_classes=self._classes())
        self.assertIn("AUX", {row["subject"] for row in result["findings"]
                              if row["code"] == "W-UNCOVERED"})

    def test_removed_net_in_dormant_group_still_fails(self):
        plan = route2()
        plan["groups"]["obsolete"] = ["OLD_SW"]
        result = resolve_route_waves(
            plan, live_nets=["GND", "SIG"], routing_classes=self._classes())
        self.assertIn("OLD_SW", {row["subject"] for row in result["findings"]
                                 if row["code"] == "W-REMOVED"})

    def test_rest_group_is_deterministic_and_complete(self):
        plan = route2()
        plan["groups"] = {"remaining": "rest"}
        plan["waves"] = [{"name": "remaining", "group": "remaining",
                          "routing_class": "low_speed"}]
        result = resolve_route_waves(
            plan, live_nets=["AUX", "GND", "SIG"],
            routing_classes=self._classes())
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["waves"][0]["nets"], ["AUX", "SIG"])


class ReceiptTest(unittest.TestCase):
    def test_receipt_is_deterministic_hash_bound_and_reopenable(self):
        first = compile_source_prep_authority(
            stack=stack2(), observed=observed2(), route_plan=route2())
        shuffled = observed2()
        shuffled["refs"].reverse()
        shuffled["nets"].reverse()
        shuffled["mpns"].reverse()
        second = compile_source_prep_authority(
            stack=stack2(), observed=shuffled, route_plan=route2())
        self.assertEqual(first, second)
        self.assertRegex(first["binding"]["authority_sha256"], r"^[0-9a-f]{64}$")
        self.assertEqual(first["verdict"], "PASS")

        root = Path(tempfile.mkdtemp(prefix="board-authority-"))
        path = write_authority(
            root / "authority.json", first, stack=stack2(),
            observed=observed2(), route_plan=route2(), migration=None)
        reopened = reopen_authority(
            path, stack=stack2(), observed=observed2(), route_plan=route2(),
            migration=None)
        self.assertEqual(reopened, first)

    def test_changed_input_invalidates_reopened_receipt(self):
        authority = compile_source_prep_authority(
            stack=stack2(), observed=observed2(), route_plan=route2())
        root = Path(tempfile.mkdtemp(prefix="board-authority-"))
        path = write_authority(
            root / "authority.json", authority, stack=stack2(),
            observed=observed2(), route_plan=route2(), migration=None)
        changed = observed2()
        changed["nets"].append("NEW_LIVE_NET")
        with self.assertRaisesRegex(AuthorityVerificationError,
                                    "input subject changed"):
            reopen_authority(path, stack=stack2(), observed=changed,
                             route_plan=route2(), migration=None)

    def test_promotion_apis_require_every_exact_input(self):
        authority = compile_source_prep_authority(
            stack=stack2(), observed=observed2(), route_plan=route2())
        root = Path(tempfile.mkdtemp(prefix="board-authority-"))
        with self.assertRaises(TypeError):
            write_authority(root / "authority.json", authority)

    def test_content_tamper_fails_self_hash(self):
        authority = compile_source_prep_authority(
            stack=stack2(), observed=observed2(), route_plan=route2())
        root = Path(tempfile.mkdtemp(prefix="board-authority-"))
        path = write_authority(
            root / "authority.json", authority, stack=stack2(),
            observed=observed2(), route_plan=route2(), migration=None)
        payload = json.loads(path.read_text())
        payload["coverage"]["live_nets"] = 999
        path.write_text(json.dumps(payload))
        with self.assertRaisesRegex(AuthorityVerificationError,
                                    "content hash changed"):
            reopen_authority(
                path, stack=stack2(), observed=observed2(),
                route_plan=route2(), migration=None)

    def test_rehashed_structural_omission_is_still_rejected(self):
        authority = compile_source_prep_authority(
            stack=stack2(), observed=observed2(), route_plan=route2())
        authority.pop("defaults")
        rehash(authority)
        valid, failures = verify_authority_structure(authority)
        self.assertFalse(valid)
        self.assertTrue(any("missing key" in row for row in failures))

    def test_same_hash_but_wrong_semantics_fail_exact_input_recompile(self):
        authority = compile_source_prep_authority(
            stack=stack2(), observed=observed2(), route_plan=route2())
        authority["defaults"]["stitch"]["cleanup_scope"] = "all"
        rehash(authority)
        valid, failures = verify_authority(
            authority, stack=stack2(), observed=observed2(),
            route_plan=route2(), migration=None)
        self.assertFalse(valid)
        self.assertIn("authority does not match recompilation from exact inputs",
                      failures)

    def test_rehashed_legacy_stack_role_ownership_claim_is_rejected(self):
        authority = compile_source_prep_authority(
            stack=stack2(), observed=observed2(), route_plan=route2())
        authority["ownership"]["semantic_layer_roles"] = \
            "legacy-route-adapter"
        rehash(authority)
        valid, failures = verify_authority_structure(authority)
        self.assertFalse(valid)
        self.assertTrue(any("canonical stack/role owner" in row
                            for row in failures))

    def test_pre_ownership_receipt_is_diagnostic_only(self):
        authority = compile_source_prep_authority(
            stack=stack2(), observed=observed2(), route_plan=route2())
        authority.pop("ownership")
        rehash(authority)
        self.assertFalse(verify_authority_structure(authority)[0])
        diagnostic = inspect_legacy_authority(authority)
        self.assertIs(diagnostic["authoritative"], False)
        self.assertEqual(diagnostic["authority_class"], LEGACY_AUTHORITY)
        self.assertIsNone(diagnostic["execution_authority"])
        self.assertTrue(diagnostic["self_hash_valid"])

    def test_failed_receipt_still_has_findings_verdict_and_nonzero_coverage(self):
        plan = route2()
        plan["groups"] = {"missing": ["OLD_NET"]}
        plan["waves"] = [{"name": "missing", "group": "missing",
                          "routing_class": "low_speed"}]
        authority = compile_source_prep_authority(
            stack=stack2(), observed=observed2(), route_plan=plan)
        self.assertEqual(authority["verdict"], "FAIL")
        self.assertGreater(len(authority["findings"]), 0)
        self.assertGreater(authority["coverage"]["copper_layers"], 0)
        self.assertTrue(verify_authority_structure(authority)[0])


class CompatibilityTest(unittest.TestCase):
    def test_legacy_adapter_is_visible_but_has_no_execution_authority(self):
        floorplan = {
            "board": {"layers": 2, "stackup": {
                "copper_thickness_mm": [0.035, 0.035]}}}
        legacy_route = {"route": {"routability": {
            "layer_roles": {"F.Cu": "signal", "B.Cu": "signal"},
            "class_layers": {"low_speed": ["F.Cu", "B.Cu"]},
        }}}
        result = adapt_legacy_stack(floorplan, legacy_route, {})
        self.assertEqual(result["schema"], "legacy-stack-adapter-v1")
        self.assertIs(result["authoritative"], False)
        self.assertEqual(result["authority_class"], LEGACY_AUTHORITY)
        self.assertIsNone(result["execution_authority"])
        self.assertEqual(result["candidate"]["schema"], "stackup-v1")
        # Passing the adapter wrapper cannot silently select its candidate.
        with self.assertRaisesRegex(AuthoritySchemaError,
                                    "legacy adapters are not authority"):
            compile_source_prep_authority(
                stack=result, observed=observed2(), route_plan=route2())

    def test_legacy_plane_net_conflict_cannot_reappear_on_third_observation(self):
        floorplan = {"board": {"layers": 4, "stackup": {
            "copper_thickness_mm": [0.035, 0.018, 0.018, 0.035]}}}
        legacy_route = {"route": {"routability": {"layer_roles": {
            "F.Cu": "signal", "In1.Cu": "reference_plane",
            "In2.Cu": "mixed", "B.Cu": "signal"}}}}
        legacy_nets = {"reference_plane_checks": {
            "first": {"reference_layer": "In1.Cu", "reference_net": "GND"},
            "conflict": {"reference_layer": "In1.Cu", "reference_net": "PWR"},
            "third": {"reference_layer": "In1.Cu", "reference_net": "GND"},
        }}
        result = adapt_legacy_stack(floorplan, legacy_route, legacy_nets)
        in1 = next(row for row in result["candidate"]["copper"]
                   if row["name"] == "In1.Cu")
        self.assertNotIn("plane_net", in1)
        self.assertTrue(any("conflicting legacy plane nets" in note
                            for note in result["notes"]))


if __name__ == "__main__":
    unittest.main()
