"""Parâmetros globais da animação. Centraliza dataset, cores e timings."""

DATASET = ["a", "ab", "ac", "ad", "ba", "b"]
THRESHOLD = 3
INIT_CAP = 2

END_CHAR = "$"

COLORS = {
    "bg":                 "#1e1e1e",
    "bucket_slot_empty":  "#2b2b2b",
    "bucket_slot_filled": "#4fc3f7",
    "bucket_border":      "#ffffff",
    "bucket_growing":     "#ffd54f",
    "trie_node":          "#81c784",
    "trie_is_trie_bit":   "#c5e1a5",
    "end_slot":           "#ef5350",
    "active":             "#ffeb3b",
    "pointer":            "#ffffff",
    "output_array":       "#ce93d8",
    "text":               "#ffffff",
    "caption":            "#bbbbbb",
}

TIMINGS = {
    "insert":       0.8,
    "realloc":      2.0,
    "burst_frame":  0.3,
    "traverse":     0.6,
    "caption_hold": 1.5,
}
