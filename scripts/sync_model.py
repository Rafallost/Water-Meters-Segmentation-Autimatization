#!/usr/bin/env python3
"""
Automatic model synchronization script.

This script automates the entire process of:
1. Starting EC2 instance
2. Waiting for MLflow to be ready
3. Downloading Production model
4. Optionally stopping EC2 instance

Usage:
    python WMS/scripts/sync_model.py
    python WMS/scripts/sync_model.py --keep-running  # Don't stop EC2 after download
    python WMS/scripts/sync_model.py --force         # Re-download even if cached
"""

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

# Colors for terminal output
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_step(message):
    """Print a step message with formatting."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}▶ {message}{Colors.END}")

def print_success(message):
    """Print a success message."""
    print(f"{Colors.GREEN}✅ {message}{Colors.END}")

def print_warning(message):
    """Print a warning message."""
    print(f"{Colors.YELLOW}⚠️  {message}{Colors.END}")

def print_error(message):
    """Print an error message."""
    print(f"{Colors.RED}❌ {message}{Colors.END}")

def check_gh_cli():
    """Check if GitHub CLI is installed."""
    try:
        result = subprocess.run(
            ["gh", "--version"],
            capture_output=True,
            text=True,
            check=True
        )
        print_success(f"GitHub CLI detected: {result.stdout.split()[2]}")
        return True
    except FileNotFoundError:
        print_error("GitHub CLI (gh) not found!")
        print("\nInstall instructions:")
        print("  Windows: winget install --id GitHub.cli")
        print("  macOS:   brew install gh")
        print("  Linux:   See https://github.com/cli/cli#installation")
        return False
    except subprocess.CalledProcessError:
        print_error("GitHub CLI check failed!")
        return False

def check_gh_auth():
    """Check if GitHub CLI is authenticated."""
    try:
        result = subprocess.run(
            ["gh", "auth", "status"],
            capture_output=True,
            text=True,
            check=True
        )
        print_success("GitHub CLI authenticated")
        return True
    except subprocess.CalledProcessError:
        print_error("GitHub CLI not authenticated!")
        print("\nAuthenticate with: gh auth login")
        return False

def start_ec2_workflow():
    """Start the EC2 instance via GitHub Actions workflow."""
    print_step("Starting EC2 instance via GitHub Actions...")

    try:
        # Trigger workflow
        result = subprocess.run(
            ["gh", "workflow", "run", "ec2-manual-control.yaml", "-f", "action=start"],
            capture_output=True,
            text=True,
            check=True,
            cwd=Path(__file__).parent.parent.parent
        )

        print_success("Workflow triggered successfully")

        # Wait a bit for workflow to start
        print("⏳ Waiting 10 seconds for workflow to start...")
        time.sleep(10)

        return True

    except subprocess.CalledProcessError as e:
        print_error(f"Failed to start workflow: {e.stderr}")
        return False

def wait_for_workflow():
    """Wait for the workflow to complete and return its run ID."""
    print_step("Waiting for workflow to complete...")

    max_attempts = 60  # 10 minutes max
    attempt = 0

    while attempt < max_attempts:
        try:
            # Get latest workflow run
            result = subprocess.run(
                ["gh", "run", "list", "--workflow=ec2-manual-control.yaml", "--limit=1", "--json", "status,conclusion,databaseId"],
                capture_output=True,
                text=True,
                check=True,
                cwd=Path(__file__).parent.parent.parent
            )

            runs = json.loads(result.stdout)

            if not runs:
                print("⏳ Waiting for workflow to appear...")
                time.sleep(10)
                attempt += 1
                continue

            run = runs[0]
            status = run['status']
            conclusion = run.get('conclusion')
            run_id = run['databaseId']

            if status == 'completed':
                if conclusion == 'success':
                    print_success(f"Workflow completed successfully (run #{run_id})")
                    return run_id
                else:
                    print_error(f"Workflow failed with conclusion: {conclusion}")
                    print(f"\nView logs: gh run view {run_id}")
                    return None

            print(f"⏳ Workflow status: {status} (attempt {attempt + 1}/{max_attempts})")
            time.sleep(10)
            attempt += 1

        except subprocess.CalledProcessError as e:
            print_error(f"Failed to check workflow status: {e.stderr}")
            return None
        except json.JSONDecodeError as e:
            print_error(f"Failed to parse workflow status: {e}")
            return None

    print_error("Workflow did not complete in time (10 minutes)")
    return None

def get_mlflow_url(run_id):
    """Extract MLflow URL from workflow run."""
    print_step("Getting MLflow URL from workflow output...")

    try:
        # Get workflow run details
        result = subprocess.run(
            ["gh", "run", "view", str(run_id), "--log"],
            capture_output=True,
            text=True,
            check=True,
            cwd=Path(__file__).parent.parent.parent
        )

        # Search for MLflow URL in logs
        for line in result.stdout.split('\n'):
            if 'mlflow_url=' in line or 'MLflow URL:' in line:
                # Extract URL (format: http://IP:5000)
                parts = line.split('http://')
                if len(parts) > 1:
                    url = 'http://' + parts[1].split()[0].strip()
                    print_success(f"MLflow URL: {url}")
                    return url

        # Fallback: try to get from GitHub Actions output
        print_warning("Could not find MLflow URL in logs, checking workflow outputs...")

        # This is a workaround - we'll need to parse the summary
        result = subprocess.run(
            ["gh", "run", "view", str(run_id)],
            capture_output=True,
            text=True,
            check=True,
            cwd=Path(__file__).parent.parent.parent
        )

        for line in result.stdout.split('\n'):
            if 'http://' in line and ':5000' in line:
                # Extract URL
                start = line.find('http://')
                end = line.find(':5000') + 5
                url = line[start:end]
                print_success(f"MLflow URL: {url}")
                return url

        print_error("Could not extract MLflow URL from workflow output")
        print("\nManually check workflow run:")
        print(f"  gh run view {run_id}")
        return None

    except subprocess.CalledProcessError as e:
        print_error(f"Failed to get workflow output: {e.stderr}")
        return None

def download_model(mlflow_url, force=False):
    """Download the model using download_model.py script."""
    print_step("Downloading Production model from MLflow...")

    script_path = Path(__file__).parent.parent / "src" / "download_model.py"

    if not script_path.exists():
        print_error(f"download_model.py not found at: {script_path}")
        return False

    cmd = [sys.executable, str(script_path), "--mlflow-uri", mlflow_url]

    if force:
        cmd.append("--force")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )

        print(result.stdout)
        print_success("Model downloaded successfully!")
        return True

    except subprocess.CalledProcessError as e:
        print_error("Failed to download model")
        print(e.stdout)
        print(e.stderr)
        return False

def stop_ec2_workflow():
    """Stop the EC2 instance via GitHub Actions workflow."""
    print_step("Stopping EC2 instance...")

    try:
        result = subprocess.run(
            ["gh", "workflow", "run", "ec2-manual-control.yaml", "-f", "action=stop"],
            capture_output=True,
            text=True,
            check=True,
            cwd=Path(__file__).parent.parent.parent
        )

        print_success("EC2 stop workflow triggered")
        print("⏳ EC2 will stop in ~1-2 minutes")
        return True

    except subprocess.CalledProcessError as e:
        print_error(f"Failed to stop EC2: {e.stderr}")
        return False

def main():
    parser = argparse.ArgumentParser(
        description="Automatic model synchronization - start EC2, download model, stop EC2"
    )
    parser.add_argument(
        "--keep-running",
        action="store_true",
        help="Keep EC2 running after download (don't stop automatically)"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force re-download even if model is cached locally"
    )
    parser.add_argument(
        "--mlflow-url",
        help="Use specific MLflow URL (skip EC2 start/stop)"
    )

    args = parser.parse_args()

    print(f"\n{Colors.BOLD}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.GREEN}🤖 Automatic Model Synchronization{Colors.END}")
    print(f"{Colors.BOLD}{'='*60}{Colors.END}\n")

    # If MLflow URL provided, skip EC2 control
    if args.mlflow_url:
        print_warning(f"Using provided MLflow URL: {args.mlflow_url}")
        success = download_model(args.mlflow_url, force=args.force)
        sys.exit(0 if success else 1)

    # Check prerequisites
    if not check_gh_cli() or not check_gh_auth():
        print_error("\nPrerequisites not met. Please install and configure GitHub CLI.")
        sys.exit(1)

    # Start EC2
    if not start_ec2_workflow():
        sys.exit(1)

    # Wait for workflow to complete
    run_id = wait_for_workflow()
    if not run_id:
        print_error("\nWorkflow did not complete successfully")
        sys.exit(1)

    # Get MLflow URL
    mlflow_url = get_mlflow_url(run_id)
    if not mlflow_url:
        print_error("\nCould not get MLflow URL")
        print("\nYou can manually download the model:")
        print("1. Check workflow output: gh run view {}".format(run_id))
        print("2. Find the MLflow URL")
        print("3. Run: python WMS/src/download_model.py --mlflow-uri <URL>")
        sys.exit(1)

    # Download model
    if not download_model(mlflow_url, force=args.force):
        print_error("\nModel download failed")
        if not args.keep_running:
            print_warning("Stopping EC2 anyway...")
            stop_ec2_workflow()
        sys.exit(1)

    # Stop EC2 (unless --keep-running)
    if not args.keep_running:
        print("\n" + "="*60)
        response = input(f"{Colors.YELLOW}💡 Stop EC2 instance? (Y/n): {Colors.END}").strip().lower()

        if response in ['', 'y', 'yes']:
            stop_ec2_workflow()
        else:
            print_warning("EC2 instance left running")
            print(f"   MLflow URL: {mlflow_url}")
            print("   Stop manually: gh workflow run ec2-manual-control.yaml -f action=stop")
    else:
        print_warning("EC2 instance left running (--keep-running flag)")
        print(f"   MLflow URL: {mlflow_url}")

    print(f"\n{Colors.BOLD}{Colors.GREEN}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.GREEN}✅ Model synchronization complete!{Colors.END}")
    print(f"{Colors.BOLD}{Colors.GREEN}{'='*60}{Colors.END}\n")

    print("Next steps:")
    print(f"  {Colors.BLUE}▶{Colors.END} Run predictions: python WMS/src/predicts.py")
    print(f"  {Colors.BLUE}▶{Colors.END} Check model: ls -lh WMS/models/production.pth")

if __name__ == "__main__":
    main()
