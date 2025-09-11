import time
from states.shorts_state import ShortsState

def timed_node(func):
    def wrapper(state: ShortsState) -> ShortsState:
        start_time = time.perf_counter()
        result = func(state)
        end_time = time.perf_counter()
        duration = (end_time - start_time) * 1000 # ms단위
        print(f"{func.__name__} took {duration:.2f} ms")
        return result
    return wrapper