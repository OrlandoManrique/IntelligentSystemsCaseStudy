import matplotlib.pyplot as plt
import matplotlib.patches as patches
import pandas as pd
import numpy as np
import os

# ==========================================
# 0. GLOBAL SETTINGS & SAVING UTILS
# ==========================================
_plot_sequence = 0
PLOT_FOLDER = 'plots'

def _save_and_show_plot(fig, tag):
    global _plot_sequence
    _plot_sequence += 1
    
    base_dir = os.getcwd()
    abs_plot_folder = os.path.join(base_dir, PLOT_FOLDER)
    
    if not os.path.exists(abs_plot_folder):
        try:
            os.makedirs(abs_plot_folder)
        except OSError:
            pass # Ignore if we can't create it
    
    clean_tag = tag.lower().replace(" ", "_").replace(":", "").replace("-", "_")
    filename = f"plot_{_plot_sequence:03d}_{clean_tag}.png"
    filepath = os.path.join(abs_plot_folder, filename)
    
    try:
        fig.savefig(filepath, bbox_inches='tight', dpi=150)
        print(f"[Visualizer] Plot saved to: {filepath}")
    except Exception as e:
        print(f"[Visualizer] Warning: Could not save plot. {e}")
    
    try: 
        manager = plt.get_current_fig_manager()
        if manager is not None:
            manager.window.showMaximized()
    except: 
        pass
        
    plt.show()

# ==========================================
# 1. DATA INTEGRATION & CLEAN STATISTICS
# ==========================================

def prepare_unified_dataframe(df_alloc, df_locations, df_items=None):
    # (Same logic as before, just compacting for brevity)
    if 'utilization' in df_alloc.columns:
        agg_dict = {'utilization': 'sum'}
        if 'SKU' in df_alloc.columns: agg_dict['SKU'] = 'first'
        df_alloc_grouped = df_alloc.groupby('LOCATION_ID', as_index=False).agg(agg_dict)
    else:
        df_alloc_grouped = df_alloc

    df = pd.merge(df_locations, df_alloc_grouped, left_on='loc_inst_code', right_on='LOCATION_ID', how='left')
    df['utilization'] = df['utilization'].fillna(0.0)
    
    if df_items is not None and 'SKU' in df.columns:
        df = pd.merge(df, df_items[['ITEM_ID', 'DEMAND']], left_on='SKU', right_on='ITEM_ID', how='left')
        df['DEMAND'] = df['DEMAND'].fillna(0)
    
    return df

def calculate_warehouse_stats(df):
    """
    Calculates Global Report metrics and returns them as native Python types
    (clean floats/ints) for pretty printing.
    """
    # 1. Calculate raw values
    mean_util = df['utilization'].mean() * 100
    total_density = df['utilization'].sum() / len(df) if len(df) > 0 else 0
    occupied_bins = df[df['utilization'] > 0].shape[0]
    total_bins = df.shape[0]
    
    stats = {
        "Mean Utilization": round(float(mean_util), 2),       # cast to float, round to 2
        "Total Density": round(float(total_density), 4),      # cast to float, round to 4
        "Occupied Bins": int(occupied_bins),                  # cast to standard int
        "Total Bins": int(total_bins)
    }
    
    # 2. Add Travel Cost if Demand exists
    if 'DEMAND' in df.columns:
        df['dist'] = df['x'].abs() + df['y'].abs() + df['z'].abs()
        total_cost = (df['dist'] * df['DEMAND']).sum()
        stats["Total Travel Cost"] = round(float(total_cost), 2)
        
    return stats

def print_stats_pretty(stats, title="Warehouse Report"):
    """
    Prints the stats dictionary in a clean, tabular format.
    """
    print(f"\n{'-'*10} {title} {'-'*10}")
    for key, value in stats.items():
        # Add % symbol for utilization
        if "Utilization" in key:
            print(f"{key:<20}: {value}%")
        # Add comma separators for large numbers (Cost)
        elif "Cost" in key:
            print(f"{key:<20}: {value:,.2f}")
        else:
            print(f"{key:<20}: {value}")
    print(f"{'-'*40}\n")

# ==========================================
# 2. VISUALIZATION SUITE (Colors & Plots)
# ==========================================
COLORS = {
    'low': '#2ecc71', 'med': '#f1c40f', 'high': '#e74c3c', 
    'empty': '#ecf0f1', 'border': '#2c3e50', 'text': '#333333'
}

