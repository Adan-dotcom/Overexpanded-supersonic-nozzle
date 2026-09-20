import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.linalg import qr
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.metrics import f1_score, mean_absolute_error, mean_squared_error, roc_auc_score
from sklearn.model_selection import GroupShuffleSplit
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.neural_network import MLPClassifier, MLPRegressor


OPERATING_COLUMNS = ["pc_pa", "t0_k", "pa_pa", "of_ratio"]


def parse_boolean(series, name):
    if series.dtype == bool:
        return series
    mapping = {
        "true": True,
        "false": False,
        "1": True,
        "0": False,
        "yes": True,
        "no": False,
    }
    normalized = series.astype(str).str.strip().str.lower()
    unknown = sorted(set(normalized) - set(mapping))
    if unknown:
        raise SystemExit(f"Column {name} contains ambiguous boolean values: {unknown}")
    return normalized.map(mapping).astype(bool)


def sensor_layouts(x_train, budget):
    n_sensors = x_train.shape[1]
    uniform = np.unique(np.linspace(0, n_sensors - 1, budget).round().astype(int))
    centered = x_train - np.mean(x_train, axis=0, keepdims=True)
    _, _, vt = np.linalg.svd(centered, full_matrices=False)
    rank = min(budget, vt.shape[0])
    _, _, pivots = qr(vt[:rank], pivoting=True, mode="economic")
    return {"uniform": uniform[:budget], "pod_qr": np.asarray(pivots[:budget])}


def classification_metrics(y_true, probability):
    prediction = probability >= 0.5
    result = {"f1": float(f1_score(y_true, prediction))}
    result["auroc"] = float(roc_auc_score(y_true, probability)) if len(np.unique(y_true)) == 2 else None
    return result


