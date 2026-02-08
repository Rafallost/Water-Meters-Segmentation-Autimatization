#!/usr/bin/env python3
"""
Simple model synchronization using AWS CLI directly.

This script doesn't require GitHub CLI - uses AWS CLI instead.

Usage:
    python WMS/scripts/sync_model_aws.py
    python WMS/scripts/sync_model_aws.py --force  # Re-download even if cached
    python WMS/scripts/sync_model_aws.py --no-stop  # Don't stop EC2 after download
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

def check_aws_cli():
    """Check if AWS CLI is installed."""
    try:
        result = subprocess.run(
            ["aws", "--version"],
            capture_output=True,
            text=True,
            check=True
        )
        print_success(f"AWS CLI detected: {result.stdout.strip().split()[0]}")
        return True
    except FileNotFoundError:
        print_error("AWS CLI not found!")
        print("\nInstall instructions:")
        print("  Windows: https://aws.amazon.com/cli/")
        print("  macOS:   brew install awscli")
        print("  Linux:   sudo apt install awscli")
        return False
    except subprocess.CalledProcessError:
        print_error("AWS CLI check failed!")
        return False

def check_aws_credentials():
    """Check if AWS credentials are configured."""
    try:
        result = subprocess.run(
            ["aws", "sts", "get-caller-identity"],
            capture_output=True,
            text=True,
            check=True
        )
        identity = json.loads(result.stdout)
        print_success(f"AWS credentials OK (Account: {identity['Account']})")
        return True
    except subprocess.CalledProcessError as e:
        print_error("AWS credentials not configured!")
        print("\nError:", e.stderr)
        print("\nSetup instructions:")
        print("  1. Go to AWS Academy Lab → Start Lab")
        print("  2. Click 'AWS Details' → Show AWS CLI credentials")
        print("  3. Update credentials in ~/.aws/credentials")
        print("  OR set environment variables:")
        print("     Windows: $env:AWS_ACCESS_KEY_ID=\"...\"")
        print("     Linux:   export AWS_ACCESS_KEY_ID=\"...\"")
        print("\n  OR use helper script:")
        print("     python WMS/scripts/fetch_aws_credentials.py --check")
        return False
    except json.JSONDecodeError:
        print_error("Failed to parse AWS credentials!")
        return False

def get_ec2_info():
    """Get EC2 instance info."""
    print_step("Getting EC2 instance information...")

    try:
        # Get instance ID
        result = subprocess.run(
            [
                "aws", "ec2", "describe-instances",
                "--filters", "Name=tag:Name,Values=wms-k3s",
                "--query", "Reservations[0].Instances[0].[InstanceId,State.Name]",
                "--output", "json",
                "--region", "us-east-1"
            ],
            capture_output=True,
            text=True,
            check=True
        )

        data = json.loads(result.stdout)

        if not data or data[0] is None:
            print_error("EC2 instance not found!")
            print("\nMake sure Terraform infrastructure is deployed.")
            print("See: devops/terraform/README.md")
            return None, None

        instance_id = data[0]
        state = data[1]

        print_success(f"Instance ID: {instance_id}")
        print(f"   Current state: {state}")

        # Get Elastic IP
        result = subprocess.run(
            [
                "aws", "ec2", "describe-addresses",
                "--filters", "Name=tag:Name,Values=wms-eip",
                "--query", "Addresses[0].PublicIp",
                "--output", "text",
                "--region", "us-east-1"
            ],
            capture_output=True,
            text=True,
            check=True
        )

        public_ip = result.stdout.strip()

        if public_ip and public_ip != "None":
            print_success(f"Elastic IP: {public_ip}")
        else:
            print_error("Elastic IP not found!")
            return None, None

        return instance_id, public_ip, state

    except subprocess.CalledProcessError as e:
        print_error(f"Failed to get EC2 info: {e.stderr}")
        return None, None, None
    except json.JSONDecodeError as e:
        print_error(f"Failed to parse EC2 info: {e}")
        return None, None, None

def start_ec2(instance_id):
    """Start EC2 instance."""
    print_step("Starting EC2 instance...")

    try:
        subprocess.run(
            [
                "aws", "ec2", "start-instances",
                "--instance-ids", instance_id,
                "--region", "us-east-1"
            ],
            capture_output=True,
            text=True,
            check=True
        )

        print_success("Start command sent")
        print("⏳ Waiting for instance to start...")

        subprocess.run(
            [
                "aws", "ec2", "wait", "instance-running",
                "--instance-ids", instance_id,
                "--region", "us-east-1"
            ],
            check=True
        )

        print_success("Instance is running!")
        return True

    except subprocess.CalledProcessError as e:
        print_error(f"Failed to start EC2: {e.stderr}")
        return False

def wait_for_mlflow(public_ip, max_wait=600):
    """Wait for MLflow to be ready."""
    print_step(f"Waiting for MLflow to be ready at http://{public_ip}:5000")
    print("This may take 2-5 minutes (Docker, k3s, MLflow startup)...")

    import urllib.request
    import urllib.error

    start_time = time.time()
    attempt = 0

    while time.time() - start_time < max_wait:
        try:
            with urllib.request.urlopen(f"http://{public_ip}:5000/health", timeout=5) as response:
                if response.status == 200:
                    print_success("MLflow is ready!")
                    return True
        except (urllib.error.URLError, TimeoutError, ConnectionError):
            pass

        attempt += 1
        elapsed = int(time.time() - start_time)
        print(f"⏳ Attempt {attempt} - MLflow not ready yet ({elapsed}s elapsed)...")
        time.sleep(10)

    print_error("MLflow did not become ready in time")
    return False

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

def stop_ec2(instance_id):
    """Stop EC2 instance."""
    print_step("Stopping EC2 instance...")

    try:
        subprocess.run(
            [
                "aws", "ec2", "stop-instances",
                "--instance-ids", instance_id,
                "--region", "us-east-1"
            ],
            capture_output=True,
            text=True,
            check=True
        )

        print_success("Stop command sent")
        print("⏳ EC2 will stop in ~1-2 minutes")
        return True

    except subprocess.CalledProcessError as e:
        print_error(f"Failed to stop EC2: {e.stderr}")
        return False

def main():
    parser = argparse.ArgumentParser(
        description="Model synchronization using AWS CLI (no GitHub CLI required)"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force re-download even if model is cached locally"
    )
    parser.add_argument(
        "--no-stop",
        action="store_true",
        help="Don't stop EC2 after download (leave running)"
    )

    args = parser.parse_args()

    print(f"\n{Colors.BOLD}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.GREEN}🤖 Model Synchronization (AWS CLI){Colors.END}")
    print(f"{Colors.BOLD}{'='*60}{Colors.END}\n")

    # Check prerequisites
    if not check_aws_cli():
        print_error("\nAWS CLI not installed!")
        sys.exit(1)

    if not check_aws_credentials():
        print_error("\nAWS credentials not configured!")
        sys.exit(1)

    # Get EC2 info
    instance_id, public_ip, state = get_ec2_info()
    if not instance_id or not public_ip:
        sys.exit(1)

    mlflow_url = f"http://{public_ip}:5000"

    # Start EC2 if not running
    if state != "running":
        if not start_ec2(instance_id):
            sys.exit(1)

        # Wait for MLflow
        if not wait_for_mlflow(public_ip):
            print_error("\nMLflow not ready - you can try manually later:")
            print(f"  python WMS/src/download_model.py --mlflow-uri {mlflow_url}")
            sys.exit(1)
    else:
        print_success("EC2 is already running!")

        # Quick check if MLflow is ready
        print("Checking if MLflow is ready...")
        if not wait_for_mlflow(public_ip, max_wait=30):
            print_warning("MLflow might not be ready yet, trying anyway...")

    # Download model
    if not download_model(mlflow_url, force=args.force):
        print_error("\nModel download failed")
        if not args.no_stop:
            print_warning("Stopping EC2 anyway...")
            stop_ec2(instance_id)
        sys.exit(1)

    # Log Production model metrics to tracked file
    print_step("Logging Production model metrics...")
    try:
        log_script = Path(__file__).parent / "log_production_metrics.py"
        subprocess.run(
            [sys.executable, str(log_script), "--mlflow-uri", mlflow_url],
            check=False  # Don't fail if logging fails
        )
    except Exception as e:
        print_warning(f"Could not log metrics: {e}")

    # Stop EC2 (unless --no-stop)
    if not args.no_stop:
        print("\n" + "="*60)
        response = input(f"{Colors.YELLOW}💡 Stop EC2 instance? (Y/n): {Colors.END}").strip().lower()

        if response in ['', 'y', 'yes']:
            stop_ec2(instance_id)
        else:
            print_warning("EC2 instance left running")
            print(f"   MLflow URL: {mlflow_url}")
            print(f"   Stop manually: aws ec2 stop-instances --instance-ids {instance_id} --region us-east-1")
    else:
        print_warning("EC2 instance left running (--no-stop flag)")
        print(f"   MLflow URL: {mlflow_url}")

    print(f"\n{Colors.BOLD}{Colors.GREEN}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.GREEN}✅ Model synchronization complete!{Colors.END}")
    print(f"{Colors.BOLD}{Colors.GREEN}{'='*60}{Colors.END}\n")

    print("Next steps:")
    print(f"  {Colors.BLUE}▶{Colors.END} Run predictions: python WMS/src/predicts.py")
    print(f"  {Colors.BLUE}▶{Colors.END} Check model: dir WMS\\models\\production.pth")

if __name__ == "__main__":
    main()
