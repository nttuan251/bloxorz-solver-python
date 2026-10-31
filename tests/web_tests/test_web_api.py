import unittest

from web import api


class LevelTests(unittest.TestCase):
    def test_lists_every_level_in_order(self):
        levels = api.list_levels()
        self.assertGreater(len(levels), 0)
        numbers = [lv["number"] for lv in levels]
        self.assertEqual(numbers, sorted(numbers))

    def test_rejects_ids_outside_the_maps_folder(self):
        for bad in ["../README", "level_01/../../x", "nope"]:
            with self.assertRaises(api.ApiError):
                api.level_payload(bad)

    def test_payload_starts_standing_on_start_tile(self):
        payload = api.level_payload("level_01")
        self.assertEqual(payload["state"]["a"], payload["start"])
        self.assertEqual(payload["state"]["b"], payload["start"])
        self.assertFalse(payload["state"]["split"])


class StepTests(unittest.TestCase):
    def test_state_round_trips_through_json(self):
        state = api.level_payload("level_10")["state"]
        self.assertEqual(api.state_to_json(api.state_from_json(state)), state)

    def test_rolling_off_the_board_is_reported_as_a_fall(self):
        start = api.level_payload("level_01")["state"]
        result = api.step("level_01", start, "UP")
        self.assertFalse(result["ok"])
        self.assertEqual(result["reason"], "fall")

    def test_switch_control_needs_a_split_block(self):
        start = api.level_payload("level_01")["state"]
        with self.assertRaises(api.ApiError):
            api.step("level_01", start, "SWITCH_CONTROL")

    def test_state_from_another_level_is_rejected(self):
        # any two levels with different bridges will do; the map order can change
        payloads = [api.level_payload(lv["id"]) for lv in api.list_levels()]
        plain = next(p for p in payloads if not p["state"]["bridges"])
        bridged = next(p for p in payloads if p["state"]["bridges"])
        with self.assertRaises(api.ApiError):
            api.step(plain["id"], bridged["state"], "DOWN")

    def test_unknown_action_is_rejected(self):
        start = api.level_payload("level_01")["state"]
        with self.assertRaises(api.ApiError):
            api.step("level_01", start, "JUMP")


class SolveTests(unittest.TestCase):
    def test_every_solver_reaches_the_goal_on_a_split_level(self):
        for solver in ["BFS", "DFS", "UCS", "A*"]:
            with self.subTest(solver=solver):
                result = api.solve("level_08", solver, "UNIFORM", "TELEPORT_AWARE")
                self.assertTrue(result["found"])
                self.assertEqual(len(result["states"]), len(result["actions"]) + 1)
                final = result["states"][-1]
                self.assertEqual(final["a"], final["b"])
                self.assertEqual(final["a"], api.level_payload("level_08")["goal"])

    def test_solution_replays_move_by_move_through_step(self):
        result = api.solve("level_10", "BFS")
        state = result["states"][0]
        for action, expected in zip(result["actions"], result["states"][1:]):
            step = api.step("level_10", state, action)
            self.assertTrue(step["ok"], action)
            self.assertEqual(step["state"], expected)
            state = step["state"]
        self.assertTrue(step["won"])

    def test_bfs_and_ucs_uniform_agree_on_length(self):
        bfs = api.solve("level_08", "BFS")
        ucs = api.solve("level_08", "UCS", "UNIFORM")
        self.assertEqual(bfs["metrics"]["steps"], ucs["metrics"]["steps"])

    def test_explored_heat_covers_the_start_tile(self):
        result = api.solve("level_01", "BFS")
        start = api.level_payload("level_01")["start"]
        cells = {(r, c) for r, c, _ in result["explored"]}
        self.assertIn(tuple(start), cells)

    def test_unknown_solver_is_rejected(self):
        with self.assertRaises(api.ApiError):
            api.solve("level_01", "GREEDY")


if __name__ == "__main__":
    unittest.main()
