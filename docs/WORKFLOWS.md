# Workflows & Pipelines Explained

This document explains **all GitHub Actions workflows** in this project and when they run.

---

## 🎯 Overview: The Complete Flow

```
┌─────────────────────────────────────────────────────────────┐
│  USER UPLOADS NEW TRAINING DATA                             │
│  (push to WMS/data/training/)                               │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│  1. DATA VALIDATION (data-qa.yaml)                          │
│     • Checks image/mask pairs                               │
│     • Validates resolutions                                 │
│     • Ensures binary masks (0/255)                          │
│     → PASS: Continue   → FAIL: Stop with error              │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│  2. DATA UPLOAD (data-upload.yaml)                          │
│     • Versions data with DVC → S3                           │
│     • Creates Pull Request to main                          │
│     • Triggers training workflow                            │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│  3. TRAINING (train.yml) - 3 Attempts                       │
│     • Starts EC2 infrastructure (ephemeral)                 │
│     • Runs 3 training attempts with different seeds         │
│     • Logs to MLflow                                        │
│     • Compares to baseline (Dice ≥0.9075, IoU ≥0.8665)     │
│     → IMPROVED: Promote to Production                       │
│     → NOT IMPROVED: Reject PR                               │
│     • Stops EC2 infrastructure                              │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼ (if model improved)
┌─────────────────────────────────────────────────────────────┐
│  4. MERGE TO MAIN                                           │
│     • PR auto-approved by workflow                          │
│     • User merges PR                                        │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│  5. DEPLOYMENT (automatic on merge to main)                 │
│     • Build Docker image                                    │
│     • Push to ECR                                           │
│     • Deploy to k3s with Helm                               │
│     • Run smoke tests                                       │
└─────────────────────────────────────────────────────────────┘
```

---

## 📋 All Workflows Explained

### 1. **Data Quality Assurance** (`data-qa.yaml`)

**Purpose:** Quick validation check before expensive training
**Triggers:** On pull request to main
**Duration:** ~20-30 seconds

**What it does:**
- Checks that every image has a corresponding mask
- Validates image and mask resolutions match
- Ensures masks are binary (only 0 and 255 values)
- Checks for sufficient mask coverage

**Outcomes:**
- ✅ PASS → Training can proceed
- ❌ FAIL → PR blocked, shows errors

**Why you need it:** Prevents wasting 10+ minutes of training on bad data.

---

### 2. **Data Upload & Validation** (`data-upload.yaml`)

**Purpose:** Version data and create PR automatically
**Triggers:** When you push to `data/*` branches
**Duration:** ~40-60 seconds

**What it does:**
1. Runs data QA validation
2. If POC mode (data in Git): Commits data directly
3. If production mode: Adds data to DVC, pushes to S3
4. Creates a Pull Request to main branch
5. Adds validation report as PR comment

**Outcomes:**
- ✅ PASS → PR created, training workflow triggered
- ❌ FAIL → Commit comment with errors, no PR created

**Why you need it:** Automates the PR creation process, you don't need to create PRs manually.

---

### 3. **Train Model** (`train.yml`) ⭐ **MAIN WORKFLOW**

**Purpose:** Train model with ephemeral infrastructure
**Triggers:** On pull request to main (when data changes detected)
**Duration:** ~10-12 minutes

**What it does:**

#### Job 1: Start EC2 Infrastructure (`start-infra`)
- Finds EC2 instance by tag
- Starts the instance
- Waits for MLflow to be healthy
- Returns MLflow URL for training jobs
- **Duration:** ~20-30 seconds

#### Jobs 2-4: Training Attempts (`train`, matrix: [1, 2, 3])
- Runs on GitHub-hosted runners (free!)
- Each uses a different random seed
- Connects to MLflow on EC2
- Trains U-Net model
- Logs metrics to MLflow
- **Duration:** ~3 minutes each (parallel)

#### Job 5: Aggregate Results (`aggregate-results`)
- Collects metrics from all 3 attempts
- Finds best result (highest Dice score)
- Checks quality gate:
  - **Baseline:** Dice 0.9275, IoU 0.8865
  - **Threshold:** Dice ≥0.9075, IoU ≥0.8665 (2% tolerance)
- If ANY attempt improved: Promotes to MLflow Production
- Posts results table as PR comment
- **Duration:** ~10 seconds

#### Job 6: Stop EC2 Infrastructure (`stop-infra`)
- Stops EC2 instance to save costs
- Runs even if training failed
- **Duration:** ~10 seconds

**Outcomes:**
- 📈 **IMPROVED:** Model promoted, PR auto-approved, ready to merge
- 📊 **NO IMPROVEMENT:** PR rejected with explanation

**Why you need it:** Core training pipeline with cost optimization (EC2 only runs during training).

