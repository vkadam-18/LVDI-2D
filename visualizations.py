import plotly.express as px


# -------------------------------------------------
# Helper: detect dimension columns
# -------------------------------------------------
def get_dimension_columns(df, measure_col):
    """
    Returns non-measure columns (dimensions).
    For 1D tables: Returns only "Dimension Value" (not "Dimension Type")
    For 2D tables: Returns "Dimension1 Value" and "Dimension2 Value"
    """
    dims = []
    
    for c in df.columns:
        # Skip the specific measure column being used
        if c == measure_col:
            continue
        
        # Skip ALL columns that look like measures (contain years or metric keywords)
        if any(year in c for year in ["2023", "2024", "2025"]):
            continue
        
        if any(metric in c for metric in ["Avg Rate", "Count", "Matter", "Timekeeper"]):
            continue
        
        # Skip metadata columns
        if any(pattern in c for pattern in ["index", "Unnamed"]):
            continue
        
        # CRITICAL: Skip "Dimension Type" columns (they're metadata, not values)
        # Only keep "Dimension Value", "Dimension1 Value", "Dimension2 Value"
        if "Dimension Type" in c or "Dimension1 Type" in c or "Dimension2 Type" in c:
            continue
        
        # This is a dimension VALUE column
        dims.append(c)
    
    return dims


# -------------------------------------------------
# Main plotting router
# -------------------------------------------------
def plot_generic(df, measure_col, chart_type):
    """
    Generic plot function for:
    - bar (1D and 2D)
    - line (1D and 2D)
    - stacked_bar (2D)
    - grouped_bar (2D)
    - heatmap (2D)
    """

    dims = get_dimension_columns(df, measure_col)
    
    if len(dims) == 0:
        raise ValueError("No dimension columns found in dataframe")
    
    # Clean up measure column name for title
    measure_name = measure_col.replace(" Jun", "").replace(" Sep", "")

    # ---------------- 1D CHARTS ----------------
    if len(dims) == 1:
        if chart_type == "bar":
            fig = px.bar(
                df,
                x=dims[0],
                y=measure_col,
                text_auto=True,
                title=f"{measure_name}"
            )
            fig.update_layout(xaxis_title=dims[0].replace("Dimension Value", "Category"))
            fig.update_layout(yaxis_title=measure_name)
            return fig
            
        elif chart_type == "line":
            fig = px.line(
                df,
                x=dims[0],
                y=measure_col,
                markers=True,
                title=f"{measure_name} Trend"
            )
            fig.update_layout(xaxis_title=dims[0].replace("Dimension Value", "Category"))
            fig.update_layout(yaxis_title=measure_name)
            return fig
            
        elif chart_type == "donut":
            return px.pie(
                df,
                names=dims[0],
                values=measure_col,
                hole=0.4,
                title=f"{measure_name} Distribution"
            )
        else:
            raise ValueError(f"Unsupported chart type '{chart_type}' for 1D data")


    elif len(dims) == 2:
        
        dim1_label = dims[0].replace("Dimension1 Value", "Dimension 1").replace("Dimension Value", "Category")
        dim2_label = dims[1].replace("Dimension2 Value", "Dimension 2").replace("Dimension Value", "Category")
        
        if chart_type == "bar":
            
            fig = px.bar(
                df,
                x=dims[0],
                y=measure_col,
                color=dims[1],
                barmode="group",
                text_auto=True,
                title=f"{measure_name}"
            )
            fig.update_layout(xaxis_title=dim1_label)
            fig.update_layout(yaxis_title=measure_name)
            fig.update_layout(legend_title=dim2_label)
            return fig
        
        elif chart_type == "stacked_bar":
            fig = px.bar(
                df,
                x=dims[0],
                y=measure_col,
                color=dims[1],
                barmode="stack",
                text_auto=True,
                title=f"{measure_name} (Stacked)"
            )
            fig.update_layout(xaxis_title=dim1_label)
            fig.update_layout(yaxis_title=measure_name)
            fig.update_layout(legend_title=dim2_label)
            return fig
        
        elif chart_type == "grouped_bar":
            fig = px.bar(
                df,
                x=dims[0],
                y=measure_col,
                color=dims[1],
                barmode="group",
                text_auto=True,
                title=f"{measure_name} (Grouped)"
            )
            fig.update_layout(xaxis_title=dim1_label)
            fig.update_layout(yaxis_title=measure_name)
            fig.update_layout(legend_title=dim2_label)
            return fig
        
        elif chart_type == "line":
            fig = px.line(
                df,
                x=dims[0],
                y=measure_col,
                color=dims[1],
                markers=True,
                title=f"{measure_name} Trend"
            )
            fig.update_layout(xaxis_title=dim1_label)
            fig.update_layout(yaxis_title=measure_name)
            fig.update_layout(legend_title=dim2_label)
            return fig
        
        elif chart_type == "heatmap":
            # Create pivot table for heatmap
            pivot_df = df.pivot_table(
                index=dims[1],
                columns=dims[0],
                values=measure_col,
                aggfunc='mean'
            )
            fig = px.imshow(
                pivot_df,
                labels=dict(x=dim1_label, y=dim2_label, color=measure_name),
                aspect="auto",
                color_continuous_scale="Blues",
                title=f"{measure_name} Heatmap"
            )
            return fig
        
        elif chart_type == "donut":
            
            grouped = df.groupby(dims[0])[measure_col].sum().reset_index()
            return px.pie(
                grouped,
                names=dims[0],
                values=measure_col,
                hole=0.4,
                title=f"{measure_name} Distribution"
            )
        
        else:
            raise ValueError(f"Unsupported chart type '{chart_type}' for 2D data")

    else:
        raise ValueError(
            f"Expected 1 or 2 dimensions, found {len(dims)}. "
            f"Available dimensions: {dims}"
        )