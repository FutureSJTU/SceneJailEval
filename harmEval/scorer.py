def weighted_score(scores, weights):
    total = 0
    for dim, score in scores.items():
        w = weights.get(dim, 0)
        if score is not None:
            total += score * w
    return round(total, 2)
