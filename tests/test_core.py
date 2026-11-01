"""Tests for goal convergence and explicit command rejection (no ROS needed)."""
import json
import math
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'app'))
from intent import fit, predict
from navigation import GOALS, velocity


class CoreTests(unittest.TestCase):
    def test_reject_unsupported_instructions(self):
        model = fit(json.loads((ROOT/'data/commands.json').read_text())['train'])
        for text in ['こんにちは', '天気を教えて', '管制室には行かないで', '資材庫と研究ラボに行って']:
            self.assertEqual(predict(model, text)['label'], 'unknown', text)

    def test_sequential_goal_convergence(self):
        x, y, yaw = 0.0, 0.0, 0.0
        # Independent kinematic simulation checks steering sign, angle wrapping,
        # arrival tolerance, and travel between goals, but not Gazebo physics.
        for goal in GOALS.values():
            arrived = False
            for _ in range(1800):
                v, w, arrived = velocity(x, y, yaw, goal)
                self.assertLessEqual(abs(v), .35)
                self.assertLessEqual(abs(w), .8)
                if arrived:
                    break
                x += .05*v*math.cos(yaw)
                y += .05*v*math.sin(yaw)
                yaw += .05*w
            self.assertTrue(arrived, goal)
            self.assertLess(math.hypot(x-goal[0], y-goal[1]), .18)


if __name__ == '__main__':
    unittest.main()
