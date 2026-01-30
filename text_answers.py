import re
from difflib import SequenceMatcher
from utils import resolve_measure_column

def normalize(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", s.lower())


def best_match(values_series, target_value):
    """
    Find the best matching value in a series.
    Uses fuzzy matching to handle variations like:
    - "healthcare" vs "Health Care"
    - "tech" vs "Technology"
    """
    target = normalize(target_value)
    
    best_value = None
    best_score = 0
    
    for val in values_series:
        val_str = str(val)
        candidate = normalize(val_str)
        
        # Calculate similarity score
        score = SequenceMatcher(None, candidate, target).ratio()
        
        # Bonus: if target is contained in candidate (e.g., "health" in "healthcare")
        if target in candidate or candidate in target:
            score = max(score, 0.85)
        
        if score > best_score:
            best_score = score
            best_value = val_str
    
    # Accept matches with 60% or higher confidence (lowered from 70%)
    if best_score >= 0.6:
        return best_value
    
    return None


def generate_text_answer(df, intent, version):
    """
    Generate answer for 1D tables
    """
    year = intent.get("year")
    metric = intent.get("metric")
    filter_values = intent.get("filter_values", {})
    
    if not year or not metric:
        return "⚠️ Please specify year and metric."
    
    # Get the dimension VALUE column (where actual data is)
    # Look for columns like "Dimension Value", "Industry", "Practice Area", etc.
    dim_col = None
    
    # Priority 1: Look for "Dimension Value" column (common pattern)
    for col in df.columns:
        if "Dimension Value" in col:
            dim_col = col
            break
    
    # Priority 2: Look for first column that isn't metadata or measures
    if not dim_col:
        for col in df.columns:
            col_lower = col.lower()
            # Skip metadata columns
            if any(x in col_lower for x in ["dimension type", "type", "index", "unnamed"]):
                continue
            # Skip measure columns (contain year or metric keywords)
            if any(x in col for x in ["2023", "2024", "2025", "Avg Rate", "Count", "Matter"]):
                continue
            dim_col = col
            break
    
    if not dim_col:
        return f"⚠️ No dimension column found. Available columns: {list(df.columns)}"
    
    filtered_df = df.copy()
    
    # Apply filter if provided - search in the DIMENSION column
    applied_filters = []
    for dim_name, filter_val in filter_values.items():
        if filter_val:
            matched_val = best_match(filtered_df[dim_col], filter_val)
            
            if matched_val is None:
                # Show available values to help user
                available_values = filtered_df[dim_col].unique()[:5]  # Show first 5
                return f"⚠️ No data found for `{filter_val}` in {dim_col}. Available values include: {list(available_values)}"
            
            filtered_df = filtered_df[filtered_df[dim_col] == matched_val]
            applied_filters.append(f"{matched_val}")
    
    if filtered_df.empty:
        return "⚠️ No data found for the selected filters."
    
    # NOW get the measure column
    measure_col = resolve_measure_column(filtered_df, year, metric, version)
    if not measure_col:
        available_measures = [c for c in df.columns if any(y in c for y in ["2023", "2024", "2025"])]
        return f"⚠️ Measure `{year} {metric}` not available. Available columns: {available_measures}"
    
    value = round(filtered_df[measure_col].mean(), 2)
    
    if applied_filters:
        filter_text = " × ".join(applied_filters)
        return (
            f"📊 **{year} {metric}** for **{filter_text}** "
            f"({version}) is **{value}**."
        )
    else:
        return (
            f"📊 **{year} {metric}** overall average "
            f"({version}) is **{value}**."
        )


def generate_2d_text_answer(df, intent, version):
    """
    Generate answer for 2D tables
    """
    year = intent.get("year")
    metric = intent.get("metric")
    filter_values = intent.get("filter_values", {})
    
    if not year or not metric:
        return "⚠️ Please specify year and metric."
    
    # Get dimension VALUE columns (where actual data is)
    # Look for patterns like "Dimension1 Value", "Dimension2 Value" or just regular dimension columns
    dim_cols = []
    
    # Priority 1: Look for "Dimension X Value" columns
    for i in [1, 2]:
        for col in df.columns:
            if f"Dimension{i} Value" in col or f"Dimension {i} Value" in col:
                dim_cols.append(col)
                break
    
    # Priority 2: Look for first two non-metadata, non-measure columns
    if len(dim_cols) < 2:
        dim_cols = []
        for col in df.columns:
            col_lower = col.lower()
            # Skip metadata columns
            if any(x in col_lower for x in ["dimension type", "dimension1 type", "dimension2 type", "type", "index", "unnamed"]):
                continue
            # Skip measure columns
            if any(x in col for x in ["2023", "2024", "2025", "Avg Rate", "Count", "Matter"]):
                continue
            dim_cols.append(col)
            if len(dim_cols) == 2:
                break
    
    if len(dim_cols) < 2:
        return f"⚠️ Expected 2 dimension columns, found {len(dim_cols)}. Columns: {list(df.columns)}"
    
    dim1_col, dim2_col = dim_cols[0], dim_cols[1]
    
    filtered_df = df.copy()
    applied_filters = []
    
    # Apply filters for both dimensions
    for key, val in filter_values.items():
        if val:
            # Try to match against dim1
            matched = best_match(filtered_df[dim1_col], val)
            if matched:
                filtered_df = filtered_df[filtered_df[dim1_col] == matched]
                applied_filters.append(matched)
                continue
            
            # Try to match against dim2
            matched = best_match(filtered_df[dim2_col], val)
            if matched:
                filtered_df = filtered_df[filtered_df[dim2_col] == matched]
                applied_filters.append(matched)
    
    if filtered_df.empty:
        return "⚠️ No matching data found for the specified filters."
    
    # NOW get the measure column
    measure_col = resolve_measure_column(filtered_df, year, metric, version)
    if not measure_col:
        available_measures = [c for c in df.columns if any(y in c for y in ["2023", "2024", "2025"])]
        return f"⚠️ `{year} {metric}` not available. Available columns: {available_measures}"
    
    value = round(filtered_df[measure_col].mean(), 2)
    
    if applied_filters:
        filter_text = " × ".join(applied_filters)
        return (
            f"📊 **{year} {metric}** for **{filter_text}** "
            f"({version}) is **{value}**."
        )
    else:
        return (
            f"📊 **{year} {metric}** overall average "
            f"({version}) is **{value}**."
        )