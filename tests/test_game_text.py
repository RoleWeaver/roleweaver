"""Outgoing NWN text keeps multilingual letters but avoids fragile punctuation."""

import unittest

from roleweaver.game_text import normalize_game_punctuation


class GameTextTests(unittest.TestCase):
    def test_smart_apostrophes_and_dashes_become_game_safe(self):
        source = "Then I’ll ask—please don’t leave… ‘Meriel’ said."
        self.assertEqual(
            normalize_game_punctuation(source),
            "Then I'll ask-please don't leave... 'Meriel' said.",
        )

    def test_multilingual_letters_and_line_breaks_are_preserved(self):
        source = "François, Zażółć, Привет, ¿dónde?\nL’amour"
        self.assertEqual(
            normalize_game_punctuation(source),
            "François, Zażółć, Привет, ¿dónde?\nL'amour",
        )
