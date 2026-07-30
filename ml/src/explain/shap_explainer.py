"""SHAP TreeExplainer wrapper + grouped attribution (blueprint §14.2/§14.3).

The explainer is built once (construction is the expensive part) and reused
across every prediction — never rebuilt per request.
"""

import shap
import numpy as np

from .groups import FEATURE_GROUPS, GROUP_LABELS


def build_explainer(raw_tree_model):
    return shap.TreeExplainer(raw_tree_model)


def explain_row(explainer, x_row, feature_names):
    """Returns (raw_shap_dict, grouped_shap_dict) for one fused feature vector."""
    shap_values = explainer.shap_values(np.array([x_row]))

    # TreeExplainer's return shape varies by sklearn/xgboost wrapper version
    # (list-of-arrays for older multiclass-style output vs a single 2D/3D
    # array) — normalise to a flat 1D array of per-feature contribution
    # toward the positive (fraudulent) class before doing anything else.
    if isinstance(shap_values, list):
        values = np.array(shap_values[-1][0])
    else:
        arr = np.array(shap_values)
        values = arr[0, :, -1] if arr.ndim == 3 else arr[0]

    raw = {name: float(v) for name, v in zip(feature_names, values)}

    grouped = {}
    for name, v in raw.items():
        group = FEATURE_GROUPS.get(name, "other")
        grouped[group] = grouped.get(group, 0.0) + v

    return raw, grouped


def top_groups(grouped: dict, eligible_only: set, k=5):
    """Ranked (group, contribution) pairs, positive contributions first —
    what pushed the prediction toward fraudulent, which is what the user-facing
    'why' section shows (negative/reassuring contributions are available in
    the raw output for the admin/research view but not surfaced by default)."""
    items = [(g, v) for g, v in grouped.items() if g in eligible_only]
    items.sort(key=lambda kv: kv[1], reverse=True)
    return items[:k]
