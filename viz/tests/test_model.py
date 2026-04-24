"""Valida que o simulador reproduz o algoritmo de burstsort.cpp fielmente."""

from burstsort_viz import events as E
from burstsort_viz.config import DATASET, THRESHOLD, INIT_CAP
from burstsort_viz.model import simulate


def _count(log, cls):
    return sum(1 for e in log if isinstance(e, cls))


def test_output_is_sorted_lexicographically():
    log, out = simulate(DATASET, THRESHOLD, INIT_CAP)
    assert out == sorted(DATASET), f"got {out}, expected {sorted(DATASET)}"


def test_one_realloc_in_dataset():
    log, _ = simulate(DATASET, THRESHOLD, INIT_CAP)
    assert _count(log, E.BucketRealloc) == 1


def test_realloc_doubles_capacity():
    log, _ = simulate(DATASET, THRESHOLD, INIT_CAP)
    realloc = next(e for e in log if isinstance(e, E.BucketRealloc))
    assert realloc.old_capacity == 2
    assert realloc.new_capacity == 4
    assert realloc.snapshot == ("a", "ab")


def test_one_burst_in_dataset():
    log, _ = simulate(DATASET, THRESHOLD, INIT_CAP)
    assert _count(log, E.BurstBegin) == 1
    assert _count(log, E.BurstEnd) == 1


def test_burst_separates_end_string_into_end_slot():
    """`a` termina no depth=1 e deve ir para o slot '$' do sub-trie."""
    log, _ = simulate(DATASET, THRESHOLD, INIT_CAP)
    push_events = [e for e in log if isinstance(e, E.BurstPushToSubBucket)]
    sub_buckets = {e.new_bucket_id: e.slot_char
                   for e in log if isinstance(e, E.BurstCreateSubBucket)}
    a_slot = next(sub_buckets[p.sub_bucket_id]
                  for p in push_events if p.string == "a")
    assert a_slot == "$", f"esperado slot '$', veio '{a_slot}'"


def test_burst_distributes_continuing_strings_correctly():
    log, _ = simulate(DATASET, THRESHOLD, INIT_CAP)
    sub_buckets = {e.new_bucket_id: e.slot_char
                   for e in log if isinstance(e, E.BurstCreateSubBucket)}
    placement = {p.string: sub_buckets[p.sub_bucket_id]
                 for p in log if isinstance(p, E.BurstPushToSubBucket)}
    assert placement["a"] == "$"
    assert placement["ab"] == "b"
    assert placement["ac"] == "c"
    assert placement["ad"] == "d"


def test_traverse_does_not_sort_end_slot():
    log, _ = simulate(DATASET, THRESHOLD, INIT_CAP)
    emits = [e for e in log if isinstance(e, E.TraverseEmitBucket)]
    # bucket emitido contendo 'a' (no slot $ do sub-trie) não pode ser sorted
    a_emit = next(e for e in emits if e.strings == ("a",))
    assert a_emit.sorted_emit is False


def test_traverse_sorts_non_end_buckets():
    """O bucket [ba, b] no slot 'b' da raiz deve ser ordenado para [b, ba]."""
    log, _ = simulate(DATASET, THRESHOLD, INIT_CAP)
    emits = [e for e in log if isinstance(e, E.TraverseEmitBucket)]
    ba_emit = next(e for e in emits if "ba" in e.strings)
    assert ba_emit.sorted_emit is True
    assert ba_emit.strings == ("b", "ba")


def test_event_order_insert_then_traverse():
    """Todos os eventos de insert devem vir antes de qualquer evento de traverse."""
    log, _ = simulate(DATASET, THRESHOLD, INIT_CAP)
    insert_classes = (E.BeginInsert, E.NewBucket, E.BucketPush, E.BucketRealloc,
                      E.BurstBegin, E.BurstEnd)
    traverse_classes = (E.TraverseVisitTrie, E.TraverseVisitSlot,
                        E.TraverseEmitBucket, E.TraverseComplete)
    last_insert = max(i for i, e in enumerate(log) if isinstance(e, insert_classes))
    first_traverse = min(i for i, e in enumerate(log) if isinstance(e, traverse_classes))
    assert last_insert < first_traverse


def test_no_burst_on_end_slot_bucket():
    """Bucket no slot '$' nunca pode ter sido bursted."""
    log, _ = simulate(DATASET, THRESHOLD, INIT_CAP)
    end_buckets = {e.bucket_id for e in log
                   if isinstance(e, E.NewBucket) and e.slot_char == "$"}
    end_buckets |= {e.new_bucket_id for e in log
                    if isinstance(e, E.BurstCreateSubBucket) and e.slot_char == "$"}
    burst_targets = {e.bucket_id for e in log if isinstance(e, E.BurstBegin)}
    assert end_buckets.isdisjoint(burst_targets)