def main():
    parser = argparse.ArgumentParser(description="Train sparse pressure-sensor baselines without CFD-case leakage.")
    parser.add_argument("dataset", type=Path)
    parser.add_argument("--allow-provisional", action="store_true")
    parser.add_argument("--seed", type=int, default=20260919)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    frame = pd.read_csv(args.dataset)
    if not args.allow_provisional:
        frame = frame[parse_boolean(frame["physics_accepted"], "physics_accepted")].copy()
    if len(frame) < 20:
        raise SystemExit(
            f"Only {len(frame)} eligible cases. Final training requires at least 20; "
            "use --allow-provisional only to test the software."
        )

    sensor_columns = sorted(column for column in frame.columns if column.startswith("p_s"))
    if not sensor_columns:
        raise SystemExit("No pressure columns named p_sNNN were found.")
    groups = frame["case_id"].astype(str).to_numpy()
    splitter = GroupShuffleSplit(n_splits=1, test_size=0.20, random_state=args.seed)
    train_index, test_index = next(splitter.split(frame, groups=groups))
    p_train = frame.iloc[train_index][sensor_columns].to_numpy(float)
    p_test = frame.iloc[test_index][sensor_columns].to_numpy(float)
    operating_train = frame.iloc[train_index][OPERATING_COLUMNS].to_numpy(float)
    operating_test = frame.iloc[test_index][OPERATING_COLUMNS].to_numpy(float)
    separated_train = frame.iloc[train_index]["separated"].to_numpy(int)
    separated_test = frame.iloc[test_index]["separated"].to_numpy(int)
    xsep_train = frame.iloc[train_index]["x_sep_m"].to_numpy(float)
    xsep_test = frame.iloc[test_index]["x_sep_m"].to_numpy(float)

    budgets = [value for value in (2, 3, 4, 5, 6, 8, 10, 12, 16, 24) if value <= len(sensor_columns)]
    results = []
    for budget in budgets:
        for layout_name, indices in sensor_layouts(p_train, budget).items():
            x_train = np.column_stack((p_train[:, indices], operating_train))
            x_test = np.column_stack((p_test[:, indices], operating_test))
            classifiers = {
                "random_forest": RandomForestClassifier(n_estimators=300, min_samples_leaf=2, random_state=args.seed),
                "mlp": make_pipeline(
                    StandardScaler(),
                    MLPClassifier(hidden_layer_sizes=(64, 32), max_iter=2000, random_state=args.seed),
                ),
            }
            for model_name, model in classifiers.items():
                model.fit(x_train, separated_train)
                probability = model.predict_proba(x_test)[:, 1]
                results.append(
                    {
                        "task": "classification",
                        "model": model_name,
                        "layout": layout_name,
                        "budget": budget,
                        "sensor_indices": indices.tolist(),
                        **classification_metrics(separated_test, probability),
                    }
                )

            train_mask = separated_train.astype(bool) & np.isfinite(xsep_train)
            test_mask = separated_test.astype(bool) & np.isfinite(xsep_test)
            if np.sum(train_mask) < 10 or np.sum(test_mask) < 2:
                continue
            regressors = {
                "random_forest": RandomForestRegressor(n_estimators=300, min_samples_leaf=2, random_state=args.seed),
                "mlp": make_pipeline(
                    StandardScaler(),
                    MLPRegressor(hidden_layer_sizes=(64, 32), max_iter=3000, random_state=args.seed),
                ),
            }
            for model_name, model in regressors.items():
                model.fit(x_train[train_mask], xsep_train[train_mask])
                prediction = model.predict(x_test[test_mask])
                results.append(
                    {
                        "task": "x_sep_regression",
                        "model": model_name,
                        "layout": layout_name,
                        "budget": budget,
                        "sensor_indices": indices.tolist(),
                        "mae_m": float(mean_absolute_error(xsep_test[test_mask], prediction)),
                        "rmse_m": float(np.sqrt(mean_squared_error(xsep_test[test_mask], prediction))),
                    }
                )

    provisional_used = bool(
        "provisional" in frame and parse_boolean(frame["provisional"], "provisional").any()
    )
    payload = {
        "dataset": str(args.dataset.resolve()),
        "n_cases": len(frame),
        "n_train": len(train_index),
        "n_test": len(test_index),
        "physics_accepted_only": not args.allow_provisional,
        "provisional_data_used": provisional_used,
        "validation_protocol": "single_group_holdout_development",
        "publishable": False,
        "warning": (
            "Development-only metrics: provisional data used"
            if provisional_used or args.allow_provisional
            else "Development-only metrics: grouped nested validation and a locked test set remain required"
        ),
        "results": results,
    }
    output = args.output or args.dataset.with_name("sensor_model_results.json")
    output.write_text(json.dumps(payload, indent=2) + "\n", encoding="ascii")
    result_frame = pd.DataFrame(results)
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5), constrained_layout=True)
    classification = result_frame[result_frame["task"] == "classification"]
    for (model, layout), group in classification.groupby(["model", "layout"]):
        group = group.sort_values("budget")
        axes[0].plot(group["budget"], group["f1"], marker="o", label=f"{model} / {layout}")
    axes[0].set(xlabel="Pressure sensors", ylabel="F1", title="Separation classification", ylim=(0, 1.03))
    regression = result_frame[result_frame["task"] == "x_sep_regression"]
    for (model, layout), group in regression.groupby(["model", "layout"]):
        group = group.sort_values("budget")
        axes[1].plot(group["budget"], 1e3 * group["mae_m"], marker="o", label=f"{model} / {layout}")
    axes[1].set(xlabel="Pressure sensors", ylabel="MAE x_sep [mm]", title="Conditional separation location")
    for axis in axes:
        axis.grid(alpha=0.25)
        axis.legend(fontsize=7)
    figure_path = output.with_suffix(".png")
    fig.savefig(figure_path, dpi=180)
    plt.close(fig)
    print(json.dumps({key: value for key, value in payload.items() if key != "results"}, indent=2))
    print(f"Wrote {len(results)} model/layout/budget results to {output}")
    print(f"Wrote development plot to {figure_path}")


if __name__ == "__main__":
    main()
