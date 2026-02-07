# End-to-End Test Guide

Complete testing procedure for the automated ML pipeline from data upload to deployment.

## Test Overview

This test validates the complete workflow:
```
Data Upload → QA → DVC → PR → Training (3x) → Quality Gate → Approve → Deploy → Verify
```

**Estimated time:** 30-45 minutes
**Prerequisites:** EC2 running, MLflow active, GitHub Actions runner configured

---

## Phase 0: Pre-Test Verification

### Check Infrastructure Status

```bash
# SSH into EC2 (AWS Academy Lab)
ssh -i ~/.ssh/labsuser.pem ec2-user@<EC2_PUBLIC_IP>

# Verify MLflow is running
curl http://localhost:5000/health
# Expected: 200 OK

# Verify k3s cluster
kubectl get nodes
# Expected: Ready

# Verify serving deployment
kubectl get pods -l app=wms-model
# Expected: Running

# Check GitHub Actions runner
cd ~/actions-runner
./run.sh --check
# Expected: Runner is configured and running
```

### Check Current Model

```bash
# On EC2, check MLflow for current Production model
python3 << 'EOF'
import mlflow
from mlflow.tracking import MlflowClient

mlflow.set_tracking_uri("http://localhost:5000")
client = MlflowClient()

try:
    versions = client.search_model_versions("name='water-meter-segmentation'")
    prod_versions = [v for v in versions if v.current_stage == 'Production']

    if prod_versions:
        v = prod_versions[0]
        print(f"Current Production: Version {v.version}")
        print(f"Run ID: {v.run_id}")
    else:
        print("No Production model found (OK for first test)")
except Exception as e:
    print(f"Error: {e}")
EOF
```

---

## Phase 1: Prepare Test Data

### Option A: Use Existing Training Image (Quick Test)

```bash
# On local machine in repo root
cd WMS/data/training

# Copy an existing image/mask pair
cp images/image001.jpg images/test_e2e_001.jpg
cp masks/image001.png masks/test_e2e_001.png

# Verify files exist
ls -lh images/test_e2e_001.jpg masks/test_e2e_001.png
```

### Option B: Create New Test Data (Full Test)

If you have new water meter images with masks:

```bash
# Add new image and mask
cp /path/to/new/image.jpg WMS/data/training/images/test_e2e_001.jpg
cp /path/to/new/mask.png WMS/data/training/masks/test_e2e_001.png

# Verify resolution is 512x512
file WMS/data/training/images/test_e2e_001.jpg
file WMS/data/training/masks/test_e2e_001.png
```

---

## Phase 2: Configure Git Hook (If Not Done)

```bash
# On local machine
cd /path/to/Water-Meters-Segmentation-Autimatization

# Run setup script
./setup-hooks.sh

# Verify hook is configured
git config core.hooksPath
# Expected: devops/hooks
```

---

## Phase 3: Push Test Data

### Commit and Push

```bash
# Stage test data
git add WMS/data/training/images/test_e2e_001.jpg
git add WMS/data/training/masks/test_e2e_001.png
git status

# Commit
git commit -m "test: E2E workflow validation"

# Push to main (hook will intercept)
git push origin main
```

### Expected Output

```
🔍 Checking for training data changes...

╔════════════════════════════════════════════════════════════╗
║  🚫 Direct push to main with training data blocked        ║
╚════════════════════════════════════════════════════════════╝

Training data changes detected. Creating data branch...
📦 Creating branch: data/20260207-183045
🚀 Pushing to data/20260207-183045...

✅ Success! Your changes are now on branch: data/20260207-183045

Next steps:
  1. GitHub Actions will validate your data
  2. If valid, a Pull Request will be created automatically
  3. Training will run automatically
  ...
```

**⏱️ Timeline:** Hook execution ~5-10 seconds

---

## Phase 4: Monitor Data Upload Workflow

### Watch GitHub Actions

Navigate to:
```
https://github.com/Rafallost/Water-Meters-Segmentation-Autimatization/actions
```

### Expected: "Data Upload & Validation" Workflow

**Steps to verify:**

1. ✅ **Checkout code** - Should pass
2. ✅ **Setup Python** - Should pass
3. ✅ **Install dependencies** - Should pass
4. ✅ **Run Data QA Validation** - Should pass (if data is valid)
5. ✅ **Configure DVC** - Should pass
6. ✅ **DVC add and push training data** - Should pass (pushes to S3)
7. ✅ **Create Pull Request** - Should pass (creates PR automatically)

**⏱️ Timeline:** ~2-3 minutes

### Verification Checkpoint 1: PR Created

Check for new PR:
```
https://github.com/Rafallost/Water-Meters-Segmentation-Autimatization/pulls
```

**Expected PR:**
- Title: `Training Data Update: data/20260207-183045`
- Body: Validation report with image/mask counts
- Status: Checks running

---

## Phase 5: Monitor Training Workflow

### Watch "Train Model" Workflow

