#!/usr/bin/env python3
"""
Show metrics of current Production model from MLflow.

Usage:
    python WMS/scripts/show_metrics.py
    python WMS/scripts/show_metrics.py --all  # Show all versions
"""

import argparse
import sys
import mlflow
from mlflow.tracking import MlflowClient
from datetime import datetime

MLFLOW_URI = "http://100.49.195.150:5000"
MODEL_NAME = "water-meter-segmentation"


def format_metrics(metrics):
    """Format metrics dict for display."""
    return "\n".join([f"    {k}: {v:.4f}" for k, v in sorted(metrics.items())])


def show_production_metrics():
    """Show metrics for Production model."""
    print(f"Connecting to MLflow: {MLFLOW_URI}")
    mlflow.set_tracking_uri(MLFLOW_URI)
    client = MlflowClient()

    try:
        # Get Production model
        prod_versions = client.get_latest_versions(MODEL_NAME, stages=["Production"])

        if not prod_versions:
            print(f"\n[WARNING] No Production model found for '{MODEL_NAME}'")
            print("\nPromote a model first:")
            print("  python WMS/scripts/check_model.py")
            return

        prod_version = prod_versions[0]
        print(f"\n{'='*60}")
        print(f"PRODUCTION MODEL - Version {prod_version.version}")
        print(f"{'='*60}\n")

        # Get run details
        run = client.get_run(prod_version.run_id)

        print(f"Run ID: {run.info.run_id}")
        print(f"Created: {datetime.fromtimestamp(run.info.start_time / 1000).strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Status: {run.info.status}")
        print(f"\nMetrics:")
        print(format_metrics(run.data.metrics))

        if run.data.params:
            print(f"\nKey Parameters:")
            important_params = ['learning_rate', 'batch_size', 'epochs', 'optimizer']
            for param in important_params:
                if param in run.data.params:
                    print(f"    {param}: {run.data.params[param]}")

        # Quality assessment
        dice = run.data.metrics.get('val_dice', run.data.metrics.get('test_dice', 0))
        print(f"\n{'='*60}")
        if dice >= 0.85:
            print("✅ EXCELLENT MODEL (Dice >= 85%)")
        elif dice >= 0.70:
            print("⚠️  GOOD MODEL (Dice 70-85%)")
        elif dice >= 0.50:
            print("⚠️  MEDIOCRE MODEL (Dice 50-70%) - Consider retraining")
        else:
            print("❌ POOR MODEL (Dice < 50%) - Retraining recommended!")
        print(f"{'='*60}\n")

    except Exception as e:
        print(f"[ERROR] Failed to get model metrics: {e}")
        print("\nTroubleshooting:")
        print("  1. Is EC2 running? Start with: python WMS/scripts/sync_model_aws.py --no-stop")
        print("  2. Is MLflow accessible? Try: curl http://100.49.195.150:5000/health")
        sys.exit(1)


def show_all_versions():
    """Show metrics for all model versions."""
    print(f"Connecting to MLflow: {MLFLOW_URI}")
    mlflow.set_tracking_uri(MLFLOW_URI)
    client = MlflowClient()

    try:
        versions = client.search_model_versions(f'name="{MODEL_NAME}"')

        if not versions:
            print(f"\n[ERROR] No versions found for model '{MODEL_NAME}'")
            return

        print(f"\n{'='*60}")
        print(f"ALL MODEL VERSIONS ({len(versions)} total)")
        print(f"{'='*60}\n")

        for v in sorted(versions, key=lambda x: int(x.version), reverse=True):
            run = client.get_run(v.run_id)
            dice = run.data.metrics.get('val_dice', run.data.metrics.get('test_dice', 0))
            iou = run.data.metrics.get('val_iou', run.data.metrics.get('test_iou', 0))

            stage_marker = "🏆 PRODUCTION" if v.current_stage == "Production" else v.current_stage
            print(f"Version {v.version}: {stage_marker}")
            print(f"  Dice: {dice:.4f} | IoU: {iou:.4f}")
            print(f"  Created: {datetime.fromtimestamp(run.info.start_time / 1000).strftime('%Y-%m-%d %H:%M:%S')}")
            print()

    except Exception as e:
        print(f"[ERROR] Failed to get model versions: {e}")
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Show Production model metrics from MLflow")
    parser.add_argument(
        "--all",
        action="store_true",
        help="Show all model versions (not just Production)"
    )

    args = parser.parse_args()

    if args.all:
        show_all_versions()
    else:
        show_production_metrics()
