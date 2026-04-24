"""Mobjects reutilizáveis: strings, buckets, trie nodes, arrays.

Cada classe é um VGroup. Não animam por si; as cenas chamam `self.play(...)`
sobre as primitivas Manim aplicadas a esses mobjects.
"""

from manim import (
    VGroup, Rectangle, Square, Text,
    LEFT, RIGHT, UP, DOWN, ORIGIN,
)

from .config import COLORS


class StringMob(VGroup):
    """Uma string como um retângulo etiquetado, transportável entre estruturas."""

    def __init__(self, text, font_size=22, **kwargs):
        super().__init__(**kwargs)
        self.text_value = text
        rect = Rectangle(
            width=max(0.7, 0.30 * len(text) + 0.45),
            height=0.55,
            color=COLORS["bucket_border"],
            fill_color=COLORS["bucket_slot_filled"],
            fill_opacity=1,
            stroke_width=2,
        )
        label = Text(text, font_size=font_size, color="#000000")
        label.move_to(rect.get_center())
        self.add(rect, label)
        self.rect = rect
        self.label = label


class InputArrayMob(VGroup):
    """Coluna vertical de strings de entrada."""

    def __init__(self, strings, **kwargs):
        super().__init__(**kwargs)
        self.string_mobs = []

        title = Text("entrada", font_size=20, color=COLORS["caption"])
        self.add(title)

        for i, s in enumerate(strings):
            sm = StringMob(s)
            sm.next_to(title, DOWN, buff=0.25 + 0.45 * i)
            self.add(sm)
            self.string_mobs.append(sm)


class BucketSlotMob(VGroup):
    """Linha horizontal de N slots vazios (uma 'std::vector' visual)."""

    def __init__(self, capacity, slot_size=0.7, **kwargs):
        super().__init__(**kwargs)
        self.capacity = capacity
        self.slot_size = slot_size
        self.slot_squares = []
        for i in range(capacity):
            sq = Square(
                side_length=slot_size,
                color=COLORS["bucket_border"],
                fill_color=COLORS["bucket_slot_empty"],
                fill_opacity=1,
                stroke_width=2,
            )
            sq.shift(RIGHT * slot_size * i)
            self.slot_squares.append(sq)
            self.add(sq)
        # centra o grupo na origem
        self.shift(LEFT * slot_size * (capacity - 1) / 2)
        self.contents = []  # StringMobs adicionados externamente

    def slot_position(self, idx):
        return self.slot_squares[idx].get_center()


class TrieNodeMob(VGroup):
    """Linha horizontal de slots etiquetados representando um TrieNode."""

    def __init__(self, slot_chars, slot_size=0.65, **kwargs):
        super().__init__(**kwargs)
        self.slot_chars = list(slot_chars)
        self.slot_size = slot_size
        self.slot_groups = {}
        for i, ch in enumerate(self.slot_chars):
            color = COLORS["end_slot"] if ch == "$" else COLORS["trie_node"]
            sq = Square(
                side_length=slot_size,
                color=COLORS["bucket_border"],
                fill_color=color,
                fill_opacity=0.85,
                stroke_width=2,
            )
            sq.shift(RIGHT * slot_size * i)
            label = Text(ch, font_size=20, color="#000000")
            label.move_to(sq.get_center())
            grp = VGroup(sq, label)
            self.slot_groups[ch] = grp
            self.add(grp)
        self.shift(LEFT * slot_size * (len(self.slot_chars) - 1) / 2)

    def slot_bottom(self, ch):
        return self.slot_groups[ch].get_bottom()