The training workflow should start automatically on the PR.

**Expected: 3 Training Attempts**

Each attempt runs sequentially (not parallel):

**Attempt 1:**
1. ✅ Checkout code
2. ✅ Set up Python
3. ✅ Install dependencies
4. ✅ Pull training data with DVC
5. ✅ Data Quality Assurance
6. 🔄 Train model (Attempt 1) - **Takes 5-10 minutes**
7. ✅ Get training results
8. ✅ Upload results artifact

**Attempt 2:** (same steps, different seed)

**Attempt 3:** (same steps, different seed)

**Then: Aggregate Results Job**
1. ✅ Download all results
2. ✅ Aggregate and evaluate
3. ✅/❌ Promote best model to Production (if improved)
4. ✅ Comment on PR with all results
5. ✅/❌ Auto-approve PR (if improved)

**⏱️ Timeline:** ~20-30 minutes total (3 attempts × 7-10 min each + aggregation)

### Verification Checkpoint 2: Training Results

**Check PR comments for training results:**

Expected comment format:
```markdown
## ✅ Training Results (3 attempts)

📈 **MODEL IMPROVED**

### All Attempts

| Attempt | Dice | IoU | Passed | Improved |
|---------|------|-----|--------|----------|
| 1 🏆    | 0.9312 | 0.8901 | ✅ | 📈 |
| 2       | 0.9201 | 0.8798 | ✅ | - |
| 3       | 0.9156 | 0.8723 | ✅ | - |

### Best Result (Attempt 1)
...

🚀 **Best model has been promoted to Production**
```

---

## Phase 6: Verify Model Promotion

### Check MLflow

```bash
# SSH to EC2
ssh -i ~/.ssh/labsuser.pem ec2-user@<EC2_PUBLIC_IP>

# Check Production model
python3 << 'EOF'
import mlflow
from mlflow.tracking import MlflowClient

mlflow.set_tracking_uri("http://localhost:5000")
client = MlflowClient()

versions = client.search_model_versions("name='water-meter-segmentation'")
prod_versions = [v for v in versions if v.current_stage == 'Production']

if prod_versions:
    v = prod_versions[0]
    print(f"✅ Production Model: Version {v.version}")
    print(f"Run ID: {v.run_id}")

    # Get metrics
    run = client.get_run(v.run_id)
    print(f"Dice: {run.data.metrics.get('val_dice', 'N/A')}")
    print(f"IoU: {run.data.metrics.get('val_iou', 'N/A')}")
else:
    print("❌ No Production model found")
EOF
```

**Expected:** New Production model with improved metrics

---

## Phase 7: Merge Pull Request

### If Auto-Approved

The PR should have an approval from `github-actions[bot]`:
```
✅ Auto-approved: Model improved over baseline

🤖 This PR has been automatically approved because training
produced a model that improves upon the baseline metrics.
```

### Merge the PR

Via GitHub UI:
1. Go to the PR
2. Click **Merge pull request**
3. Confirm merge

Or via CLI:
```bash
gh pr merge <PR_NUMBER> --squash
```

**⏱️ Timeline:** Manual action, ~1 minute

---

## Phase 8: Monitor Deployment

### Watch "Release and Deploy" Workflow

After merge to main, the deployment workflow should trigger.

**Expected Steps:**
1. ✅ Checkout code
2. ✅ Login to ECR
3. ✅ Build + Push Docker image (~5-10 minutes)
4. ✅ Deploy to k3s
5. ✅ Wait for deployment
6. ✅ Run smoke tests

**⏱️ Timeline:** ~8-12 minutes

---

## Phase 9: Verify Deployment

### Check Pod Status

```bash
# SSH to EC2
kubectl get pods -l app=wms-model

# Expected:
# NAME                         READY   STATUS    RESTARTS   AGE
# wms-model-xxxxxxxxxx-xxxxx   1/1     Running   0          2m
```

### Check Service Health

```bash
# Health check
curl http://localhost:30080/health

# Expected:
# {"status":"healthy","model_version":"..."}

# Metrics endpoint
curl http://localhost:30080/metrics

# Expected: Prometheus metrics
```

### Test Prediction

```bash
# Test prediction with sample image
# Assuming you have a test image

# Option 1: Using curl (if you have base64 encoded image)
curl -X POST http://localhost:30080/predict \
  -H "Content-Type: application/json" \
  -d '{"image_data": "BASE64_ENCODED_IMAGE"}'

# Option 2: Using Python
python3 << 'EOF'
import requests
import base64
from pathlib import Path

# Read test image
img_path = Path("WMS/data/training/images/test_e2e_001.jpg")
with open(img_path, "rb") as f:
    img_base64 = base64.b64encode(f.read()).decode()

# Make prediction
response = requests.post(
    "http://localhost:30080/predict",
    json={"image_data": img_base64}
)

print(f"Status: {response.status_code}")
if response.status_code == 200:
    print("✅ Prediction successful!")
    # Response contains mask
else:
    print(f"❌ Prediction failed: {response.text}")
EOF
```

