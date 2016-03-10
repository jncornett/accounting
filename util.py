from collections import deque


class UniBufferedStream(object):

    """
    >>> u = UniBufferedStream(iter([]))
    >>> u.empty
    True
    >>> u = UniBufferedStream(iter([1, 2]))
    >>> u.buf
    1
    >>> u.empty
    False
    >>> u.fetch()
    >>> u.buf
    2
    >>> u.empty
    False
    >>> u.fetch()
    >>> u.empty
    True
    """

    def __init__(self, it):
        self.it = it
        self.empty = False
        self.buf = None
        self.fetch()

    def fetch(self):
        try:
            self.buf = next(self.it)
        except StopIteration:
            self.empty = True
            self.buf = None


class OrderedStream(object):

    """
    >>> a = [1, 2, 4, 8, 16, 32]
    >>> b = [1, 2, 3, 64, 128, 1000]
    >>> c = []
    >>> os = OrderedStream([iter(a), iter(b), iter(c)])
    >>> list(os.generate()) == sorted(a + b)
    True
    >>> os = OrderedStream([iter(a)], allow_late=False)
    >>> x = os.generate()
    >>> next(x)
    1
    >>> next(x)
    2
    >>> os.add_source(iter(b))
    >>> next(x)
    4
    >>> os = OrderedStream([iter(a)], allow_late=True)
    >>> x = os.generate()
    >>> next(x)
    1
    >>> next(x)
    2
    >>> os.add_source(iter(b))
    >>> next(x)
    1
    """

    def __init__(self, sources, key=None, allow_late=False):
        self.allow_late = allow_late
        self.streams = {}
        self._holes = set()

        self.set_key(key)

        for source in sources:
            self.add_source(source)

    def set_key(self, key=None):
        if key:
            self._key = lambda x, fn=key: fn(x[1].buf)
        else:
            self._key = lambda x: x[1].buf

    def add_source(self, source):
        stream = UniBufferedStream(source)
        if not stream.empty:
            if hasattr(self, "_min") and self._min > stream.buf:
                if not self.allow_late:
                    return

            if self._holes:
                idx = self._holes.pop()
            else:
                idx = max(self.streams, default=-1) + 1

            self.streams[idx] = stream

    def generate(self):
        while self.streams:
            idx, stream = min(self.streams.items(), key=self._key)

            self._min = stream.buf
            yield self._min

            stream.fetch()
            if stream.empty:
                del self.streams[idx]
                self._holes.add(idx)


class Buffer(object):

    """
    >>> buf = Buffer()
    """

    def __init__(self, items=None):
        self._data = deque(items or [])

    def add(self, item):
        self.data.append(item)

    def flush(self):
        items = list(self.data)
        self.data = deque()
        return items
