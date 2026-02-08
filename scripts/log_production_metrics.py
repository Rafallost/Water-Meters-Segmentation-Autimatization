#!/usr/bin/env python3
"""
Log Production model metrics to a tracked file.

This script:
1. Fetches Production model from MLflow
2. Extracts key metrics
3. Appends to models/production_history.json
4. Updates models/production_current.json

Usage:
    python WMS/scripts/log_production_metrics.py
    python WMS/scripts/log_production_metrics.py --mlflow-uri http://IP:5000
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

import mlflow
from mlflow.tracking import MlflowClient


def log_production_metrics(mlflow_uri: str, models_dir: str = "WMS/models"):
    """Log Production model metrics to files."""

    print(f"Connecting to MLflow: {mlflow_uri}")
    mlflow.set_tracking_uri(mlflow_uri)
    client = MlflowClient()

    try:
        # Get Production model
        prod_versions = client.get_latest_versions(
            "water-meter-segmentation",
            stages=["Production"]
        )

        if not prod_versions:
            print("[WARNING] No Production model found")
            return False

        prod_version = prod_versions[0]
        run = client.get_run(prod_version.run_id)

        # Extract metrics
        metrics = {
            "version": int(prod_version.version),
            "run_id": prod_version.run_id,
            "stage": prod_version.current_stage,
            "timestamp": datetime.now().isoformat(),
            "created_at": datetime.fromtimestamp(run.info.start_time / 1000).isoformat(),
            "metrics": {
                k: float(v) for k, v in run.data.metrics.items()
            },
            "params": dict(run.data.params)
        }

        # Ensure models directory exists
        models_path = Path(models_dir)
        models_path.mkdir(parents=True, exist_ok=True)

        # Update current Production metrics
        current_file = models_path / "production_current.json"
        with open(current_file, 'w') as f:
            json.dump(metrics, f, indent=2)
        print(f"[OK] Updated: {current_file}")

        # Append to history
        history_file = models_path / "production_history.jsonl"
        with open(history_file, 'a') as f:
            f.write(json.dumps(metrics) + '\n')
        print(f"[OK] Appended to: {history_file}")

        # Print summary
        print("\n" + "="*60)
        print(f"PRODUCTION MODEL - Version {metrics['version']}")
        print("="*60)
        print(f"Run ID: {metrics['run_id']}")
        print(f"Created: {metrics['created_at']}")
        print(f"\nKey Metrics:")

        for key in ['val_dice', 'val_iou', 'test_dice', 'test_iou']:
            if key in metrics['metrics']:
                print(f"  {key}: {metrics['metrics'][key]:.4f}")

        print("="*60)

        return True

    except Exception as e:
        print(f"[ERROR] Failed to log Production metrics: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Log Production model metrics to tracked files"
    )
    parser.add_argument(
        "--mlflow-uri",
        default=os.environ.get("MLFLOW_TRACKING_URI", "http://localhost:5000"),
        help="MLflow tracking URI"
    )
    parser.add_argument(
        "--models-dir",
        default="WMS/models",
        help="Models directory (default: WMS/models)"
    )

    args = parser.parse_args()

    success = log_production_metrics(args.mlflow_uri, args.models_dir)
    sys.exit(0 if success else 1)
