# Helper Scripts

Utility scripts for common operations.

## sync_model_aws.py - Automatic Model Synchronization (AWS CLI)

**Purpose:** Automatically download the latest Production model from MLflow using AWS CLI directly.

**✅ Recommended:** Simpler than sync_model.py - uses AWS CLI directly (no GitHub CLI needed!)

### Quick Start

```bash
# Automatic mode (AWS CLI)
python WMS/scripts/sync_model_aws.py

# Windows: just double-click sync_model_aws.bat in project root
```

### Prerequisites

1. **AWS CLI** (you already have it!)
   ```bash
   aws --version
   ```

2. **AWS Credentials configured:**
   - Option A: `~/.aws/credentials` file
   - Option B: Environment variables (AWS_ACCESS_KEY_ID, etc.)

3. **Terraform infrastructure deployed** (EC2 instance with tag `wms-k3s`)

### Usage Options

```bash
# Basic usage
python WMS/scripts/sync_model_aws.py

# Force re-download
python WMS/scripts/sync_model_aws.py --force

# Keep EC2 running after download
python WMS/scripts/sync_model_aws.py --no-stop
```

---

## sync_model.py - Automatic Model Synchronization (GitHub CLI)

**Purpose:** Automatically download the latest Production model from MLflow using GitHub Actions workflows.

**Note:** Requires GitHub CLI installed and configured. Use `sync_model_aws.py` if you don't have GitHub CLI.

### Quick Start

```bash
# Automatic mode (recommended)
python WMS/scripts/sync_model.py

# Windows: just double-click sync_model.bat in project root
```

### What It Does

1. ✅ Checks GitHub CLI is installed and authenticated
2. 🚀 Starts EC2 instance via GitHub Actions workflow
3. ⏳ Waits for workflow to complete (~3-5 minutes)
4. 📡 Extracts MLflow URL from workflow output
5. 📥 Downloads Production model to `WMS/models/production.pth`
6. 🛑 Asks if you want to stop EC2 (saves costs)

### Usage Options

```bash
# Basic usage - full automation
python WMS/scripts/sync_model.py

# Keep EC2 running after download (for multiple operations)
python WMS/scripts/sync_model.py --keep-running

# Force re-download even if model is cached
python WMS/scripts/sync_model.py --force

# Use existing EC2 instance (skip start/stop)
python WMS/scripts/sync_model.py --mlflow-url http://<EC2_IP>:5000
```

### Prerequisites

1. **GitHub CLI (gh):**
   ```bash
   # Windows
   winget install --id GitHub.cli

   # macOS
   brew install gh

   # Linux
   # See: https://github.com/cli/cli#installation
   ```

2. **Authentication:**
   ```bash
   gh auth login
   ```

3. **Repository Access:**
   - Must be run from project root or have access to `.github/workflows/`

### Troubleshooting

#### "GitHub CLI not found"
- Install GitHub CLI (see Prerequisites above)
- Make sure `gh` is in your PATH

#### "GitHub CLI not authenticated"
```bash
gh auth login
```

#### "Workflow did not complete in time"
- Check workflow manually: `gh run list --workflow=ec2-manual-control.yaml`
- View specific run: `gh run view <RUN_ID>`
- EC2 might be taking longer to start (first boot takes ~5 minutes)

#### "Could not extract MLflow URL"
- Workflow completed but URL not in output
- Manually check: `gh run view <RUN_ID>`
- Look for "Public IP" and use: `python WMS/src/download_model.py --mlflow-uri http://<IP>:5000`

#### AWS Session Expired (AWS Academy Lab)
- AWS Academy sessions expire after ~4 hours
- Credentials in GitHub Secrets need to be updated
- Go to AWS Academy → Start Lab → AWS Details → Update GitHub Secrets

### Manual Alternative

If the automatic script doesn't work, use manual method:

```bash
# 1. Start EC2
gh workflow run ec2-manual-control.yaml -f action=start

# 2. Wait 3-5 minutes, check status
gh run list --workflow=ec2-manual-control.yaml --limit=1

# 3. Get workflow output
gh run view <RUN_ID>  # Look for Public IP

# 4. Download model
python WMS/src/download_model.py --mlflow-uri http://<EC2_IP>:5000

# 5. Stop EC2
gh workflow run ec2-manual-control.yaml -f action=stop
```

### Cost Optimization

- Script automatically offers to stop EC2 after download
- EC2 costs ~$0.02/hour when running (t3.large)
- Model download takes ~30 seconds once EC2 is ready
- Total cost per sync: ~$0.002 (less than 1 cent)

### For Developers

The script uses:
- `gh workflow run` - Trigger GitHub Actions workflows
- `gh run list` - List workflow runs
- `gh run view` - Get workflow run details and logs
- `subprocess` - Execute shell commands
- `json` - Parse GitHub CLI JSON output

See source code for implementation details.
