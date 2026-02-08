#!/usr/bin/env python3
"""
Fetch AWS credentials from GitHub repository secrets.

Usage:
    python WMS/scripts/fetch_aws_credentials.py

This script:
1. Uses GitHub CLI to fetch AWS credentials from repo secrets
2. Sets them as environment variables
3. Optionally saves to ~/.aws/credentials file

Requires:
- GitHub CLI (gh) installed and authenticated
- Read access to repository secrets (requires repo admin or secrets read permission)
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path


def check_gh_cli():
    """Check if GitHub CLI is available."""
    try:
        subprocess.run(
            ["gh", "--version"],
            capture_output=True,
            check=True
        )
        return True
    except (FileNotFoundError, subprocess.CalledProcessError):
        print("❌ GitHub CLI (gh) not found or not working")
        print("\nInstall instructions:")
        print("  Windows: winget install --id GitHub.cli")
        print("  macOS:   brew install gh")
        print("  Linux:   See https://github.com/cli/cli#installation")
        print("\nThen authenticate: gh auth login")
        return False


def fetch_secret(secret_name):
    """Fetch a secret from GitHub repository."""
    try:
        result = subprocess.run(
            ["gh", "secret", "list", "--json", "name"],
            capture_output=True,
            text=True,
            check=True
        )

        secrets = json.loads(result.stdout)
        secret_names = [s['name'] for s in secrets]

        if secret_name not in secret_names:
            return None

        # Note: gh CLI cannot read secret values for security reasons
        # Secrets can only be accessed in GitHub Actions workflows
        return None

    except subprocess.CalledProcessError:
        return None


def print_instructions():
    """Print instructions for setting up AWS credentials."""
    print("\n" + "="*70)
    print("AWS CREDENTIALS SETUP")
    print("="*70)

    print("\n📋 GitHub Secrets are encrypted and cannot be read directly.")
    print("   They can only be accessed in GitHub Actions workflows.\n")

    print("For local development, set AWS credentials manually:\n")

    print("Option 1: Environment Variables (Temporary)")
    print("-" * 50)
    print("# Get credentials from AWS Academy Lab:")
    print("# 1. AWS Academy → Learner Lab → Start Lab")
    print("# 2. AWS Details → Show AWS CLI credentials")
    print("# 3. Copy and run:\n")
    print("# Windows PowerShell:")
    print('$env:AWS_ACCESS_KEY_ID="ASIA..."')
    print('$env:AWS_SECRET_ACCESS_KEY="..."')
    print('$env:AWS_SESSION_TOKEN="..."')
    print("\n# Linux/macOS:")
    print('export AWS_ACCESS_KEY_ID="ASIA..."')
    print('export AWS_SECRET_ACCESS_KEY="..."')
    print('export AWS_SESSION_TOKEN="..."\n')

    print("Option 2: AWS Credentials File (Persistent)")
    print("-" * 50)
    aws_dir = Path.home() / ".aws"
    creds_file = aws_dir / "credentials"
    print(f"# Edit file: {creds_file}")
    print("# Add:\n")
    print("[default]")
    print("aws_access_key_id = ASIA...")
    print("aws_secret_access_key = ...")
    print("aws_session_token = ...\n")

    print("Option 3: Quick Setup Script")
    print("-" * 50)
    print("# Create a script (set-aws-creds.ps1 or .sh):")
    print("# Paste credentials from AWS Academy")
    print("# Run before using sync_model_aws.py\n")

    print("="*70)
    print("\n✅ After setting credentials, verify with:")
    print("   aws sts get-caller-identity")
    print("\n✅ Then run model sync:")
    print("   python WMS/scripts/sync_model_aws.py\n")


def check_current_credentials():
    """Check if AWS credentials are currently set."""
    print("\n🔍 Checking current AWS credentials...\n")

    # Check environment variables
    env_vars = ["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_SESSION_TOKEN"]
    has_env = all(os.environ.get(var) for var in env_vars)

    if has_env:
        print("✅ AWS credentials found in environment variables")
        # Verify they work
        try:
            result = subprocess.run(
                ["aws", "sts", "get-caller-identity"],
                capture_output=True,
                text=True,
                check=True
            )
            identity = json.loads(result.stdout)
            print(f"   Account: {identity['Account']}")
            print(f"   User: {identity['Arn'].split('/')[-1]}")
            print("\n✅ Credentials are valid and working!")
            return True
        except (subprocess.CalledProcessError, json.JSONDecodeError, KeyError):
            print("⚠️  Credentials exist but may be invalid or expired")
            return False

    # Check credentials file
    creds_file = Path.home() / ".aws" / "credentials"
    if creds_file.exists():
        print(f"✅ AWS credentials file found: {creds_file}")
        # Verify they work
        try:
            result = subprocess.run(
                ["aws", "sts", "get-caller-identity"],
                capture_output=True,
                text=True,
                check=True
            )
            identity = json.loads(result.stdout)
            print(f"   Account: {identity['Account']}")
            print(f"   User: {identity['Arn'].split('/')[-1]}")
            print("\n✅ Credentials are valid and working!")
            return True
        except (subprocess.CalledProcessError, json.JSONDecodeError, KeyError):
            print("⚠️  Credentials file exists but may be invalid or expired")
            return False

    print("❌ No AWS credentials found")
    return False


def main():
    parser = argparse.ArgumentParser(
        description="Fetch AWS credentials from GitHub or check existing credentials"
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Check if AWS credentials are currently configured"
    )

    args = parser.parse_args()

    print("\n" + "="*70)
    print("AWS CREDENTIALS HELPER")
    print("="*70)

    if args.check:
        has_creds = check_current_credentials()
        sys.exit(0 if has_creds else 1)

    # Check if gh CLI is available
    if not check_gh_cli():
        print_instructions()
        sys.exit(1)

    # Explain limitation
    print("\n📋 GitHub Secrets Management:\n")
    print("GitHub secrets are encrypted and cannot be retrieved via CLI.")
    print("They are only accessible in GitHub Actions workflow runs.\n")
    print("For local development, you need to set AWS credentials manually.")
    print("(This is a security feature - secrets are write-only via CLI)\n")

    # Check current credentials
    has_creds = check_current_credentials()

    if not has_creds:
        print_instructions()
        sys.exit(1)


if __name__ == "__main__":
    main()
