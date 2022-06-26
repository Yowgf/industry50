def get_eqseparated_val(key, s):
    split_by_eq = s.split("=")
    if len(split_by_eq) < 2:
        raise ValueError(key, f"must be a '='-separated string. "+
                                 f"Got: {s}")
    return split_by_eq[1]