**Expected:** 200 OK with predicted mask

---

## Phase 10: Final Verification

### System Status Summary

```bash
# Run comprehensive check
python3 << 'EOF'
import requests
import mlflow
from mlflow.tracking import MlflowClient

print("="*60)
print("SYSTEM STATUS CHECK")
print("="*60)
print()

# 1. MLflow
print("1. MLflow Tracking Server")
try:
    response = requests.get("http://localhost:5000/health")
    if response.status_code == 200:
        print("   ✅ MLflow is running")
    else:
        print(f"   ❌ MLflow health check failed: {response.status_code}")
except Exception as e:
    print(f"   ❌ Cannot reach MLflow: {e}")

# 2. Production Model
print("\n2. Production Model")
try:
    mlflow.set_tracking_uri("http://localhost:5000")
    client = MlflowClient()
    versions = client.search_model_versions("name='water-meter-segmentation'")
    prod_versions = [v for v in versions if v.current_stage == 'Production']

    if prod_versions:
        v = prod_versions[0]
        print(f"   ✅ Production Version: {v.version}")
        run = client.get_run(v.run_id)
        dice = run.data.metrics.get('val_dice', 0)
        iou = run.data.metrics.get('val_iou', 0)
        print(f"   📊 Dice: {dice:.4f} | IoU: {iou:.4f}")
    else:
        print("   ❌ No Production model")
except Exception as e:
    print(f"   ❌ Error: {e}")

# 3. Serving API
print("\n3. Serving API")
try:
    response = requests.get("http://localhost:30080/health")
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ API is healthy")
        print(f"   📦 Model version: {data.get('model_version', 'unknown')}")
    else:
        print(f"   ❌ API health check failed: {response.status_code}")
except Exception as e:
    print(f"   ❌ Cannot reach API: {e}")

print()
print("="*60)
print("END-TO-END TEST COMPLETE")
print("="*60)
EOF
```

---

## Expected Test Results

### ✅ Success Criteria

- [ ] Git hook intercepted push to main
- [ ] Data branch created automatically
- [ ] Data QA workflow passed
- [ ] DVC pushed data to S3
- [ ] Pull Request created automatically
- [ ] Training workflow ran 3 attempts
- [ ] Best model improved over baseline
- [ ] PR auto-approved by workflow
- [ ] Model promoted to Production in MLflow
- [ ] PR merged to main
- [ ] Docker image built and pushed to ECR
- [ ] k3s deployment updated
- [ ] Health check returns 200 OK
- [ ] Prediction endpoint works

### ⏱️ Total Time Estimate

- Phase 1-3 (Prep): ~5 minutes
- Phase 4 (Data Upload): ~3 minutes
- Phase 5 (Training): ~25 minutes
- Phase 6-7 (Verification + Merge): ~5 minutes
- Phase 8 (Deployment): ~10 minutes
- Phase 9-10 (Verification): ~5 minutes

**Total: ~50 minutes**

---

## Troubleshooting

### Data QA Failed

**Problem:** Data validation fails
**Check:**
```bash
# View data-upload workflow logs
# Look for specific validation errors
```
**Solution:** Fix data issues (resolution, binary masks, file pairs) and push again

### No Training Runs

**Problem:** Training workflow doesn't start
**Check:**
- PR was created
- Workflows are enabled in GitHub Settings
- Self-hosted runner is online

### All Training Attempts Failed Quality Gate

**Problem:** No attempt improved model
**Possible causes:**
- Not enough new training data
- Data quality issues
- Hyperparameter tuning needed

**Solution:** Add more/better data or adjust training config

### Deployment Failed

**Problem:** k3s deployment fails
**Check:**
```bash
kubectl describe pod <pod-name>
kubectl logs <pod-name>
```
**Common issues:**
- Image pull errors (ECR authentication)
- Resource limits (memory/CPU)
- Configuration errors

---

## Cleanup After Test

### Remove Test Data (Optional)

```bash
# On local machine
git checkout main
git pull origin main

# Remove test files
rm WMS/data/training/images/test_e2e_001.jpg
rm WMS/data/training/masks/test_e2e_001.png

# Commit cleanup
git add WMS/data/training/
git commit -m "cleanup: remove E2E test data"
git push origin main
```

### Verify System Still Healthy

After cleanup, run Phase 10 verification again.

---

## Next Steps

After successful E2E test:

1. ✅ **Document results** - Take screenshots, save logs
2. ✅ **Update thesis** - Include E2E test results
3. ✅ **Cost calculation** - Track AWS costs for thesis
4. ⏭️ **Manual comparison** - Task #11 (for thesis)
5. ⏭️ **Documentation** - Tasks #13-15
6. 🚨 **Cleanup AWS** - When testing is complete

**IMPORTANT:** Remember to run cleanup-aws.sh when done to avoid unnecessary AWS charges!
