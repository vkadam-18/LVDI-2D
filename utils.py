def resolve_measure_column(df, year, metric, version):
    expected = f"{year} {metric} {version}"

    if expected in df.columns:
        return expected

    # fallback safety
    for c in df.columns:
        if year in c and metric.lower() in c.lower():
            return c

    return None
