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
    """
    Saves the plot with a sequential ID and displays it.
    """
    global _plot_sequence
    _plot_sequence += 1
    
    base_dir = os.getcwd()
    abs_plot_folder = os.path.join(base_dir, PLOT_FOLDER)
    
    if not os.path.exists(abs_plot_folder):
        try: os.makedirs(abs_plot_folder)
        except OSError: pass
    
    # Clean tag for filename
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
        if manager is not None: manager.window.showMaximized()
    except: pass
    plt.show()

# ==========================================
# 1. DATA PREPARATION & LOGIC ENGINE
# ==========================================

def _clean_allocation_data(df_alloc):
    """
    Standardizes column names and formats from raw input.
    """
    df = df_alloc.copy()
    
    # 1. Normalize Column Names
    rename_map = {
        'LOC_CODE': 'LOCATION_ID',
        'ITEM_ID': 'SKU',
        'UTILIZATION_PCT': 'utilization',
        'QTY_ALLOCATED': 'QTY'
    }
    df.rename(columns=rename_map, inplace=True)
    
    # 2. Normalize Utilization (0-100 -> 0.0-1.0)
    # Heuristic: If max value > 1.1, assume it's percentage
    if 'utilization' in df.columns:
        if df['utilization'].max() > 1.1:
            df['utilization'] = df['utilization'] / 100.0
            
    # 3. Remove Failed Allocations
    if 'LOCATION_ID' in df.columns:
        df = df[df['LOCATION_ID'] != 'UNFIT']
        
    return df

def _apply_abc_classification(df):
    if 'DEMAND' not in df.columns:
        df['ABC_Class'] = 'C'
        return df

    unique_items = df[['SKU', 'DEMAND']].drop_duplicates().sort_values(by='DEMAND', ascending=False)
    if len(unique_items) == 0:
        df['ABC_Class'] = 'C'; return df

    idx_a = int(len(unique_items) * 0.20)
    idx_b = int(len(unique_items) * 0.50)

    skus_a = set(unique_items.iloc[:idx_a]['SKU'])
    skus_b = set(unique_items.iloc[idx_a:idx_b]['SKU'])
    
    def get_class(sku):
        if pd.isna(sku): return 'Empty'
        if sku in skus_a: return 'A'
        if sku in skus_b: return 'B'
        return 'C'

    df['ABC_Class'] = df['SKU'].apply(get_class)
    return df

def _calculate_pick_score(df):
    # 1. Horizontal: Closer to Bay 1/X=0 is better
    if 'bay_num' in df.columns:
        max_bay = df['bay_num'].max()
        df['score_horizontal'] = 1 - (df['bay_num'] / max_bay) if max_bay > 0 else 0
    else:
        max_x = df['x'].max()
        df['score_horizontal'] = 1 - (df['x'] / max_x) if max_x > 0 else 0
        
    # 2. Vertical: Golden Zone (700-1500mm)
    df['in_golden_zone'] = df['z'].between(700, 1500)
    df['score_vertical'] = df['in_golden_zone'].astype(float)
    
    # 3. Composite (60% Travel, 40% Ergo)
    df['pick_score'] = (df['score_horizontal'] * 60) + (df['score_vertical'] * 40)
    return df

