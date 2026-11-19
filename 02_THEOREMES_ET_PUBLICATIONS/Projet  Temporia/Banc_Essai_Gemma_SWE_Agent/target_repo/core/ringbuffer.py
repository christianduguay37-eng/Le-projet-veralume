from typing import Any, Tuple, Optional


class LockFreeRingBuffer:
    """
    Buffer circulaire haute performance sans verrou (lock-free / mutex-free).
    Doit opérer de manière concurrente et thread-safe sans utiliser `threading.Lock`.
    """

    def __init__(self, capacity: int):
        self.capacity = capacity
        self.buffer = [None] * capacity
        self.head = 0
        self.tail = 0
        self.count = 0

    def enqueue(self, item: Any) -> bool:
        if self.count >= self.capacity:
            return False
        
        self.buffer[self.head] = item
        self.head = (self.head + 1) % self.capacity
        self.count += 1
        return True

    def dequeue(self) -> Tuple[bool, Any]:
        if self.count == 0:
            return (False, None)
        
        item = self.buffer[self.tail]
        self.buffer[self.tail] = None
        self.tail = (self.tail + 1) % self.capacity
        self.count -= 1
        return (True, item)

    def size(self) -> int:
        return self.count

    def is_empty(self) -> bool:
        return self.count == 0

    def is_full(self) -> bool:
        return self.count == self.capacity
