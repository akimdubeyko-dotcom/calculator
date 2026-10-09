"""Team selection and resized mouse interaction checks."""
import os
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
import unittest
import pygame
from model import CLUBS, GameState
from game import Game, TEAM_BUTTON, TEAM_CHOICES, WIDTH, HEIGHT


class TeamTests(unittest.TestCase):
    def test_defaults_and_reset_preserve_selected_sides(self):
        state = GameState()
        self.assertEqual((CLUBS[state.throwers].name, CLUBS[state.target].name),
                         ('Барселона', 'Реал Мадрид'))
        state.choose_club('target', 4)
        state.throw()
        state.reset()
        self.assertEqual((state.throwers, state.target), (0, 4))
        self.assertEqual(state.throws, 0)

    def test_selecting_opponent_swaps_and_clears_inflight_round(self):
        state = GameState()
        state.throw()
        self.assertTrue(state.choose_club('target', 0))
        self.assertEqual((state.throwers, state.target), (1, 0))
        self.assertFalse(state.projectiles)
        self.assertEqual(state.throws, 0)
        self.assertFalse(state.choose_club('target', 0))
        self.assertFalse(state.choose_club('target', 99))
        self.assertFalse(state.choose_club('unknown', 2))

    def test_all_clubs_can_be_selected_for_either_side(self):
        state = GameState()
        for role in ('throwers', 'target'):
            for i in range(len(CLUBS)):
                state.choose_club(role, i)
                self.assertEqual(getattr(state, role), i)
                self.assertNotEqual(state.throwers, state.target)
                self.assertTrue(state.throw())
                self.assertNotIn('{', state.bubble)
                state.update(1)

    def test_menu_clicks_after_resize_pause_and_return_to_game(self):
        game = Game(seed=42)
        try:
            game.handle_event(pygame.event.Event(pygame.VIDEORESIZE, w=900, h=680))
            def click(rect):
                size, offset = game.viewport()
                pos = (offset[0]+rect.centerx*size[0]/WIDTH,
                       offset[1]+rect.centery*size[1]/HEIGHT)
                game.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=pos))
            click(TEAM_BUTTON)
            self.assertTrue(game.team_menu)
            game.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE))
            game.step(.1)
            self.assertEqual(game.state.throws, 0)
            self.assertEqual(game.state.time, 0)
            for role, index, rect in TEAM_CHOICES:
                click(rect)
                self.assertEqual(getattr(game.state, role), index)
                game.draw()
            game.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE))
            self.assertFalse(game.team_menu)
            self.assertTrue(game.running)
            game.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE))
            self.assertEqual(game.state.throws, 1)
        finally:
            pygame.quit()


if __name__ == '__main__':
    unittest.main()