def prepare_unified_dataframe(df_alloc_raw, df_locations, df_items=None):
    # 1. Clean Allocations
    df_alloc = _clean_allocation_data(df_alloc_raw)
    
    # 2. Aggregation (Handle multiple items per bin)
    if 'utilization' in df_alloc.columns:
        agg_dict = {'utilization': 'sum'}
        if 'SKU' in df_alloc.columns: agg_dict['SKU'] = 'first'
        df_alloc_grouped = df_alloc.groupby('LOCATION_ID', as_index=False).agg(agg_dict)
    else:
        df_alloc_grouped = df_alloc

    # 3. Merge with Locations
    df = pd.merge(df_locations, df_alloc_grouped, left_on='loc_inst_code', right_on='LOCATION_ID', how='left')
    df['utilization'] = df['utilization'].fillna(0.0)
    
    # 4. Merge with Items (Demand, Weight)
    if df_items is not None and 'SKU' in df.columns:
        # Handle Items file columns
        items_clean = df_items.copy()
        if 'ITEM_ID' in items_clean.columns: 
            # Ensure merge keys match
            pass 
        
        df = pd.merge(df, items_clean[['ITEM_ID', 'DEMAND', 'WT_KG']], left_on='SKU', right_on='ITEM_ID', how='left')
        df['DEMAND'] = df['DEMAND'].fillna(0)
        df['WT_KG'] = df['WT_KG'].fillna(0)
    else:
        df['DEMAND'] = 0; df['WT_KG'] = 0

    # 5. Logic Engine (ABC, Zones, Scores)
    df = _apply_abc_classification(df)
    df['is_heavy'] = df['WT_KG'] > 15.0
    df['is_golden_height'] = df['z'].between(700, 1500)
    
    if 'bay_num' in df.columns:
        df['is_target_bay'] = df['bay_num'] <= (df['bay_num'].max() * 0.25)
    else:
        df['is_target_bay'] = False

    df = _calculate_pick_score(df)
    return df

# ==========================================
# 2. STATISTICS
# ==========================================

def calculate_warehouse_stats(df):
    occupied_df = df[df['utilization'] > 0]
    
    # Avg Util of OCCUPIED bins
    avg_util = occupied_df['utilization'].mean() * 100 if not occupied_df.empty else 0.0
    density = df['utilization'].sum() / len(df) if len(df) > 0 else 0
    
    # Violations
    weight_vios = occupied_df[(occupied_df['is_heavy']) & (occupied_df['z'] > 1500)].shape[0]
    misplaced_a = occupied_df[
        (occupied_df['ABC_Class'] == 'A') & 
        (~(occupied_df['is_target_bay'] & occupied_df['is_golden_height']))
    ].shape[0]

    stats = {
        "Avg Util (Occupied)": round(avg_util, 2),
        "Global Density": round(density, 4),
        "Occupied Bins": len(occupied_df),
        "Total Bins": len(df),
        "Weight Violations": weight_vios,
        "Misplaced A-Items": misplaced_a
    }
    
    if 'DEMAND' in df.columns:
        df['dist'] = df['x'].abs() + df['y'].abs() + df['z'].abs()
        stats["Total Travel Cost"] = round((df['dist'] * df['DEMAND']).sum(), 2)
        
    return stats

def _print_stats(stats, title):
    print(f"\n{'-'*10} {title} {'-'*10}")
    for k, v in stats.items():
        if "Violations" in k or "Misplaced" in k:
            print(f"{k:<25}: {v} {'(!)' if v > 0 else '(OK)'}")
        elif "Util" in k:
            print(f"{k:<25}: {v}%")
        elif "Cost" in k:
            print(f"{k:<25}: {v:,.2f}")
        else:
            print(f"{k:<25}: {v}")
    print(f"{'-'*45}\n")

# ==========================================
# 3. VISUALIZATION FUNCTIONS
# ==========================================
COLORS = {
    'low': '#2ecc71', 'med': '#f1c40f', 'high': '#e74c3c', 
    'empty': '#ecf0f1', 'border': '#2c3e50', 'text': '#333333',
    'A': '#e74c3c', 'B': '#f1c40f', 'C': '#3498db'
}

def _get_color(pct):
    if pct <= 0: return COLORS['empty']
    if pct < 0.5: return COLORS['low']
    elif pct < 0.85: return COLORS['med']
    else: return COLORS['high']

def _plot_top(df, title_suffix):
    fig, ax = plt.subplots(figsize=(12, 10)); ax.set_facecolor('white')
    df_foot = df.drop_duplicates(subset=['x', 'y'])
    
    for _, row in df_foot.iterrows():
        u = df[(df['x']==row['x']) & (df['y']==row['y'])]['utilization'].mean()
        ax.add_patch(patches.Rectangle((row['x'], row['y']), row['width'], row['depth'], 
                     linewidth=0.5, edgecolor=COLORS['border'], facecolor=_get_color(u), alpha=0.8))
        
    ax.autoscale(); ax.set_aspect('equal'); ax.invert_yaxis()
    ax.set_title(f"Top-Down Heatmap: {title_suffix}", fontsize=14)
    _save_and_show_plot(fig, f"top_view_{title_suffix}")