def _get_traffic_light_color(percentage):
    if percentage <= 0: return COLORS['empty']
    if percentage < 0.50: return COLORS['low']
    elif percentage < 0.85: return COLORS['med']
    else: return COLORS['high']

def plot_top_view_heatmap(df):
    fig, ax = plt.subplots(figsize=(12, 10))
    ax.set_facecolor('white')
    
    df_footprint = df.drop_duplicates(subset=['x', 'y'])
    print(f"[Visualizer] Drawing Top View Heatmap for {len(df_footprint)} stacks.")
    
    for _, row in df_footprint.iterrows():
        stack_util = df[(df['x'] == row['x']) & (df['y'] == row['y'])]['utilization'].mean()
        rect = patches.Rectangle(
            (row['x'], row['y']), row['width'], row['depth'],
            linewidth=0.5, edgecolor=COLORS['border'], 
            facecolor=_get_traffic_light_color(stack_util), alpha=0.8
        )
        ax.add_patch(rect)
        
    ax.autoscale(); ax.set_aspect('equal'); ax.invert_yaxis()
    ax.set_title("Warehouse Top-Down Utilization Heatmap", fontsize=15)
    ax.set_xlabel("X (mm)"); ax.set_ylabel("Y (mm)")
    
    legend_patches = [
        patches.Patch(color=COLORS['low'], label='Low (<50%)'),
        patches.Patch(color=COLORS['med'], label='Med (<85%)'),
        patches.Patch(color=COLORS['high'], label='High (>85%)'),
        patches.Patch(color=COLORS['empty'], label='Empty')
    ]
    ax.legend(handles=legend_patches, title="Utilization", loc='upper right')
    _save_and_show_plot(fig, "top_view")

def plot_front_view(df, start_id, end_id):
    if 'utilization' not in df.columns: df['utilization'] = 0.0
    df_sorted = df.sort_values('loc_inst_code').reset_index(drop=True)
    
    try:
        idx_start = df_sorted[df_sorted['loc_inst_code'] == start_id].index[0]
        idx_end = df_sorted[df_sorted['loc_inst_code'] == end_id].index[0]
        if idx_start > idx_end: idx_start, idx_end = idx_end, idx_start
        subset = df_sorted.iloc[idx_start : idx_end+1]
    except IndexError:
        print(f"[Visualizer] Error: IDs {start_id} or {end_id} not found.")
        return

    target_stacks = subset[['x', 'y']].drop_duplicates()
    full_view_data = pd.merge(df, target_stacks, on=['x', 'y'], how='inner')
    
    if {'row_num', 'bay_num', 'level_num'}.issubset(full_view_data.columns):
        full_view_data = full_view_data.sort_values(by=['row_num', 'bay_num', 'level_num'])
    else:
        full_view_data = full_view_data.sort_values(by=['loc_inst_code', 'z'])

    fig, ax = plt.subplots(figsize=(14, 7))
    ax.set_facecolor('white')
    
    grouped_stacks = full_view_data.groupby(['x', 'y'], sort=False)
    cursor_x = 0; VISUAL_GAP = 50; max_h = 0
    print(f"[Visualizer] Drawing Front View for {len(grouped_stacks)} rack columns.")

    for _, stack_df in grouped_stacks:
        w = stack_df.iloc[0]['width']
        for _, loc in stack_df.iterrows():
            h, z, util = loc['height'], loc['z'], loc['utilization']
            ax.add_patch(patches.Rectangle((cursor_x, z), w, h, fill=True, facecolor='white', edgecolor=COLORS['border'], linewidth=1))
            if util > 0:
                ax.add_patch(patches.Rectangle((cursor_x, z), w, h * util, facecolor=_get_traffic_light_color(util), alpha=0.9))
            if h > 50 and w > 50:
                lvl = int(loc['level_num']) if 'level_num' in loc else '?'
                ax.text(cursor_x + w/2, z + h/2, f"L{lvl}", ha='center', va='center', fontsize=8, color=COLORS['text'], alpha=0.5)

        top_z = stack_df['z'].max() + stack_df['height'].max()
        if top_z > max_h: max_h = top_z
        cursor_x += (w + VISUAL_GAP)

    ax.set_xlim(-100, cursor_x + 100); ax.set_ylim(0, max_h + 200)
    ax.set_aspect('equal')
    ax.set_title(f"Front View Elevation: {start_id} to {end_id}", fontsize=14)
    ax.set_xlabel("Sequence"); ax.set_ylabel("Elevation (mm)")
    _save_and_show_plot(fig, "front_view")