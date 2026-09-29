"""Pareto front over several objectives."""


# dominates reports whether a beats b on every objective and strictly wins on one.
def dominates(a, b, senses):
    better = False
    for left, right, sense in zip(a, b, senses):
        if sense * left < sense * right:
            return False
        if sense * left > sense * right:
            better = True
    return better


# pareto_front returns the indices of the points no other point dominates.
def pareto_front(points, senses):
    return [i for i, point in enumerate(points)
            if not any(dominates(other, point, senses)
                       for j, other in enumerate(points) if j != i)]