def _plot_front(df, title_suffix):
    s_id, e_id = df['loc_inst_code'].min(), df['loc_inst_code'].max()
    # Sort
    df_s = df.sort_values('loc_inst_code').reset_index(drop=True)
    try:
        idx_s = df_s[df_s['loc_inst_code'] == s_id].index[0]
        idx_e = df_s[df_s['loc_inst_code'] == e_id].index[0]
        if idx_s > idx_e: idx_s, idx_e = idx_e, idx_s
        subset = df_s.iloc[idx_s:idx_e+1]
    except: return

    target = subset[['x', 'y']].drop_duplicates()
    data = pd.merge(df, target, on=['x', 'y'], how='inner')
    if {'row_num','bay_num','level_num'}.issubset(data.columns):
        data = data.sort_values(['row_num','bay_num','level_num'])
    else: data = data.sort_values(['loc_inst_code','z'])

    fig, ax = plt.subplots(figsize=(14, 7)); ax.set_facecolor('white')
    cur_x = 0; gap = 50; max_h = 0
    
    for _, stack in data.groupby(['x', 'y'], sort=False):
        w = stack.iloc[0]['width']
        for _, r in stack.iterrows():
            ax.add_patch(patches.Rectangle((cur_x, r['z']), w, r['height'], fill=True, fc='white', ec=COLORS['border'], lw=1))
            if r['utilization'] > 0:
                ax.add_patch(patches.Rectangle((cur_x, r['z']), w, r['height']*r['utilization'], fc=_get_color(r['utilization']), alpha=0.9))
            if r['height']>50:
                lvl = int(r['level_num']) if 'level_num' in r else '?'
                ax.text(cur_x+w/2, r['z']+r['height']/2, f"L{lvl}", ha='center', va='center', fontsize=8, alpha=0.5)
        
        top = stack['z'].max() + stack['height'].max()
        if top > max_h: max_h = top
        cur_x += w + gap

    ax.set_xlim(-100, cur_x+100); ax.set_ylim(0, max_h+200); ax.set_aspect('equal')
    ax.set_title(f"Front Elevation: {title_suffix}", fontsize=14)
    _save_and_show_plot(fig, f"front_view_{title_suffix}")

def _plot_scatter(df, title_suffix):
    fig, ax = plt.subplots(figsize=(10, 6))
    plot_df = df[df['SKU'].notna() & (df['utilization'] > 0)].copy()
    
    if not plot_df.empty:
        for cls in ['A', 'B', 'C']:
            sub = plot_df[plot_df['ABC_Class'] == cls]
            ax.scatter(sub['pick_score'], sub['DEMAND'], c=COLORS.get(cls,'gray'), label=f'Class {cls}', alpha=0.7, edgecolors='w', s=80)
            
        ax.set_title(f"Demand vs Pick Score: {title_suffix}", fontsize=14)
        ax.set_xlabel("Pick Score (Ergonomics + Proximity)"); ax.set_ylabel("Demand")
        ax.grid(True, ls='--', alpha=0.5); ax.legend()
        plt.axvline(x=50, c='gray', ls='--')
        _save_and_show_plot(fig, f"scatter_{title_suffix}")
    else:
        plt.close(fig)
        print("[Visualizer] No data for scatter plot.")

# ==========================================
# 4. MAIN WRAPPER (THE ONLY FUNCTION YOU CALL)
# ==========================================

def generate_dashboard(df_alloc_raw, df_locations, df_items, title="Report"):
    """
    Main Entry Point.
    1. Prepares Data (Cleans, Merges, ABC, Scoring)
    2. Calculates Stats
    3. Prints Report
    4. Generates All Plots
    Returns the processed dataframe in case you need it for logic.
    """
    print(f"\n{'='*20} PROCESSING: {title} {'='*20}")
    
    # 1. Prepare
    df_unified = prepare_unified_dataframe(df_alloc_raw, df_locations, df_items)
    
    # 2. Stats
    stats = calculate_warehouse_stats(df_unified)
    _print_stats(stats, title)
    
    # 3. Plots
    _plot_top(df_unified, title)
    _plot_front(df_unified, title)
    _plot_scatter(df_unified, title)
    
    return df_unified