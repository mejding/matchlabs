from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from calibration.calibration import (
    calibration_diagnosis,
    calibration_summary,
    calibration_table,
    expected_calibration_error,
    plot_calibration_curve,
    plot_probability_histogram,
    plot_reliability_diagram,
)


def run_calibration_analysis(
    y_true: pd.Series,
    probabilities: np.ndarray,
    output_dir: Path,
) -> dict[str, object]:
    output_dir.mkdir(exist_ok=True)
    table = calibration_table(y_true, probabilities)
    table.to_csv(output_dir / "calibration_table.csv", index=False)
    plot_calibration_curve(table, output_dir / "calibration_curve.png")
    plot_reliability_diagram(table, output_dir / "reliability_diagram.png")
    plot_probability_histogram(probabilities, output_dir / "probability_histogram.png")
    summary = calibration_summary(table)
    return {
        "summary": summary,
        "expected_calibration_error": expected_calibration_error(table),
        "diagnosis": calibration_diagnosis(summary),
    }
