import matplotlib.pyplot as plt
import matplotlib.patches as patches
import pandas as pd
import numpy as np

# ==========================================
# 1. CONFIGURATION & STYLING
# ==========================================
COLORS = {
    'low': '#2ecc71',    # Green
    'med': '#f1c40f',    # Yellow/Orange
    'high': '#e74c3c',   # Red
    'empty': '#ecf0f1',  # Light Gray (Used for empty bins/backgrounds)
    'border': '#2c3e50', # Dark Blue/Black
    'text': '#333333'
}

def _get_traffic_light_color(percentage):
    """
    Returns a color hex code based on utilization percentage.
    """
    if percentage <= 0: return COLORS['empty']
    if percentage < 0.50: return COLORS['low']
    elif percentage < 0.85: return COLORS['med']
    else: return COLORS['high']

# ==========================================
# 2. DATA INTEGRATION & STATISTICS
# ==========================================

def prepare_unified_dataframe(df_alloc, df_locations, df_items=None):
    """
    Standardizes and merges data sources.
    df_alloc: Must have ['LOCATION_ID', 'utilization'] (plus 'SKU' if using items)
    df_locations: Must have ['loc_inst_code', 'x', 'y', 'z', 'width', 'depth', 'height']
    """
    # Merge Allocation result onto the physical Location master
    df = pd.merge(
        df_locations, 
        df_alloc[['LOCATION_ID', 'SKU', 'utilization']], 
        left_on='loc_inst_code', 
        right_on='LOCATION_ID', 
        how='left'
    )
    
    # Fill empty bins with 0 utilization
    df['utilization'] = df['utilization'].fillna(0.0)
    
    # Merge with Items for Demand (used in Travel Cost stats) if provided
    if df_items is not None and 'SKU' in df.columns:
        df = pd.merge(df, df_items[['ITEM_ID', 'DEMAND']], left_on='SKU', right_on='ITEM_ID', how='left')
        df['DEMAND'] = df['DEMAND'].fillna(0)
    
    return df

def calculate_warehouse_stats(df):
    """Calculates Global Report metrics."""
    stats = {
        "Mean_Utilization_%": df['utilization'].mean() * 100,
        "Total_Density": df['utilization'].sum() / len(df) if len(df) > 0 else 0,
        "Occupied_Bins": df[df['utilization'] > 0].shape[0],
        "Total_Bins": df.shape[0]
    }
    
    # Simple Manhattan Distance to (0,0,0) calculation
    if 'DEMAND' in df.columns:
        df['dist'] = df['x'].abs() + df['y'].abs() + df['z'].abs()
        stats["Total_Travel_Cost"] = (df['dist'] * df['DEMAND']).sum()
        
    return stats

# ==========================================
# 3. VISUALIZATION SUITE
# ==========================================

def plot_top_view_heatmap(df):
    """
    Plots the Top-Down footprint. Colors are based on average utilization per stack.
    Matches the style of the Front View.
    """
    # Create Figure
    fig, ax = plt.subplots(figsize=(12, 10))
    ax.set_facecolor('white')
    
    # 1. Optimization: Drop duplicates to identify unique X/Y stacks
    # We use this to draw the footprint only once per stack
    df_footprint = df.drop_duplicates(subset=['x', 'y'])
    
    print(f"[Visualizer] Drawing Top View Heatmap for {len(df_footprint)} stacks.")
    
    for _, row in df_footprint.iterrows():
        # Get average utilization for this specific vertical stack (all Z levels at this X,Y)
        stack_util = df[(df['x'] == row['x']) & (df['y'] == row['y'])]['utilization'].mean()
        
        # Draw Rectangle
        rect = patches.Rectangle(
            (row['x'], row['y']), 
            row['width'], 
            row['depth'],
            linewidth=0.5, 
            edgecolor=COLORS['border'], 
            facecolor=_get_traffic_light_color(stack_util), # Utilization determines color
            alpha=0.8
        )
        ax.add_patch(rect)
        
    # 2. Axis Setup & Style
    ax.autoscale()
    ax.set_aspect('equal')
    ax.invert_yaxis() # Standard Warehouse View (North often Up/Down depending on coord system)
    
    ax.set_title("Warehouse Top-Down Utilization Heatmap", fontsize=15)
    ax.set_xlabel("X Coordinate (mm)")
    ax.set_ylabel("Y Coordinate (mm)")
    
    # 3. Create Custom Legend
    legend_patches = [
        patches.Patch(color=COLORS['low'], label='Low (<50%)'),
        patches.Patch(color=COLORS['med'], label='Med (<85%)'),
        patches.Patch(color=COLORS['high'], label='High (>85%)'),
        patches.Patch(color=COLORS['empty'], label='Empty')
    ]
    ax.legend(handles=legend_patches, title="Utilization", loc='upper right')
    
    # Maximize window
    try: plt.get_current_fig_manager().window.showMaximized()
    except: pass
    
    plt.show()

