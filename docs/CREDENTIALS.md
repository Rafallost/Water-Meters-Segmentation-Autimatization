# AWS Credentials Management Guide

Guide for managing AWS credentials for local development and CI/CD.

---

## 🔐 Understanding AWS Credentials

### Where Credentials Are Used

1. **GitHub Actions Workflows** (Automatic)
   - Stored in GitHub Secrets
   - Automatically injected into workflow runs
   - Secure and encrypted

2. **Local Development** (Manual Setup Required)
   - Used by `sync_model_aws.py` and other AWS CLI tools
   - Must be configured manually (security best practice)
   - GitHub Secrets cannot be read locally (by design)

---

## 📋 For Local Development

### Check Current Credentials

```bash
# Quick check
python WMS/scripts/fetch_aws_credentials.py --check

# Or manually
aws sts get-caller-identity
```

### Option 1: Environment Variables (Temporary - Recommended for AWS Academy)

**Windows PowerShell:**
```powershell
# Get from AWS Academy Lab → AWS Details → Show AWS CLI credentials
$env:AWS_ACCESS_KEY_ID="ASIA..."
$env:AWS_SECRET_ACCESS_KEY="..."
$env:AWS_SESSION_TOKEN="..."

# Verify
aws sts get-caller-identity
```

**Linux/macOS:**
```bash
# Get from AWS Academy Lab → AWS Details → Show AWS CLI credentials
export AWS_ACCESS_KEY_ID="ASIA..."
export AWS_SECRET_ACCESS_KEY="..."
export AWS_SESSION_TOKEN="..."

# Verify
aws sts get-caller-identity
```

**Why this option:**
- ✅ Session tokens expire after ~4 hours (AWS Academy)
- ✅ No old credentials left on disk
- ✅ Clean session each time

### Option 2: Credentials File (Persistent)

**Location:**
- Windows: `C:\Users\<username>\.aws\credentials`
- Linux/macOS: `~/.aws/credentials`

**Content:**
```ini
[default]
aws_access_key_id = ASIA...
aws_secret_access_key = ...
aws_session_token = ...
```

**Create file:**
```bash
# Create directory
mkdir -p ~/.aws

# Edit file
nano ~/.aws/credentials  # Linux/macOS
notepad C:\Users\%USERNAME%\.aws\credentials  # Windows
```

**Why this option:**
- ✅ Persists across terminal sessions
- ❌ Need to update when session expires
- ❌ Old credentials may cause confusion

### Option 3: Helper Script (Recommended)

Create a reusable script:

**Windows:** `set-aws-creds.ps1`
```powershell
# Paste credentials from AWS Academy
$env:AWS_ACCESS_KEY_ID="ASIA..."
$env:AWS_SECRET_ACCESS_KEY="..."
$env:AWS_SESSION_TOKEN="..."

Write-Host "✅ AWS credentials set!" -ForegroundColor Green
aws sts get-caller-identity
```

**Linux/macOS:** `set-aws-creds.sh`
```bash
#!/bin/bash
# Paste credentials from AWS Academy
export AWS_ACCESS_KEY_ID="ASIA..."
export AWS_SECRET_ACCESS_KEY="..."
export AWS_SESSION_TOKEN="..."

echo "✅ AWS credentials set!"
aws sts get-caller-identity
```

**Usage:**
```bash
# Windows
.\set-aws-creds.ps1

# Linux/macOS
source set-aws-creds.sh

# Then run your commands
python WMS/scripts/sync_model_aws.py
```

---

## 🔧 For GitHub Actions

### Update Repository Secrets

1. **Go to AWS Academy Lab**
   - Start Lab
   - Wait for green dot (ready)

2. **Get Credentials**
   - Click "AWS Details"
   - Click "Show AWS CLI credentials"
   - Copy all three values

3. **Update GitHub Secrets**
   ```bash
   # Using GitHub CLI
   gh secret set AWS_ACCESS_KEY_ID --body "ASIA..."
   gh secret set AWS_SECRET_ACCESS_KEY --body "..."
   gh secret set AWS_SESSION_TOKEN --body "..."
   ```

   **Or via GitHub UI:**
   - Repository → Settings → Secrets and variables → Actions
   - Update existing secrets:
     - `AWS_ACCESS_KEY_ID`
     - `AWS_SECRET_ACCESS_KEY`
     - `AWS_SESSION_TOKEN`

