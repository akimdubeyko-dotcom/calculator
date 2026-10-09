"""Behavioral checks for the display-independent game simulation."""

import math
import unittest

from model import FANS, ITEMS, REPLIES, TARGET, GameState, Projectile


class ProjectileTests(unittest.TestCase):
    def test_flight_starts_and_ends_at_given_points_and_arcs_upward(self):
        projectile = Projectile((100, 400), (600, 500), kind=0)
        self.assertEqual(projectile.position, projectile.start)

        projectile.age = projectile.duration / 2
        x, y = projectile.position
        self.assertAlmostEqual(x, 350)
        self.assertLess(y, 400)

        projectile.age = projectile.duration
        self.assertEqual(projectile.position, projectile.end)
        projectile.age += 10
        self.assertEqual(projectile.position, projectile.end)


class GameStateTests(unittest.TestCase):
    def setUp(self):
        self.state = GameState(seed=42)

    def test_throws_rotate_through_fans_and_use_selected_item(self):
        starts = set()
        for index in range(len(FANS) + 1):
            with self.subTest(throw=index):
                kind = index % len(ITEMS)
                self.state.select(kind)
                self.assertTrue(self.state.throw())
                projectile = self.state.projectiles[-1]
                fan_index = index % len(FANS)
                fan_x, fan_y = FANS[fan_index]

                self.assertEqual(self.state.speaker, fan_index)
                self.assertEqual(projectile.kind, kind)
                self.assertLess(abs(projectile.start[0] - fan_x), 50)
                self.assertLess(projectile.start[1], fan_y)
                self.assertLess(abs(projectile.end[0] - TARGET[0]), 20)
                self.assertLess(abs(projectile.end[1] - TARGET[1]), 20)
                self.assertGreater(self.state.poses[fan_index], 0)
                self.assertTrue(self.state.bubble)
                starts.add(projectile.start)
                self.state.update(self.state.cooldown_seconds)

        self.assertEqual(len(starts), len(FANS))
        self.assertEqual(self.state.throws, len(FANS) + 1)

    def test_cooldown_rejects_rapid_presses_without_creating_extra_throws(self):
        self.assertTrue(self.state.throw())
        self.assertFalse(self.state.throw())
        self.state.update(self.state.cooldown_seconds / 2)
        self.assertFalse(self.state.throw())
        self.assertEqual(self.state.throws, 1)
        self.assertEqual(len(self.state.projectiles), 1)

        self.state.update(self.state.cooldown_seconds / 2)
        self.assertTrue(self.state.throw())
        self.assertEqual(self.state.throws, 2)

    def test_impact_occurs_once_and_creates_reaction_reply_and_particles(self):
        self.state.select(2)
        self.state.throw()
        duration = self.state.projectiles[0].duration

        self.assertEqual(self.state.update(duration / 2), 0)
        self.assertEqual(self.state.hits, 0)
        self.assertEqual(self.state.update(duration / 2), 1)
        self.assertEqual(self.state.hits, 1)
        self.assertEqual(self.state.last_kind, 2)
        self.assertFalse(self.state.projectiles)
        self.assertGreater(self.state.reaction, 0)
        self.assertIn(self.state.reply, REPLIES)
        self.assertGreater(self.state.reply_time, 0)
        self.assertTrue(self.state.particles)
        self.assertTrue(all(particle.life > 0 for particle in self.state.particles))

        self.assertEqual(self.state.update(0.1), 0)
        self.assertEqual(self.state.update(5), 0)
        self.assertEqual(self.state.hits, 1)

    def test_particles_and_visible_replies_expire(self):
        self.state.throw()
        self.state.update(self.state.projectiles[0].duration)
        self.assertTrue(self.state.particles)
        self.assertGreater(self.state.bubble_time, 0)
        self.assertGreater(self.state.reply_time, 0)

        self.state.update(5)

        self.assertFalse(self.state.particles)
        self.assertEqual(self.state.bubble_time, 0)
        self.assertEqual(self.state.reply_time, 0)
        self.assertEqual(self.state.reaction, 0)
        self.assertTrue(all(pose == 0 for pose in self.state.poses))

    def test_reset_clears_objects_counters_and_temporary_effects(self):
        self.state.select(2)
        self.state.throw()
        self.state.update(self.state.projectiles[0].duration)
        self.state.throw()
        self.assertTrue(self.state.projectiles)
        self.assertTrue(self.state.particles)
        self.assertGreater(self.state.hits, 0)

        self.state.reset()

        self.assertEqual(self.state.throws, 0)
        self.assertEqual(self.state.hits, 0)
        self.assertEqual(self.state.time, 0)
        self.assertEqual(self.state.selected, 0)
        self.assertFalse(self.state.projectiles)
        self.assertFalse(self.state.particles)
        self.assertEqual(self.state.cooldown, 0)
        self.assertEqual(self.state.reaction, 0)
        self.assertEqual(self.state.bubble, "")
        self.assertEqual(self.state.reply, "")
        self.assertEqual(self.state.bubble_time, 0)
        self.assertEqual(self.state.reply_time, 0)
        self.assertTrue(all(pose == 0 for pose in self.state.poses))
        self.assertTrue(self.state.throw())

    def test_invalid_elapsed_time_is_rejected_without_advancing_state(self):
        self.state.throw()
        for dt in (-1, math.inf, -math.inf, math.nan):
            with self.subTest(dt=dt):
                with self.assertRaises(ValueError):
                    self.state.update(dt)
                self.assertEqual(self.state.time, 0)
                self.assertEqual(self.state.projectiles[0].age, 0)
                self.assertEqual(self.state.hits, 0)

    def test_zero_elapsed_time_does_not_move_projectiles(self):
        self.state.throw()
        projectile = self.state.projectiles[0]
        before = projectile.position

        self.assertEqual(self.state.update(0), 0)
        self.assertEqual(projectile.position, before)
        self.assertEqual(self.state.time, 0)


if __name__ == "__main__":
    unittest.main()