def plot_front_view(df, start_id, end_id):
    """
    Plots the Elevation View (Front View) for a range of locations.
    Shows inventory levels as a "Liquid Fill" matching the Top View colors.
    """
    # 1. Validation
    if 'utilization' not in df.columns:
        print("[Visualizer] Warning: 'utilization' column missing. Assuming 0%.")
        df['utilization'] = 0.0

    # Sort by ID to find the range
    df_sorted = df.sort_values('loc_inst_code').reset_index(drop=True)
    
    try:
        # Find indices
        idx_start = df_sorted[df_sorted['loc_inst_code'] == start_id].index[0]
        idx_end = df_sorted[df_sorted['loc_inst_code'] == end_id].index[0]
        
        # Ensure correct order
        if idx_start > idx_end: 
            idx_start, idx_end = idx_end, idx_start
            
        subset = df_sorted.iloc[idx_start : idx_end+1]
        
    except IndexError:
        print(f"[Visualizer] Error: IDs {start_id} or {end_id} not found.")
        return

    # 2. Expand to full stacks (if user picked Level 1, we must show Level 2, 3 etc above it)
    target_stacks = subset[['x', 'y']].drop_duplicates()
    full_view_data = pd.merge(df, target_stacks, on=['x', 'y'], how='inner')
    
    # Sort for plotting order (Left to Right, Bottom to Top)
    if {'row_num', 'bay_num', 'level_num'}.issubset(full_view_data.columns):
        full_view_data = full_view_data.sort_values(by=['row_num', 'bay_num', 'level_num'])
    else:
        full_view_data = full_view_data.sort_values(by=['loc_inst_code', 'z'])

    # 3. Plotting
    fig, ax = plt.subplots(figsize=(14, 7))
    ax.set_facecolor('white')
    
    grouped_stacks = full_view_data.groupby(['x', 'y'], sort=False)
    
    cursor_x = 0
    VISUAL_GAP = 50 # mm spacing between racks
    max_h = 0
    
    print(f"[Visualizer] Drawing Front View for {len(grouped_stacks)} rack columns.")

    for _, stack_df in grouped_stacks:
        w = stack_df.iloc[0]['width']
        
        for _, loc in stack_df.iterrows():
            h, z = loc['height'], loc['z']
            util = loc['utilization']
            
            # A. Draw The Bin Frame (Empty)
            ax.add_patch(patches.Rectangle(
                (cursor_x, z), w, h, 
                fill=True, facecolor='white', # White background inside bin
                edgecolor=COLORS['border'], linewidth=1
            ))
            
            # B. Draw The Inventory (Liquid Fill)
            if util > 0:
                fill_height = h * util
                fill_color = _get_traffic_light_color(util)
                ax.add_patch(patches.Rectangle(
                    (cursor_x, z), w, fill_height, 
                    facecolor=fill_color, alpha=0.9, edgecolor=None
                ))
            
            # C. Labels
            if h > 50 and w > 50:
                lvl = int(loc['level_num']) if 'level_num' in loc else '?'
                text_col = COLORS['text']
                ax.text(cursor_x + w/2, z + h/2, f"L{lvl}", 
                        ha='center', va='center', fontsize=8, color=text_col, alpha=0.5)

        top_z = stack_df['z'].max() + stack_df['height'].max()
        if top_z > max_h: max_h = top_z
        cursor_x += (w + VISUAL_GAP)

    # 4. Final Polish
    ax.set_xlim(-100, cursor_x + 100)
    ax.set_ylim(0, max_h + 200)
    ax.set_aspect('equal')
    ax.set_title(f"Front View Elevation: {start_id} to {end_id}", fontsize=14)
    ax.set_xlabel("Walking Path Sequence")
    ax.set_ylabel("Elevation (mm)")

    try: plt.get_current_fig_manager().window.showMaximized()
    except: pass
    
    plt.show()