4. **Verify in Workflow**
   - Trigger a workflow (e.g., manual training)
   - Check logs for "AWS credentials OK"

### When to Update Secrets

- ✅ **At start of each AWS Academy Lab session** (~4h validity)
- ✅ Before running training workflows
- ✅ When you see "unauthorized" errors in workflows

---

## 🚨 Troubleshooting

### "AWS credentials not configured"

**Symptom:** `sync_model_aws.py` fails with credential error

**Solution:**
```bash
# 1. Check if credentials exist
python WMS/scripts/fetch_aws_credentials.py --check

# 2. If not, set them (Option 1, 2, or 3 above)

# 3. Verify
aws sts get-caller-identity
```

### "ExpiredToken" or "InvalidToken"

**Symptom:** Credentials exist but AWS operations fail

**Cause:** AWS Academy Lab session expired (>4 hours)

**Solution:**
```bash
# 1. Go to AWS Academy → Restart Lab
# 2. Get new credentials
# 3. Update credentials (Option 1, 2, or 3)
# 4. Verify
aws sts get-caller-identity
```

### "UnauthorizedOperation" in workflow

**Symptom:** GitHub Actions workflow fails with permission errors

**Cause:** GitHub Secrets have expired credentials

**Solution:**
```bash
# Update GitHub Secrets (see "For GitHub Actions" section)
gh secret set AWS_ACCESS_KEY_ID --body "ASIA..."
gh secret set AWS_SECRET_ACCESS_KEY --body "..."
gh secret set AWS_SESSION_TOKEN --body "..."
```

### "No profile named 'default'"

**Symptom:** AWS CLI can't find credentials

**Solution:**
```bash
# Check if credentials file exists
cat ~/.aws/credentials  # Linux/macOS
type C:\Users\%USERNAME%\.aws\credentials  # Windows

# If not, create it (see Option 2)
```

---

## 🔒 Security Best Practices

### DO ✅

- ✅ Use environment variables for temporary sessions (AWS Academy)
- ✅ Update credentials at start of each lab session
- ✅ Add `.aws/` to `.gitignore` (already done)
- ✅ Use GitHub Secrets for workflows (never hardcode)
- ✅ Verify credentials before use: `aws sts get-caller-identity`

### DON'T ❌

- ❌ Commit credentials to Git
- ❌ Share credentials in Slack/Discord
- ❌ Use production credentials for testing
- ❌ Leave credentials in code comments
- ❌ Store credentials in unencrypted files

---

## 📚 Helper Scripts Reference

### fetch_aws_credentials.py

**Purpose:** Check and manage AWS credentials

**Usage:**
```bash
# Check current credentials
python WMS/scripts/fetch_aws_credentials.py --check

# Show setup instructions
python WMS/scripts/fetch_aws_credentials.py
```

**Output:**
- ✅ Credentials status (valid/invalid/missing)
- 📋 Setup instructions
- 🔍 Account and user info

---

## 🔗 Related Documentation

- [AWS CLI Configuration](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-files.html)
- [GitHub Encrypted Secrets](https://docs.github.com/en/actions/security-guides/encrypted-secrets)
- [AWS Academy Lab Guide](https://awsacademy.instructure.com/)
- [sync_model_aws.py Documentation](../WMS/scripts/README.md#sync_model_awspy)

---

## 📝 Quick Reference

| Task | Command |
|------|---------|
| Check credentials | `aws sts get-caller-identity` |
| Set env vars (Win) | `$env:AWS_ACCESS_KEY_ID="..."` |
| Set env vars (Linux) | `export AWS_ACCESS_KEY_ID="..."` |
| Edit creds file | `nano ~/.aws/credentials` |
| Update GitHub secret | `gh secret set AWS_ACCESS_KEY_ID` |
| Verify with helper | `python WMS/scripts/fetch_aws_credentials.py --check` |
| Run model sync | `python WMS/scripts/sync_model_aws.py` |
