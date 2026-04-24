"""Cena 1 — Inserção e Realloc.

Consome eventos do simulador até (exclusive) o primeiro BurstBegin.
Demonstra: push_back, bucket cheio, realloc com cópia visível.
"""

import sys
from pathlib import Path

# Permite rodar `manim -ql viz/burstsort_viz/scenes/insert.py InsertPhaseScene`
# de qualquer cwd: adiciona o diretório `viz/` ao sys.path.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from manim import (
    Scene, Text, VGroup, Arrow,
    FadeIn, FadeOut, Create, Write, Transform, GrowArrow,
    Indicate, LaggedStart,
    UP, DOWN, LEFT, RIGHT,
)

from burstsort_viz.config import DATASET, THRESHOLD, INIT_CAP, COLORS
from burstsort_viz.model import simulate
from burstsort_viz.events import (
    BeginInsert, NewBucket, BucketPush, BucketRealloc, BurstBegin,
)
from burstsort_viz.mobjects import (
    StringMob, InputArrayMob, BucketSlotMob, TrieNodeMob,
)


def _caption(text, color=None):
    return Text(text, font_size=22, color=color or COLORS["caption"]).to_edge(
        DOWN, buff=0.5
    )


class InsertPhaseScene(Scene):
    def construct(self):
        self.camera.background_color = COLORS["bg"]

        # --- Título ---
        title = Text(
            "Burstsort — Inserção & Realloc",
            font_size=34,
            color=COLORS["text"],
        ).to_edge(UP, buff=0.4)
        self.play(Write(title), run_time=1.0)

        # --- Painel de entrada ---
        input_panel = InputArrayMob(DATASET).to_edge(LEFT, buff=0.5).shift(UP * 0.5)
        self.play(FadeIn(input_panel), run_time=0.6)

        # --- Trie root ---
        root = TrieNodeMob(["$", "a", "b"]).shift(UP * 1.6)
        root_label = Text("trie root", font_size=18, color=COLORS["caption"])
        root_label.next_to(root, UP, buff=0.15)
        self.play(Create(root), Write(root_label), run_time=0.8)

        # --- Caption inicial ---
        caption = _caption(
            "Cada string é empurrada no bucket do seu primeiro caractere."
        )
        self.play(Write(caption), run_time=0.6)

        # --- Simulação ---
        log, _ = simulate(DATASET, THRESHOLD, INIT_CAP)

        current_bucket = None
        bucket_arrow = None
        cap_label = None
        active_input = None
        input_index = {s: i for i, s in enumerate(DATASET)}

        for ev in log:
            if isinstance(ev, BurstBegin):
                break

            if isinstance(ev, BeginInsert):
                idx = input_index[ev.string]
                active_input = input_panel.string_mobs[idx]
                self.play(Indicate(active_input, color=COLORS["active"], scale_factor=1.3),
                          run_time=0.4)

            elif isinstance(ev, NewBucket):
                new_bucket = BucketSlotMob(ev.initial_capacity)
                slot_bottom = root.slot_bottom(ev.slot_char)
                new_bucket.next_to(slot_bottom, DOWN, buff=1.4)

                arrow = Arrow(
                    start=slot_bottom + DOWN * 0.05,
                    end=new_bucket.get_top() + UP * 0.05,
                    color=COLORS["pointer"],
                    buff=0.05,
                    stroke_width=3,
                    max_tip_length_to_length_ratio=0.12,
                )
                self.play(GrowArrow(arrow), Create(new_bucket), run_time=0.6)

                current_bucket = new_bucket
                bucket_arrow = arrow

                cap_label = Text(f"size 0 / cap {ev.initial_capacity}",
                                 font_size=18, color=COLORS["caption"])
                cap_label.next_to(new_bucket, DOWN, buff=0.25)
                self.play(FadeIn(cap_label), run_time=0.2)

            elif isinstance(ev, BucketPush):
                slot_idx = ev.new_size - 1
                target = current_bucket.slot_position(slot_idx)

                copy = active_input.copy()
                self.add(copy)
                self.play(
                    copy.animate.move_to(target).scale(0.85),
                    run_time=0.7,
                )
                current_bucket.contents.append(copy)

                # atualiza rótulo de capacidade
                new_cap_label = Text(
                    f"size {ev.new_size} / cap {ev.capacity}",
                    font_size=18, color=COLORS["caption"],
                ).next_to(current_bucket, DOWN, buff=0.25)
                self.play(Transform(cap_label, new_cap_label), run_time=0.3)

                # bucket cheio: borda amarela
                if ev.new_size == ev.capacity:
                    self.play(
                        *[
                            sq.animate.set_stroke(COLORS["bucket_growing"], width=4)
                            for sq in current_bucket.slot_squares
                        ],
                        run_time=0.4,
                    )
                    full_caption = _caption(
                        f"Bucket cheio ({ev.capacity}/{ev.capacity}). "
                        "Próximo push dispara realloc.",
                        color=COLORS["bucket_growing"],
                    )
                    self.play(Transform(caption, full_caption), run_time=0.4)

                # apaga string da entrada (consumida)
                self.play(active_input.animate.set_opacity(0.25), run_time=0.2)

            elif isinstance(ev, BucketRealloc):
                realloc_caption = _caption(
                    f"Realloc {ev.old_capacity} → {ev.new_capacity}: "
                    f"aloca novo array, copia {len(ev.snapshot)} ponteiros.",
                    color=COLORS["bucket_growing"],
                )
                self.play(Transform(caption, realloc_caption), run_time=0.5)

                # constrói novo bucket maior abaixo do antigo
                new_bucket = BucketSlotMob(ev.new_capacity)
                old_center = current_bucket.get_center()
                new_bucket.move_to(old_center + DOWN * 1.3)
                self.play(Create(new_bucket), run_time=0.6)

                # copia ponteiros (LaggedStart didático)
                moves = []
                for i, content in enumerate(current_bucket.contents):
                    target = new_bucket.slot_position(i)
                    moves.append(content.animate.move_to(target))
                self.play(LaggedStart(*moves, lag_ratio=0.35), run_time=1.5)

                # transfere ownership conceitual
                new_bucket.contents = list(current_bucket.contents)

                # esvazia o velho (frame fade-out) e religa a seta
                new_arrow = Arrow(
                    start=root.slot_bottom("a") + DOWN * 0.05,
                    end=new_bucket.get_top() + UP * 0.05,
                    color=COLORS["pointer"],
                    buff=0.05,
                    stroke_width=3,
                    max_tip_length_to_length_ratio=0.12,
                )
                self.play(
                    FadeOut(current_bucket),
                    Transform(bucket_arrow, new_arrow),
                    run_time=0.6,
                )

                current_bucket = new_bucket

                new_cap_label = Text(
                    f"size {len(new_bucket.contents)} / cap {ev.new_capacity}",
                    font_size=18, color=COLORS["caption"],
                ).next_to(new_bucket, DOWN, buff=0.25)
                self.play(Transform(cap_label, new_cap_label), run_time=0.3)

                normal_caption = _caption(
                    "Array maior alocado. Inserções continuam no fim."
                )
                self.play(Transform(caption, normal_caption), run_time=0.4)

        # --- Fecho da fase ---
        ready_caption = _caption(
            f"Bucket atingiu size > threshold ({THRESHOLD}). Próxima fase: BURST.",
            color=COLORS["end_slot"],
        )
        self.play(Transform(caption, ready_caption), run_time=0.6)
        self.wait(1.8)
