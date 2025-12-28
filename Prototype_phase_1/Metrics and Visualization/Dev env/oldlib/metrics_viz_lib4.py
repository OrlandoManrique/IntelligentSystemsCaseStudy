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
        try: os.makedirs(abs_plot_folder)
        except OSError: pass
    
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
# 1. DATA PREPARATION & SCORING ENGINE
# ==========================================

def _clean_allocation_data(df_alloc):
    df = df_alloc.copy()
    rename_map = {'LOC_CODE': 'LOCATION_ID', 'ITEM_ID': 'SKU', 'UTILIZATION_PCT': 'utilization', 'QTY_ALLOCATED': 'QTY'}
    df.rename(columns=rename_map, inplace=True)
    
    if 'utilization' in df.columns:
        if df['utilization'].max() > 1.1:
            df['utilization'] = df['utilization'] / 100.0
            
    if 'LOCATION_ID' in df.columns:
        df = df[df['LOCATION_ID'] != 'UNFIT']
    return df

def _apply_abc_classification(df):
    if 'DEMAND' not in df.columns:
        df['ABC_Class'] = 'C'; return df

    # Calculate on unique items to avoid skewing by allocation count
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

def _calculate_detailed_scores(df):
    """
    Implements the "Reward Function" logic for analysis.
    """
    # 1. Setup Base Columns
    df['Reward_Zone'] = 0.0
    df['Reward_Util'] = 0.0
    df['Penalty_Dist'] = 0.0
    df['Total_Score'] = 0.0
    df['Violation_Flag'] = False
    
    # 2. Hard Constraints (Penalties)
    # Weight Safety: Heavy (>15kg) AND Z > 1500
    df['violation_weight'] = (df['is_heavy']) & (df['z'] > 1500)
    
    # 3. Scaled Rewards
    
    # A. Zone Logic
    # Target Zone: Bay <= 25% of Max AND Golden Height (700-1500)
    if 'bay_num' in df.columns:
        max_bay = df['bay_num'].max()
        # Avoid div by zero
        target_bay_limit = max_bay * 0.25 if max_bay > 0 else 999 
        df['is_target_bay'] = df['bay_num'] <= target_bay_limit
    else:
        df['is_target_bay'] = False # Cannot determine
        
    df['is_golden_height'] = df['z'].between(700, 1500)
    df['in_target_zone'] = df['is_target_bay'] & df['is_golden_height']
    
    # Reward: Class A in Target Zone (+1000)
    mask_a_target = (df['ABC_Class'] == 'A') & (df['in_target_zone'])
    df.loc[mask_a_target, 'Reward_Zone'] = 1000.0
    
    # Reward: Class B in Target Zone (+400) -> Prompt says "Mid-Target Zone" is same geo requirements
    mask_b_target = (df['ABC_Class'] == 'B') & (df['in_target_zone'])
    df.loc[mask_b_target, 'Reward_Zone'] = 400.0
    
    # B. Storage Utilization (+0 to +800)
    # (Item_Vol / Bin_Vol) * 800 -> This is 'utilization' * 800
    df['Reward_Util'] = df['utilization'] * 800.0
    
    # C. Distance Penalty (-100 to 0)
    # (Dist / Max_Dist) * -100. Using 'x' as proxy for distance from entrance (0,0)
    max_x = df['x'].max()
    if max_x > 0:
        df['Penalty_Dist'] = (df['x'] / max_x) * -100.0
    else:
        df['Penalty_Dist'] = 0.0
        
    # D. Affinity Reward (+50)
    # (Skipped for visualizer as it requires complex neighbor graph analysis, 
    # assuming 0 for static reporting unless provided)
    
    # 4. Total Score Calculation
    # Sum rewards
    df['Total_Score'] = df['Reward_Zone'] + df['Reward_Util'] + df['Penalty_Dist']
    
    # Apply Hard Penalty (-10,000) override
    df.loc[df['violation_weight'], 'Total_Score'] = -10000.0
    df.loc[df['violation_weight'], 'Violation_Flag'] = True
    
    return df

