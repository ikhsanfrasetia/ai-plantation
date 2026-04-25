import pandas as pd


def prepare_heatmap(data):
    """Prepare data for heatmap visualization"""
    heatmap = data.pivot_table(
        index="afdeling",
        columns="blok",
        values="produktivitas",  # Ganti dari 'produktifitas' menjadi 'produktivitas'
        aggfunc="mean"
    )
    
    # Sort for better display
    heatmap = heatmap.sort_index()
    heatmap = heatmap.reindex(sorted(heatmap.columns), axis=1)
    
    return heatmap