**Cost savings:** ~$14/month (EC2 runs ~10 min/training instead of 24/7)

---

### 4. **CI Pipeline** (`ci.yaml`)

**Purpose:** Code quality checks
**Triggers:** On every pull request and push to main
**Duration:** ~2-3 minutes

**What it does:**
- Lints Python code (Ruff)
- Runs unit tests (pytest)
- Checks code formatting

**Outcomes:**
- ✅ PASS → Code quality OK
- ❌ FAIL → Fix linting/test errors before merging

**Why you need it:** Prevents broken code from reaching main branch.

---

### 5. **EC2 Control** (`ec2-control.yaml`)

**Purpose:** Reusable workflow for starting/stopping EC2
**Triggers:** Called by other workflows (not directly)
**Duration:** 20-30 seconds

**What it does:**
- **START:** Starts EC2, waits for MLflow health check, returns URL
- **STOP:** Stops EC2 instance

**Why you need it:** Centralizes EC2 management, used by train.yml.

---

### 6. **Data Staging → Branch** (`data-staging.yaml`)

**Purpose:** Automatically create timestamped branch for new data
**Triggers:** When you push to magic branch `data/staging` or `data/new`
**Duration:** ~5 seconds

**What it does:**
1. Creates timestamped branch (e.g., `data/20260207-220516`)
2. Pushes your data to that branch
3. That triggers data-upload workflow

**Outcomes:**
- New branch created automatically
- Data upload workflow runs on that branch

**Why you need it:** Convenience - you don't need to manually create timestamped branches.

---

## 🎬 Typical Workflow Execution Order

### Scenario: You have new training data

```
1. You: git push origin data/staging
   ↓
2. data-staging.yaml creates data/20260207-123456 branch
   ↓
3. data-upload.yaml runs:
   - data-qa.yaml validates data ✅
   - Creates PR #5
   ↓
4. train.yml runs on PR #5:
   - start-infra: EC2 starts
   - train (1,2,3): 3 parallel training jobs
   - aggregate-results: Best model promoted ✅
   - stop-infra: EC2 stops
   - Comment on PR: "📈 MODEL IMPROVED"
   - Auto-approve PR
   ↓
5. You: Merge PR #5
   ↓
6. (Future) Deploy workflow: Build → ECR → k3s
```

---

## 🚨 Common Failure Scenarios

### ❌ Data QA Failed
**Workflow:** data-qa.yaml
**Error:** "Non-binary mask values" or "Resolution mismatch"
**Fix:** Run `python devops/scripts/data-qa.py WMS/data/training/` locally to see errors. Fix data and push again.

### ❌ Training Failed (All 3 Attempts)
**Workflow:** train.yml
**Error:** "No training attempt improved the model"
**Reason:** New data didn't improve model performance
**Fix:** Review training logs, check if data is sufficient/correct, or adjust hyperparameters.

### ❌ EC2 Connection Timeout
**Workflow:** train.yml (start-infra)
**Error:** "MLflow health check timeout"
**Reason:** EC2 instance not starting or port 5000 blocked
**Fix:** Check AWS Console, verify security group allows port 5000.

### ❌ PR Comment Failed (403)
**Workflow:** train.yml
**Error:** "Resource not accessible by integration"
**Reason:** Missing permissions
**Fix:** Already fixed! (Added `permissions: issues: write` to train.yml)

---

## 🔄 Workflow Dependencies

```
data-staging.yaml (optional convenience)
        ↓
data-upload.yaml (creates PR)
        ↓ triggers on PR
data-qa.yaml (validation check)
        ↓ if passes
train.yml (main training)
        ↓ uses
ec2-control.yaml (infrastructure management)
```

**ci.yaml** runs independently on all PRs.

---

## ⚙️ Merge Conditions

A PR can be merged when:

1. ✅ **Data QA passed** (data-qa.yaml)
2. ✅ **CI tests passed** (ci.yaml)
3. ✅ **Training improved model** (train.yml shows "📈 MODEL IMPROVED")
4. ✅ **PR auto-approved** by training workflow (optional, can merge manually)

**You decide when to merge** - the workflow won't auto-merge, just auto-approve if model improved.

---

## 💡 Tips

- **Don't merge until you see training results comment!** Wait for train.yml to finish (~10 min)
- **Check MLflow:** http://<EC2-IP>:5000 to see all training runs and metrics
- **Costs:** EC2 only runs during training (~$4/month instead of ~$18/month)
- **Manual trigger:** You can manually trigger train.yml from Actions tab (workflow_dispatch)

---

## 📚 Related Documentation

- **SETUP.md** - How to set up the infrastructure
- **USAGE.md** - Step-by-step guide for uploading data
- **ARCHITECTURE.md** - System design overview
- **devops/PLAN.md** - Original implementation plan