def prepare_unified_dataframe(df_alloc_raw, df_locations, df_items=None):
    # 1. Clean & Merge
    df_alloc = _clean_allocation_data(df_alloc_raw)
    
    if 'utilization' in df_alloc.columns:
        agg_dict = {'utilization': 'sum'}
        if 'SKU' in df_alloc.columns: agg_dict['SKU'] = 'first'
        df_alloc_grouped = df_alloc.groupby('LOCATION_ID', as_index=False).agg(agg_dict)
    else:
        df_alloc_grouped = df_alloc

    df = pd.merge(df_locations, df_alloc_grouped, left_on='loc_inst_code', right_on='LOCATION_ID', how='left')
    df['utilization'] = df['utilization'].fillna(0.0)
    
    # 2. Merge Items
    if df_items is not None and 'SKU' in df.columns:
        df = pd.merge(df, df_items[['ITEM_ID', 'DEMAND', 'WT_KG']], left_on='SKU', right_on='ITEM_ID', how='left')
        df['DEMAND'] = df['DEMAND'].fillna(0)
        df['WT_KG'] = df['WT_KG'].fillna(0)
    else:
        df['DEMAND'] = 0; df['WT_KG'] = 0

    # 3. Logic: ABC & Constraints
    df = _apply_abc_classification(df)
    df['is_heavy'] = df['WT_KG'] > 15.0
    
    # 4. Calculate Scores
    df = _calculate_detailed_scores(df)
    
    return df

# ==========================================
# 2. STATISTICS
# ==========================================

def calculate_warehouse_stats(df):
    occupied_df = df[df['utilization'] > 0]
    
    # Counts
    occ_count = len(occupied_df)
    total_count = len(df)
    occ_pct = (occ_count / total_count * 100) if total_count > 0 else 0.0
    
    # Utilization
    avg_util = occupied_df['utilization'].mean() * 100 if not occupied_df.empty else 0.0
    
    # Violations
    weight_vios = df['violation_weight'].sum()
    
    # Misplaced A-Items (Class A NOT in Target Zone)
    # Note: Using the scoring logic definitions
    misplaced_a = occupied_df[
        (occupied_df['ABC_Class'] == 'A') & 
        (~occupied_df['in_target_zone'])
    ].shape[0]
    
    # Average Scores (Occupied Only - usually scores are relevant for placed items)
    if not occupied_df.empty:
        avg_score_total = occupied_df['Total_Score'].mean()
        avg_score_zone = occupied_df['Reward_Zone'].mean()
        avg_score_util = occupied_df['Reward_Util'].mean()
        avg_score_dist = occupied_df['Penalty_Dist'].mean()
    else:
        avg_score_total = 0; avg_score_zone = 0; avg_score_util = 0; avg_score_dist = 0

    stats = {
        # Violations
        "Weight Violations": int(weight_vios),
        "Misplaced A-Items": int(misplaced_a),
        
        # Occupancy
        "Avg Util (Occupied)": avg_util,
        "%Occupied Bins": occ_pct,
        "Occupied Count": occ_count,
        "Total Count": total_count,
        
        # Scoring Metrics
        "Avg Combined Score": avg_score_total,
        "Avg Zone Reward": avg_score_zone,
        "Avg Util Reward": avg_score_util,
        "Avg Dist Penalty": avg_score_dist
    }
        
    return stats

