"""Eventos emitidos pela simulação do burstsort.

Cada operação relevante do algoritmo (insert, realloc, burst, traverse) gera
um evento imutável. As cenas Manim consomem essa lista para animar.
"""

from dataclasses import dataclass, field
from typing import List


@dataclass(frozen=True)
class Event:
    pass


@dataclass(frozen=True)
class BeginInsert(Event):
    string: str
    global_index: int


@dataclass(frozen=True)
class TrieDescend(Event):
    from_node_id: int
    to_node_id: int
    slot_char: str
    depth: int


@dataclass(frozen=True)
class NewBucket(Event):
    bucket_id: int
    node_id: int
    slot_char: str
    depth: int
    initial_capacity: int


@dataclass(frozen=True)
class BucketPush(Event):
    bucket_id: int
    string: str
    new_size: int
    capacity: int


@dataclass(frozen=True)
class BucketRealloc(Event):
    bucket_id: int
    old_capacity: int
    new_capacity: int
    snapshot: tuple  # strings já no bucket no momento da realloc


@dataclass(frozen=True)
class BurstBegin(Event):
    bucket_id: int
    depth: int
    strings: tuple


@dataclass(frozen=True)
class BurstCreateTrieNode(Event):
    new_node_id: int
    parent_node_id: int
    parent_slot_char: str
    depth: int


@dataclass(frozen=True)
class BurstCreateSubBucket(Event):
    new_bucket_id: int
    parent_trie_id: int
    slot_char: str
    initial_capacity: int


@dataclass(frozen=True)
class BurstPushToSubBucket(Event):
    sub_bucket_id: int
    string: str


@dataclass(frozen=True)
class BurstEnd(Event):
    new_node_id: int
    replaces_bucket_id: int


@dataclass(frozen=True)
class TraverseVisitTrie(Event):
    node_id: int
    depth: int


@dataclass(frozen=True)
class TraverseVisitSlot(Event):
    node_id: int
    slot_char: str
    is_trie: bool
    target_id: int  # bucket_id ou child_node_id; -1 se vazio


@dataclass(frozen=True)
class TraverseEmitBucket(Event):
    bucket_id: int
    strings: tuple
    sorted_emit: bool


@dataclass(frozen=True)
class TraverseComplete(Event):
    output: tuple
