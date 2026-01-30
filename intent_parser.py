def parse_intent(query: str):
    q = query.lower()

    # -------- Chart detection --------
    chart = None
    if any(k in q for k in ["plot", "chart", "graph", "show"]):
        chart = "bar"
    if "pie" in q or "donut" in q:
        chart = "donut"
    if "line" in q:
        chart = "line"
    if "heat" in q:
        chart = "heatmap"
    if "stack" in q:
        chart = "stacked_bar"

    # -------- Year detection --------
    year = None
    for y in ["2023", "2024", "2025"]:
        if y in q:
            year = y
            break

    # -------- Dimension detection (FIXED) --------
    # Use more specific matching to avoid false positives
    dimension_map = {
        "detailed practice area": "detailed_practice_area",  # Check this first (more specific)
        "practice area": "practice_area",
        "practice": "practice_area",
        "years of experience": "years_of_experience",
        "experience": "years_of_experience",
        "amlaw bucket": "amlaw_bucket",
        "amlaw": "amlaw_bucket",
        "firm size": "firm_size",
        "matter type": "matter_type",
        "industry": "industry",
        "role": "role",
        "city": "city",
        "country": "country",
    }

    detected_dims = []
    matched_phrases = []  # Track what we've matched to avoid duplicates
    
    # Sort by length (longest first) to match more specific phrases first
    sorted_keys = sorted(dimension_map.keys(), key=len, reverse=True)
    
    for k in sorted_keys:
        if k in q and k not in matched_phrases:
            v = dimension_map[k]
            if v not in detected_dims:  # Avoid duplicate dimensions
                detected_dims.append(v)
                matched_phrases.append(k)
            
            # Stop at 2 dimensions
            if len(detected_dims) >= 2:
                break

    # -------- Metric detection --------
    if "matter count" in q or ("matter" in q and "count" in q):
        metric = "Matter Count"
    elif "timekeeper" in q or ("timekeeper" not in q and "count" in q):
        metric = "Timekeeper Count"
    else:
        metric = "Avg Rate"

    return {
        "chart": chart,
        "dimensions": detected_dims[:2],  # max 2
        "year": year,
        "metric": metric
    }