def _print_stats(stats, title):
    print(f"\n{'-'*10} {title} {'-'*10}")
    
    # 1. Violations
    v_w = stats.get("Weight Violations", 0)
    print(f"{'Weight Violations':<25}: {v_w} {'(!)' if v_w > 0 else '(OK)'}")
    v_a = stats.get("Misplaced A-Items", 0)
    print(f"{'Misplaced A-Items':<25}: {v_a} {'(!)' if v_a > 0 else '(OK)'}")
    print("")
    
    # 2. Scores
    print("--- Scoring Breakdown (Avg per Occupied Bin) ---")
    print(f"{'Avg Combined Score':<25}: {stats.get('Avg Combined Score',0):.1f}")
    print(f"{'  > Zone Reward':<25}: {stats.get('Avg Zone Reward',0):.1f}")
    print(f"{'  > Util Reward':<25}: {stats.get('Avg Util Reward',0):.1f}")
    print(f"{'  > Dist Penalty':<25}: {stats.get('Avg Dist Penalty',0):.1f}")
    print("")
    
    # 3. Operations
    u_avg = stats.get("Avg Util (Occupied)", 0)
    print(f"{'Avg Util (Occupied)':<25}: {u_avg:.2f}%")
    
    occ_pct = stats.get("%Occupied Bins", 0)
    occ_n = stats.get("Occupied Count", 0)
    tot_n = stats.get("Total Count", 0)
    print(f"{'%Occupied Bins':<25}: {occ_pct:.1f}%   ({occ_n}/{tot_n})")
    
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

# --- A. Standard Views ---
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

# --- B. New Charts ---

def _plot_demand_vs_height(df, title_suffix):
    """
    Scatter: Height (Y) vs Demand (X).
    Logic: A-Movers (High Demand) should be in Golden Zone (700-1500).
    """
    fig, ax = plt.subplots(figsize=(10, 6))
    plot_df = df[df['SKU'].notna() & (df['utilization'] > 0)].copy()
    
    if not plot_df.empty:
        # Golden Zone band
        ax.axhspan(700, 1500, color='#2ecc71', alpha=0.1, label='Golden Zone (Ergonomic)')
        
        for cls in ['A', 'B', 'C']:
            sub = plot_df[plot_df['ABC_Class'] == cls]
            ax.scatter(sub['DEMAND'], sub['z'], c=COLORS.get(cls,'gray'), label=f'Class {cls}', alpha=0.7, edgecolors='w', s=80)
            
        ax.set_title(f"Demand vs. Height (Golden Zone Check): {title_suffix}", fontsize=14)
        ax.set_xlabel("Item Demand"); ax.set_ylabel("Elevation / Height (mm)")
        ax.grid(True, ls='--', alpha=0.5); ax.legend(loc='upper right')
        
        _save_and_show_plot(fig, f"scatter_demand_height_{title_suffix}")
    else:
        plt.close(fig)

def _plot_util_distribution(df, title_suffix):
    """
    Histogram: Distribution of Utilization % for Occupied Bins.
    """
    fig, ax = plt.subplots(figsize=(10, 6))
    # Filter only occupied
    data = df[df['utilization'] > 0]['utilization'] * 100
    
    if len(data) > 0:
        n, bins, patches_hist = ax.hist(data, bins=20, range=(0,100), color=COLORS['med'], edgecolor='white', alpha=0.7)
        
        # Color bars based on value
        for i, p in enumerate(patches_hist):
            # Calculate center of bin to decide color
            center = (p.get_x() + p.get_width() / 2) / 100.0
            p.set_facecolor(_get_color(center))

        ax.set_title(f"Volume Utilization % Distribution (Occupied Bins): {title_suffix}", fontsize=14)
        ax.set_xlabel("Utilization %"); ax.set_ylabel("Count of Bins")
        ax.grid(axis='y', alpha=0.3)
        
        _save_and_show_plot(fig, f"hist_utilization_{title_suffix}")
    else:
        plt.close(fig)

# ==========================================
# 4. MAIN WRAPPER
# ==========================================

def generate_dashboard(df_alloc_raw, df_locations, df_items, title="Report"):
    print(f"\n{'='*20} PROCESSING: {title} {'='*20}")
    
    # 1. Prepare
    df_unified = prepare_unified_dataframe(df_alloc_raw, df_locations, df_items)
    
    # 2. Stats
    stats = calculate_warehouse_stats(df_unified)
    _print_stats(stats, title)
    
    # 3. Plots
    _plot_top(df_unified, title)
    _plot_front(df_unified, title)
    _plot_demand_vs_height(df_unified, title)   # NEW
    _plot_util_distribution(df_unified, title)  # NEW
    
    return df_unified