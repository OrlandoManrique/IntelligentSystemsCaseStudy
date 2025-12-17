import matplotlib.pyplot as plt
import matplotlib.patches as patches
import pandas as pd
import numpy as np

# ==========================================
# CONFIGURATION
# ==========================================
COLORS = {
    'low': '#2ecc71',    # Green
    'med': '#f1c40f',    # Orange/Yellow
    'high': '#e74c3c',   # Red
    'empty': 'none',     # Transparent
    'border': 'black'
}

def _get_traffic_light_color(percentage):
    if percentage < 0.50: return COLORS['low']
    elif percentage < 0.85: return COLORS['med']
    else: return COLORS['high']

def plot_top_view(df_locations):
    """
    Plots the Top-Down footprint of the warehouse.
    
    Args:
        df_locations (pd.DataFrame): Must contain 'x', 'y', 'width', 'depth', 'loc_type'.
    """
    # Create Figure
    fig, ax = plt.subplots(figsize=(12, 10))
    ax.set_facecolor('white')
    
    # Optimization: Draw only the footprint (Z=0) to prevent lag
    # We drop duplicates on X/Y so we don't draw 5 rectangles on top of each other
    df_footprint = df_locations.drop_duplicates(subset=['x', 'y', 'loc_type'])
    
    # Dynamic Color Map for Location Types
    unique_types = df_locations['loc_type'].unique()
    # Use standard matplotlib colormap
    colors = plt.cm.get_cmap('tab10', len(unique_types))
    type_map = {t: colors(i) for i, t in enumerate(unique_types)}

    print(f"[Visualizer] Drawing Top View with {len(df_footprint)} stacks.")
    
    for _, row in df_footprint.iterrows():
        rect = patches.Rectangle(
            (row['x'], row['y']), 
            row['width'], 
            row['depth'],
            linewidth=0.5, 
            edgecolor=COLORS['border'], 
            facecolor=type_map.get(row['loc_type'], 'gray'), 
            alpha=0.7
        )
        ax.add_patch(rect)
        
    # Axis Setup
    ax.autoscale()
    ax.set_aspect('equal')
    ax.invert_yaxis() # Standard Warehouse View (North Up)
    ax.set_title("Warehouse Top View Map", fontsize=15)
    ax.set_xlabel("X Coordinate (mm)")
    ax.set_ylabel("Y Coordinate (mm)")
    
    # Legend
    handles = [patches.Patch(color=type_map[t], label=t) for t in unique_types]
    ax.legend(handles=handles, title="Rack Types", loc='upper right')
    
    # Try to maximize window
    try: plt.get_current_fig_manager().window.showMaximized()
    except: pass
    
    plt.show()

def plot_front_view(df_locations, start_id, end_id):
    """
    Plots the Elevation View (Front View) for a specific range of locations.
    Shows inventory levels as a "liquid fill".
    
    Args:
        df_locations (pd.DataFrame): Must contain 'x','y','z','width','height','level_num'
                                     AND 'utilization' (0.0 to 1.0).
        start_id (str): The starting LOC_INST_CODE (e.g. 'A1-00001').
        end_id (str): The ending LOC_INST_CODE.
    """
    # 1. Validation & Filtering
    if 'utilization' not in df_locations.columns:
        print("[Visualizer] Warning: 'utilization' column missing. Assuming 0%.")
        df_locations['utilization'] = 0.0

    # Sort to ensure we can slice the range correctly
    df_sorted = df_locations.sort_values('loc_inst_code').reset_index(drop=True)
    
    try:
        # Find the indices of the requested range
        idx_start = df_sorted[df_sorted['loc_inst_code'] == start_id].index[0]
        idx_end = df_sorted[df_sorted['loc_inst_code'] == end_id].index[0]
        
        # Ensure correct order
        if idx_start > idx_end: 
            idx_start, idx_end = idx_end, idx_start
            
        subset = df_sorted.iloc[idx_start : idx_end+1]
        
    except IndexError:
        print(f"[Visualizer] Error: IDs {start_id} or {end_id} not found in data.")
        return

    # 2. Expansion Logic
    # We must grab the FULL vertical stack for every location in the range.
    # (e.g., if user selects Level 1, we must also draw Level 2, 3, 4 above it)
    target_stacks = subset[['x', 'y']].drop_duplicates()
    full_view_data = pd.merge(df_locations, target_stacks, on=['x', 'y'], how='inner')
    
    # Sort by Logical Address (Row -> Bay -> Level) for correct Left-to-Right plotting
    if {'row_num', 'bay_num', 'level_num'}.issubset(full_view_data.columns):
        full_view_data = full_view_data.sort_values(by=['row_num', 'bay_num', 'level_num'])
    else:
        # Fallback if semantic columns are missing
        full_view_data = full_view_data.sort_values(by=['loc_inst_code', 'z'])

    # 3. Plotting Loop
    fig, ax = plt.subplots(figsize=(14, 7))
    ax.set_facecolor('white')
    
    # Group by (X, Y) to process one rack column at a time
    grouped_stacks = full_view_data.groupby(['x', 'y'], sort=False)
    
    cursor_x = 0
    VISUAL_GAP = 50 # mm spacing between racks in the plot
    max_h = 0
    
    print(f"[Visualizer] Drawing Front View for {len(grouped_stacks)} rack columns.")

    for _, stack_df in grouped_stacks:
        # Width is constant for a stack
        w = stack_df.iloc[0]['width']
        
        for _, loc in stack_df.iterrows():
            h, z = loc['height'], loc['z']
            util = loc['utilization']
            
            # A. Draw The Rack Slot (Empty Border)
            ax.add_patch(patches.Rectangle(
                (cursor_x, z), w, h, 
                fill=False, edgecolor=COLORS['border'], linewidth=1
            ))
            
            # B. Draw The Inventory (Liquid Fill)
            if util > 0:
                fill_height = h * util
                fill_color = _get_traffic_light_color(util)
                ax.add_patch(patches.Rectangle(
                    (cursor_x, z), w, fill_height, 
                    facecolor=fill_color, alpha=0.9, edgecolor=None
                ))
            
            # C. Draw Level Label (e.g. "L1")
            if h > 50 and w > 50:
                lvl = int(loc['level_num']) if 'level_num' in loc else '?'
                ax.text(cursor_x + w/2, z + h/2, f"L{lvl}", 
                        ha='center', va='center', fontsize=7, color='#333')

        # Update max height for plot limits
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