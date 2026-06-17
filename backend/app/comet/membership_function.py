def validate_triangular_params(a: float, b: float, c: float) -> None:
    if not (a <= b <= c):
        raise ValueError("Invalid parameters: a <= b <= c must hold.")

    if a == b == c:
        raise ValueError("Invalid parameters: a, b, and c can't all be equal.")


def triangular_membership(x: float, a: float, b: float, c: float) -> float:
    validate_triangular_params(a, b, c)

    if a == b: 
        if x <= a:
            return 1.0
        elif x >= c:
            return 0.0
        else:
            return (c - x) / (c - a)
    elif b == c:
        if x <= a:
            return 0.0
        elif x >= c:
            return 1.0
        else:
            return (x - a) / (c - a)

    if x <= a or x >= c:
        return 0.0
    elif x == b:
        return 1.0
    elif x < b:
        return (x - a) / (b - a)
    else:
        return (c - x) / (c - b)