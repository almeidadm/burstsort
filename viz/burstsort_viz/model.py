"""Simulação Python do burstsort, fiel ao C++ em upstream/src/burstsort.cpp.

Variante alvo: array-based bucket (std::vector), com expansão por doubling.
A simulação NÃO ordena — só registra eventos. As cenas Manim consomem o log.

Convenções:
- END_CHAR ('$') marca fim-de-string. Equivale a NUL no código C++.
- Cada bucket é uma lista Python com `capacity` controlada manualmente,
  para podermos detectar e emitir o evento de realloc.
"""

from typing import List, Optional

from .config import END_CHAR
from . import events as E


def _char_at(s: str, depth: int) -> str:
    """Equivalente a get_char<unsigned char>: retorna END_CHAR após o fim."""
    if depth >= len(s):
        return END_CHAR
    return s[depth]


def _is_end(c: str) -> bool:
    return c == END_CHAR


class _IdGen:
    def __init__(self):
        self._n = 0

    def next(self) -> int:
        self._n += 1
        return self._n


class Bucket:
    def __init__(self, bucket_id: int, capacity: int):
        self.id = bucket_id
        self.items: List[str] = []
        self.capacity = capacity

    def push(self, s: str, log: list) -> None:
        if len(self.items) == self.capacity:
            old_cap = self.capacity
            new_cap = old_cap * 2
            snapshot = tuple(self.items)
            self.capacity = new_cap
            log.append(E.BucketRealloc(
                bucket_id=self.id,
                old_capacity=old_cap,
                new_capacity=new_cap,
                snapshot=snapshot,
            ))
        self.items.append(s)
        log.append(E.BucketPush(
            bucket_id=self.id,
            string=s,
            new_size=len(self.items),
            capacity=self.capacity,
        ))

    def size(self) -> int:
        return len(self.items)


class TrieNode:
    def __init__(self, node_id: int):
        self.id = node_id
        # slot_char -> (is_trie: bool, payload: TrieNode | Bucket | None)
        self.slots: dict = {}


class Simulator:
    def __init__(self, threshold: int, init_cap: int):
        self.threshold = threshold
        self.init_cap = init_cap
        self.ids = _IdGen()
        self.log: List[E.Event] = []
        self.root = TrieNode(self.ids.next())

    def insert(self, s: str, idx: int) -> None:
        self.log.append(E.BeginInsert(string=s, global_index=idx))
        node = self.root
        depth = 0
        c = _char_at(s, depth)
        # desce enquanto o slot apontar para outro TrieNode
        while c in node.slots and node.slots[c][0] is True:
            child = node.slots[c][1]
            self.log.append(E.TrieDescend(
                from_node_id=node.id,
                to_node_id=child.id,
                slot_char=c,
                depth=depth,
            ))
            node = child
            depth += 1
            c = _char_at(s, depth)
        # garante bucket
        if c not in node.slots:
            bucket = Bucket(self.ids.next(), self.init_cap)
            node.slots[c] = (False, bucket)
            self.log.append(E.NewBucket(
                bucket_id=bucket.id,
                node_id=node.id,
                slot_char=c,
                depth=depth,
                initial_capacity=self.init_cap,
            ))
        else:
            bucket = node.slots[c][1]
        bucket.push(s, self.log)
        # end-slot nunca dispara burst (linha 233 do C++)
        if _is_end(c):
            return
        if bucket.size() > self.threshold:
            new_node = self._burst(bucket, depth + 1)
            node.slots[c] = (True, new_node)
            self.log.append(E.BurstEnd(
                new_node_id=new_node.id,
                replaces_bucket_id=bucket.id,
            ))

    def _burst(self, bucket: Bucket, depth: int) -> TrieNode:
        new_node = TrieNode(self.ids.next())
        self.log.append(E.BurstBegin(
            bucket_id=bucket.id,
            depth=depth,
            strings=tuple(bucket.items),
        ))
        # criação do nó já implícita pelo BurstBegin; emit explícito p/ animar
        self.log.append(E.BurstCreateTrieNode(
            new_node_id=new_node.id,
            parent_node_id=-1,  # ligação é feita no BurstEnd
            parent_slot_char="",
            depth=depth,
        ))
        for s in bucket.items:
            c = _char_at(s, depth)
            if c not in new_node.slots:
                sub = Bucket(self.ids.next(), self.init_cap)
                new_node.slots[c] = (False, sub)
                self.log.append(E.BurstCreateSubBucket(
                    new_bucket_id=sub.id,
                    parent_trie_id=new_node.id,
                    slot_char=c,
                    initial_capacity=self.init_cap,
                ))
            sub = new_node.slots[c][1]
            # push direto (sem realloc no caminho de burst — bucket recém-criado)
            sub.items.append(s)
            self.log.append(E.BurstPushToSubBucket(
                sub_bucket_id=sub.id,
                string=s,
            ))
        return new_node

    def traverse(self) -> List[str]:
        out: List[str] = []
        self._traverse_node(self.root, 0, out)
        self.log.append(E.TraverseComplete(output=tuple(out)))
        return out

    def _traverse_node(self, node: TrieNode, depth: int, out: List[str]) -> None:
        self.log.append(E.TraverseVisitTrie(node_id=node.id, depth=depth))
        # ordem canônica: end-slot primeiro, depois alfabético
        keys = sorted(node.slots.keys(), key=lambda k: (k != END_CHAR, k))
        for c in keys:
            is_trie, payload = node.slots[c]
            self.log.append(E.TraverseVisitSlot(
                node_id=node.id,
                slot_char=c,
                is_trie=is_trie,
                target_id=payload.id,
            ))
            if is_trie:
                self._traverse_node(payload, depth + 1, out)
            else:
                bucket: Bucket = payload
                emit = list(bucket.items)
                if not _is_end(c):
                    emit.sort()
                out.extend(emit)
                self.log.append(E.TraverseEmitBucket(
                    bucket_id=bucket.id,
                    strings=tuple(emit),
                    sorted_emit=not _is_end(c),
                ))


def simulate(strings, threshold: int, initial_capacity: int):
    """Roda o burstsort completo e devolve (log_de_eventos, saida_ordenada)."""
    sim = Simulator(threshold, initial_capacity)
    for i, s in enumerate(strings):
        sim.insert(s, i)
    out = sim.traverse()
    return sim.log, out
