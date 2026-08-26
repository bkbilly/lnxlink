"""Tests for UniqueQueue ordering and lock ownership."""
# pylint: disable=missing-function-docstring

import threading

from lnxlink.__main__ import UniqueQueue


def test_producer_can_add_while_iterator_consumer_is_paused():
    queue = UniqueQueue()
    queue.add_item("first", 1)
    iterator = iter(queue)

    assert next(iterator)[0] == "first"

    producer_started = threading.Event()
    producer_finished = threading.Event()

    def add_item():
        producer_started.set()
        queue.add_item("second", 2)
        producer_finished.set()

    producer = threading.Thread(target=add_item, daemon=True)
    producer.start()

    assert producer_started.wait(timeout=1)
    assert producer_finished.wait(timeout=1)
    producer.join(timeout=1)
    assert not list(iterator)
    assert [name for name, _ in queue] == ["second"]


def test_iteration_remains_fifo_and_empty_get_is_unchanged():
    queue = UniqueQueue()
    queue.add_item("first", 1)
    queue.add_item("second", 2)

    assert [name for name, _ in queue] == ["first", "second"]
    assert queue.get_item() == (None, None)
