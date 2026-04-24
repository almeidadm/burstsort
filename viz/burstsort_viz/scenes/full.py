"""Cena completa: Inserção · Realloc · Burst · Travessia.

Despacha eventos do simulador para handlers, mantendo estado em atributos
da Scene. Cobre o ciclo de vida inteiro do burstsort em ~50s.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import numpy as np

from manim import (
    Scene, Text, VGroup, Arrow, Triangle, Square,
    FadeIn, FadeOut, Create, Write, Transform, GrowArrow,
    Indicate, LaggedStart,
    UP, DOWN, LEFT, RIGHT, ORIGIN, PI,
)

from burstsort_viz.config import DATASET, THRESHOLD, INIT_CAP, COLORS
from burstsort_viz.model import simulate
from burstsort_viz.events import (
    BeginInsert, NewBucket, BucketPush, BucketRealloc,
    BurstBegin, BurstCreateTrieNode, BurstCreateSubBucket,
    BurstPushToSubBucket, BurstEnd,
    TraverseVisitTrie, TraverseVisitSlot, TraverseEmitBucket, TraverseComplete,
)
from burstsort_viz.mobjects import (
    StringMob, InputArrayMob, BucketSlotMob, TrieNodeMob,
)


ROOT_SLOTS = ["$", "a", "b"]
SUBTRIE_SLOTS = ["$", "b", "c", "d"]


def _caption(text, color=None):
    return Text(text, font_size=20, color=color or COLORS["caption"]).to_edge(
        DOWN, buff=0.3
    )


class FullLifecycleScene(Scene):
    def construct(self):
        self.camera.background_color = COLORS["bg"]
        self._init_static()
        self._consume_events()

    # ------------------------------------------------------------------
    # Setup
    # ------------------------------------------------------------------

    def _init_static(self):
        self.title = Text(
            "Burstsort — ciclo completo",
            font_size=32, color=COLORS["text"],
        ).to_edge(UP, buff=0.3)
        self.play(Write(self.title), run_time=0.7)

        self.input_panel = (
            InputArrayMob(DATASET).to_edge(LEFT, buff=0.4).shift(UP * 0.3)
        )
        self.input_index = {s: i for i, s in enumerate(DATASET)}
        self.play(FadeIn(self.input_panel), run_time=0.4)

        self._build_output_panel()
        self.play(FadeIn(self.output_panel), run_time=0.4)

        self.root = TrieNodeMob(ROOT_SLOTS).shift(UP * 2.0)
        root_label = Text("trie root", font_size=18, color=COLORS["caption"])
        root_label.next_to(self.root, UP, buff=0.15)
        self.play(Create(self.root), Write(root_label), run_time=0.5)

        self.caption = _caption(
            "Cada string entra no bucket do seu primeiro caractere."
        )
        self.play(Write(self.caption), run_time=0.5)

        # State
        self.trie_mobs = {1: self.root}                    # node_id -> TrieNodeMob
        self.bucket_mobs = {}                              # bucket_id -> BucketSlotMob
        self.bucket_arrows = {}                            # bucket_id -> Arrow
        self.bucket_cap_labels = {}                        # bucket_id -> Text
        self.bucket_parent = {}                            # bucket_id -> (node_id, slot_char)
        self.active_input = None
        self.cursor = None
        self.output_filled = 0
        self.current_burst_old_bucket_id = None

    def _build_output_panel(self):
        title = Text("saída", font_size=20, color=COLORS["caption"])
        slot_size = 0.5
        self.output_slots = []
        for _ in DATASET:
            sq = Square(
                side_length=slot_size,
                color=COLORS["bucket_border"],
                fill_color=COLORS["output_array"],
                fill_opacity=0.15,
                stroke_width=2,
            )
            self.output_slots.append(sq)
        col = VGroup(*self.output_slots).arrange(DOWN, buff=0.06)
        col.next_to(title, DOWN, buff=0.25)
        self.output_panel = VGroup(title, col)
        self.output_panel.to_edge(RIGHT, buff=0.4).shift(UP * 0.3)

    # ------------------------------------------------------------------
    # Dispatcher
    # ------------------------------------------------------------------

    def _consume_events(self):
        log, _ = simulate(DATASET, THRESHOLD, INIT_CAP)
        for ev in log:
            handler = getattr(self, f"_on_{type(ev).__name__}", None)
            if handler:
                handler(ev)

    # ------------------------------------------------------------------
    # Insert / Realloc handlers
    # ------------------------------------------------------------------

    def _on_BeginInsert(self, ev):
        idx = self.input_index[ev.string]
        self.active_input = self.input_panel.string_mobs[idx]
        self.play(
            Indicate(self.active_input, color=COLORS["active"], scale_factor=1.3),
            run_time=0.35,
        )

    def _on_NewBucket(self, ev):
        parent = self.trie_mobs[ev.node_id]
        slot_bottom = parent.slot_bottom(ev.slot_char)
        bucket = BucketSlotMob(ev.initial_capacity)
        # se já existe sub-trie no espaço abaixo, deixa o bucket próximo do pai
        burst_done = any(nid != 1 for nid in self.trie_mobs)
        buff = 0.4 if burst_done else 0.5
        bucket.next_to(slot_bottom, DOWN, buff=buff)
        arrow = Arrow(
            start=slot_bottom + DOWN * 0.05,
            end=bucket.get_top() + UP * 0.05,
            color=COLORS["pointer"], buff=0.05, stroke_width=3,
            max_tip_length_to_length_ratio=0.12,
        )
        self.play(GrowArrow(arrow), Create(bucket), run_time=0.5)
        # cap label à direita para não colidir com nada abaixo
        cap_label = Text(
            f"size 0 / cap {ev.initial_capacity}",
            font_size=16, color=COLORS["caption"],
        ).next_to(bucket, RIGHT, buff=0.2)
        self.play(FadeIn(cap_label), run_time=0.15)

        self.bucket_mobs[ev.bucket_id] = bucket
        self.bucket_arrows[ev.bucket_id] = arrow
        self.bucket_cap_labels[ev.bucket_id] = cap_label
        self.bucket_parent[ev.bucket_id] = (ev.node_id, ev.slot_char)

    def _on_BucketPush(self, ev):
        bucket = self.bucket_mobs[ev.bucket_id]
        target = bucket.slot_position(ev.new_size - 1)
        copy = self.active_input.copy()
        self.add(copy)
        self.play(copy.animate.move_to(target).scale(0.85), run_time=0.55)
        bucket.contents.append(copy)

        new_label = Text(
            f"size {ev.new_size} / cap {ev.capacity}",
            font_size=16, color=COLORS["caption"],
        ).next_to(bucket, RIGHT, buff=0.2)
        self.play(Transform(self.bucket_cap_labels[ev.bucket_id], new_label),
                  run_time=0.2)

        if ev.new_size == ev.capacity:
            self.play(
                *[sq.animate.set_stroke(COLORS["bucket_growing"], width=4)
                  for sq in bucket.slot_squares],
                run_time=0.3,
            )

        self.play(self.active_input.animate.set_opacity(0.25), run_time=0.15)

    def _on_BucketRealloc(self, ev):
        cap = _caption(
            f"Realloc {ev.old_capacity} → {ev.new_capacity}: "
            f"aloca novo array, copia ponteiros.",
            color=COLORS["bucket_growing"],
        )
        self.play(Transform(self.caption, cap), run_time=0.4)

        old_bucket = self.bucket_mobs[ev.bucket_id]
        old_center = old_bucket.get_center()
        new_bucket = BucketSlotMob(ev.new_capacity)
        new_bucket.move_to(old_center + DOWN * 1.2)
        self.play(Create(new_bucket), run_time=0.5)

        moves = [c.animate.move_to(new_bucket.slot_position(i))
                 for i, c in enumerate(old_bucket.contents)]
        self.play(LaggedStart(*moves, lag_ratio=0.3), run_time=1.2)
        new_bucket.contents = list(old_bucket.contents)

        node_id, slot_char = self.bucket_parent[ev.bucket_id]
        parent = self.trie_mobs[node_id]
        new_arrow = Arrow(
            start=parent.slot_bottom(slot_char) + DOWN * 0.05,
            end=new_bucket.get_top() + UP * 0.05,
            color=COLORS["pointer"], buff=0.05, stroke_width=3,
            max_tip_length_to_length_ratio=0.12,
        )
        self.play(
            FadeOut(old_bucket),
            Transform(self.bucket_arrows[ev.bucket_id], new_arrow),
            run_time=0.5,
        )
        self.bucket_mobs[ev.bucket_id] = new_bucket

        new_label = Text(
            f"size {len(new_bucket.contents)} / cap {ev.new_capacity}",
            font_size=16, color=COLORS["caption"],
        ).next_to(new_bucket, RIGHT, buff=0.2)
        self.play(Transform(self.bucket_cap_labels[ev.bucket_id], new_label),
                  run_time=0.2)

        normal = _caption("Array maior alocado. Inserções continuam no fim.")
        self.play(Transform(self.caption, normal), run_time=0.3)

    # ------------------------------------------------------------------
    # Burst handlers
    # ------------------------------------------------------------------

    def _on_BurstBegin(self, ev):
        cap = _caption(
            f"BURST! size {len(ev.strings)} > threshold {THRESHOLD}.",
            color=COLORS["end_slot"],
        )
        self.play(Transform(self.caption, cap), run_time=0.5)
        old_bucket = self.bucket_mobs[ev.bucket_id]
        self.play(
            *[sq.animate.set_fill(COLORS["end_slot"], opacity=0.7)
              for sq in old_bucket.slot_squares],
            run_time=0.4,
        )
        self.wait(0.4)
        self.current_burst_old_bucket_id = ev.bucket_id

    def _on_BurstCreateTrieNode(self, ev):
        cap = _caption(
            "Bucket vira TrieNode. Strings se redistribuem pelo PRÓXIMO caractere."
        )
        self.play(Transform(self.caption, cap), run_time=0.5)

        old_id = self.current_burst_old_bucket_id
        old_bucket = self.bucket_mobs[old_id]
        old_center = old_bucket.get_center()
        self.play(
            FadeOut(old_bucket),
            FadeOut(self.bucket_cap_labels[old_id]),
            run_time=0.4,
        )

        sub_trie = TrieNodeMob(SUBTRIE_SLOTS, slot_size=1.4).move_to(old_center)
        self.play(Create(sub_trie), run_time=0.7)
        self.trie_mobs[ev.new_node_id] = sub_trie

    def _on_BurstCreateSubBucket(self, ev):
        sub_trie = self.trie_mobs[ev.parent_trie_id]
        slot_bottom = sub_trie.slot_bottom(ev.slot_char)
        bucket = BucketSlotMob(ev.initial_capacity, slot_size=0.6)
        bucket.next_to(slot_bottom, DOWN, buff=0.4)
        arrow = Arrow(
            start=slot_bottom + DOWN * 0.05,
            end=bucket.get_top() + UP * 0.05,
            color=COLORS["pointer"], buff=0.05, stroke_width=2,
            max_tip_length_to_length_ratio=0.15,
        )
        self.play(GrowArrow(arrow), Create(bucket), run_time=0.4)
        self.bucket_mobs[ev.new_bucket_id] = bucket
        self.bucket_arrows[ev.new_bucket_id] = arrow
        self.bucket_parent[ev.new_bucket_id] = (ev.parent_trie_id, ev.slot_char)

    def _on_BurstPushToSubBucket(self, ev):
        sub_bucket = self.bucket_mobs[ev.sub_bucket_id]
        old_bucket = self.bucket_mobs[self.current_burst_old_bucket_id]
        s_mob = next(c for c in old_bucket.contents if c.text_value == ev.string)
        target = sub_bucket.slot_position(0)
        self.bring_to_front(s_mob)  # evita ficar atrás dos slots do sub-bucket
        self.play(
            s_mob.animate.move_to(target).scale_to_fit_width(0.5),
            run_time=0.45,
        )
        sub_bucket.contents.append(s_mob)
        old_bucket.contents.remove(s_mob)

    def _on_BurstEnd(self, ev):
        old_id = ev.replaces_bucket_id
        sub_trie = self.trie_mobs[ev.new_node_id]
        node_id, slot_char = self.bucket_parent[old_id]
        parent = self.trie_mobs[node_id]
        slot_sq = parent.slot_groups[slot_char][0]
        self.play(
            slot_sq.animate.set_fill(COLORS["trie_is_trie_bit"], opacity=0.95),
            run_time=0.4,
        )
        new_arrow = Arrow(
            start=parent.slot_bottom(slot_char) + DOWN * 0.05,
            end=sub_trie.get_top() + UP * 0.05,
            color=COLORS["pointer"], buff=0.05, stroke_width=3,
            max_tip_length_to_length_ratio=0.12,
        )
        self.play(Transform(self.bucket_arrows[old_id], new_arrow), run_time=0.4)
        del self.bucket_mobs[old_id]
        cap = _caption(
            "Burst completo. is_trie=1 (verde claro). Slot $ nunca sofre burst."
        )
        self.play(Transform(self.caption, cap), run_time=0.5)
        self.wait(1.0)
        self.current_burst_old_bucket_id = None

    # ------------------------------------------------------------------
    # Traverse handlers
    # ------------------------------------------------------------------

    def _make_cursor(self):
        cursor = Triangle(
            color=COLORS["active"],
            fill_color=COLORS["active"],
            fill_opacity=1,
            stroke_width=2,
        ).rotate(PI).scale(0.18)
        return cursor

    def _on_TraverseVisitTrie(self, ev):
        node = self.trie_mobs[ev.node_id]
        if self.cursor is None:
            self.cursor = self._make_cursor()
            self.cursor.next_to(node, UP, buff=0.1)
            cap = _caption(
                "Travessia: cursor varre slots 0,1,2,... emitindo strings."
            )
            self.play(Transform(self.caption, cap), FadeIn(self.cursor),
                      run_time=0.5)
        else:
            self.play(self.cursor.animate.next_to(node, UP, buff=0.1),
                      run_time=0.35)
            cap = _caption(
                f"is_trie=1 — desce para o sub-trie (depth = {ev.depth})."
            )
            self.play(Transform(self.caption, cap), run_time=0.3)

    def _on_TraverseVisitSlot(self, ev):
        node = self.trie_mobs[ev.node_id]
        slot_grp = node.slot_groups[ev.slot_char]
        self.play(self.cursor.animate.next_to(slot_grp, UP, buff=0.05),
                  run_time=0.3)

    def _on_TraverseEmitBucket(self, ev):
        bucket = self.bucket_mobs[ev.bucket_id]
        if ev.sorted_emit and len(ev.strings) > 1:
            cap = _caption(
                "Bucket comum (não end-slot): mkqsort ordena antes de emitir."
            )
            self.play(Transform(self.caption, cap), run_time=0.3)
            new_pos = {s: bucket.slot_position(i) for i, s in enumerate(ev.strings)}
            moves = [c.animate.move_to(new_pos[c.text_value])
                     for c in bucket.contents]
            self.play(LaggedStart(*moves, lag_ratio=0.3), run_time=0.8)
            bucket.contents.sort(key=lambda c: ev.strings.index(c.text_value))
        elif not ev.sorted_emit:
            cap = _caption("End-slot: copia direto, sem ordenar.",
                           color=COLORS["end_slot"])
            self.play(Transform(self.caption, cap), run_time=0.3)

        for s_mob in bucket.contents:
            target = self.output_slots[self.output_filled].get_center()
            self.bring_to_front(s_mob)
            self.play(s_mob.animate.move_to(target).scale_to_fit_width(0.45),
                      run_time=0.45)
            self.play(
                self.output_slots[self.output_filled].animate.set_fill(
                    COLORS["output_array"], opacity=0.55
                ),
                run_time=0.1,
            )
            self.output_filled += 1

        # limpa o bucket vazio
        cleanup = [FadeOut(bucket)]
        if ev.bucket_id in self.bucket_arrows:
            cleanup.append(FadeOut(self.bucket_arrows[ev.bucket_id]))
        if ev.bucket_id in self.bucket_cap_labels:
            cleanup.append(FadeOut(self.bucket_cap_labels[ev.bucket_id]))
        self.play(*cleanup, run_time=0.25)

    def _on_TraverseComplete(self, ev):
        if self.cursor is not None:
            self.play(FadeOut(self.cursor), run_time=0.3)
        cap = _caption(
            "Travessia completa. Saída em ordem lexicográfica.",
            color=COLORS["active"],
        )
        self.play(Transform(self.caption, cap), run_time=0.5)
        self.play(
            *[sq.animate.set_stroke(COLORS["active"], width=4)
              for sq in self.output_slots],
            run_time=0.5,
        )
        self.wait(2.0)
