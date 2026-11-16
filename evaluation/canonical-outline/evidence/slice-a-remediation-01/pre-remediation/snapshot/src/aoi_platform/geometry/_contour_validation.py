"""Private traversal only: strategies own numerical semantics and failures.

The edge/previous-pair interleaving is part of legacy error precedence.
"""


def validate_contour(count, strategy):
    for i in range(count):
        strategy.edge(i)
        for j in range(i):
            strategy.pair(i, j)
    return strategy.finish()
