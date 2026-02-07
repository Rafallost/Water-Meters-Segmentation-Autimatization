# Configuration & Deployment Guide

**Project:** Water Meters Segmentation - MLOps Automation
**Date:** 2026-02-07
**Session:** Complete Infrastructure Setup (4-hour implementation)

---

## 🎯 Session Goal

Complete implementation of all critical phases:
- Phase 5: AWS Infrastructure (Terraform)
- Phase 6: Application Deployment
- Task #16: Training Pipeline
- Phase 2: Core Scripts
- Phase 8: Cleanup Script

---

## ⚙️ Phase 5: AWS Infrastructure Setup

### Prerequisites
- AWS Academy Lab session started
- AWS credentials configured
- IP address: `46.112.70.5`
- Account ID: `055677744286`
- Region: `us-east-1`

### Step 1: Initialize Terraform

```bash
cd Water-Meters-Segmentation-Autimatization/devops/terraform

# Export AWS credentials (get from AWS Academy Learner Lab)
export AWS_ACCESS_KEY_ID=<your_access_key>
export AWS_SECRET_ACCESS_KEY=<your_secret_key>
export AWS_SESSION_TOKEN=<your_session_token>

# Initialize Terraform
terraform init
```

### Step 2: Plan Infrastructure

```bash
# Review what will be created
terraform plan -var-file=../../infrastructure/terraform.tfvars
```

**Expected resources:**
- 1 VPC with public subnet
- 1 Security Group (SSH: 22, HTTP: 8000 from my_ip)
- 1 EC2 instance (t3.small, us-east-1)
- 1 Elastic IP
- 2 S3 buckets (DVC data, MLflow artifacts)
- 1 ECR repository
- 1 IAM role + instance profile

### Step 3: Apply Infrastructure

```bash
# Create all resources (⚠️ COSTS START HERE)
terraform apply -var-file=../../infrastructure/terraform.tfvars -auto-approve
```

**Estimated time:** 3-5 minutes
**Expected output:** EC2 public IP, MLflow URL, S3 bucket names

---

## 📝 Terraform Output

```bash
# ✅ Apply completed successfully - 16 resources created

EC2 Public IP: 13.219.216.230
EC2 Instance ID: i-02fb263c90e39258e
MLflow URL: http://13.219.216.230:5000
ECR Repository: 055677744286.dkr.ecr.us-east-1.amazonaws.com/wms-model
DVC Bucket: wms-dvc-data-055677744286
MLflow Bucket: wms-mlflow-artifacts-055677744286

SSH Command:
ssh -i ~/.ssh/labsuser.pem ec2-user@13.219.216.230
```

**Apply completed at:** [timestamp]
**Duration:** ~50 seconds

---

## 🔧 Phase 5 Continued: EC2 Setup

### Step 4: Verify EC2 Instance

```bash
# Get EC2 IP from terraform output
EC2_IP=$(cd devops/terraform && terraform output -raw ec2_public_ip)
echo "EC2 IP: $EC2_IP"

# Wait for instance to be ready (may take 2-3 minutes)
sleep 120

# Test SSH connection
ssh -i ~/.ssh/labsuser.pem -o StrictHostKeyChecking=no ec2-user@$EC2_IP 'echo "SSH connection successful"'
```

### Step 5: Verify Services on EC2

```bash
# Check k3s
ssh -i ~/.ssh/labsuser.pem ec2-user@13.219.216.230 'sudo systemctl status k3s | head -10'
# ✅ Status: active (running)

# Check MLflow
ssh -i ~/.ssh/labsuser.pem ec2-user@13.219.216.230 'sudo systemctl status mlflow | head -10'
# ✅ Status: active (running)

# Verify MLflow API
ssh -i ~/.ssh/labsuser.pem ec2-user@13.219.216.230 'curl -s http://localhost:5000/health'
# ✅ Response: OK
```

**Verification completed at:** [timestamp]
**All services running successfully** ✅

---

## 🏃 Phase 5 Final: Install GitHub Actions Runner

### Step 6: Get Runner Token

1. Go to: https://github.com/Rafallost/Water-Meters-Segmentation-Autimatization/settings/actions/runners
2. Click "New self-hosted runner"
3. Select "Linux" and "x64"
4. Copy the token from the configuration command

### Step 7: Install Runner on EC2

```bash
# SSH to EC2
ssh -i ~/.ssh/labsuser.pem ec2-user@$EC2_IP

# Create runner directory
mkdir -p ~/actions-runner && cd ~/actions-runner

# Download runner (check GitHub for latest version)
RUNNER_VERSION="2.319.1"
curl -o actions-runner-linux-x64-${RUNNER_VERSION}.tar.gz -L \
  https://github.com/actions/runner/releases/download/v${RUNNER_VERSION}/actions-runner-linux-x64-${RUNNER_VERSION}.tar.gz

# Extract
tar xzf actions-runner-linux-x64-${RUNNER_VERSION}.tar.gz

# Configure (use token from GitHub)
./config.sh \
  --url https://github.com/Rafallost/Water-Meters-Segmentation-Autimatization \
  --token <TOKEN_FROM_GITHUB> \
  --name ec2-runner \
  --labels self-hosted,linux,x64,ml-training \
  --work _work

# Install as service
sudo ./svc.sh install
sudo ./svc.sh start
sudo ./svc.sh status

# Exit SSH
exit
```

**Verification:** Check GitHub Settings → Actions → Runners - should see "ec2-runner" (Idle)

---

**Runner Token:** AZ2UCCULLQGWZS33RI5PZ7DJQ4YVE
**Verification:** Check GitHub Settings → Actions → Runners - should see "ec2-runner" (Idle) ✅

---

## ✅ Phase 5: COMPLETED

**Summary:**
- ✅ Terraform infrastructure created (16 resources)
- ✅ EC2 instance running (13.219.216.230)
- ✅ k3s service running
- ✅ MLflow service running
- ✅ GitHub Actions runner installed and active

**Duration:** ~15 minutes
**Status:** SUCCESS

---

## 🛠️ Phase 2: Core DevOps Scripts

### ✅ COMPLETED

**Scripts created:**
1. ✅ `devops/scripts/data-qa.py` - Data validation with image-mask pairing, resolution checks, mask binarity validation
2. ✅ `devops/scripts/quality-gate.py` - Metrics comparison with baseline (Dice ≥ 0.9075, IoU ≥ 0.8665)

**Status:** SUCCESS
**Committed and pushed to devops submodule**

---

## 🧹 Phase 8: AWS Cleanup Script

### ✅ COMPLETED

**Script created:**
- ✅ `devops/scripts/cleanup-aws.sh` - Comprehensive cleanup script that:
  - Empties S3 buckets (including versioned objects)
  - Runs terraform destroy
  - Removes local state files
  - Includes safety confirmations

**Status:** SUCCESS
**Committed and pushed to devops submodule**

---

## 📊 Phase 6: Application Deployment

### Status: IN PROGRESS (EC2 Instance Issue)

**Completed Steps:**

1. ✅ **Docker Image Built** (3 minutes ago)
   - Image size: 8.69GB (uncompressed), 4.65GB (compressed in ECR)
   - Base: Python 3.12-slim
   - Fixed libgl1-mesa-glx → libgl1 for Python 3.12 compatibility

2. ✅ **Docker Image Pushed to ECR**
   - Repository: 055677744286.dkr.ecr.us-east-1.amazonaws.com/wms-model:latest
   - Successfully uploaded to ECR

3. ✅ **Helm Configuration Fixed**
   - Updated `MLFLOW_TRACKING_URI` to `http://10.0.1.43:5000` (EC2 internal IP)
   - Added `imagePullSecrets: ecr-secret` for ECR authentication
   - Disabled `serviceMonitor` (Prometheus not yet deployed)
   - All changes committed: commits d7b4d02, c069847

4. ✅ **Resolved Disk Pressure Issue**
   - Cleaned Docker cache: freed 8.569GB
   - Disk usage: 29% (5.7G used, 15G free)
   - Manually removed disk-pressure taint from k3s node

5. ✅ **Model Registered to MLflow**
   - Uploaded baseline model: `best.pth` (7.6MB)
   - Registered as: `water-meter-segmentation` version 2
   - Stage: Production
   - Metrics: Dice 0.9275, IoU 0.8865

6. ✅ **Helm Deployment Executed**
   ```bash
   helm upgrade --install wms-model devops/helm/ml-model/ -f infrastructure/helm-values.yaml
   ```
   - Deployment created successfully
   - Service exposed as NodePort on port 31954

**Current Issue:**

⚠️ **EC2 Instance Unresponsive (12:27 UTC onwards)**
- SSH connection timing out
- Ping requests timing out
- Last known state: Pod was pulling 4.65GB image from ECR
- Pod status before disconnect: ContainerCreating → Running (with 2 restarts)

**Root Cause Analysis:**
- t3.small instance (2GB RAM) insufficient for 8.69GB Docker image
- Image pull + extraction likely triggered OOM (Out of Memory)
- Instance may have crashed or been stopped by AWS

**Recovery Plan:**

**Option A: Restart Instance** (AWS Console or CLI)
```bash
# Via AWS CLI
aws ec2 reboot-instances --instance-ids i-02fb263c90e39258e --region us-east-1

# Or start if stopped
aws ec2 start-instances --instance-ids i-02fb263c90e39258e --region us-east-1
```

**Option B: Upgrade Instance Type** (if budget allows)
```bash
# Stop instance
aws ec2 stop-instances --instance-ids i-02fb263c90e39258e --wait

# Change to t3.medium (4GB RAM)
aws ec2 modify-instance-attribute \
  --instance-id i-02fb263c90e39258e \
  --instance-type t3.medium

# Start instance
aws ec2 start-instances --instance-ids i-02fb263c90e39258e
```

**Option C: Recreate with Larger Instance**
```bash
# Update terraform.tfvars: instance_type = "t3.medium"
cd devops/terraform
terraform apply -var-file=../../infrastructure/terraform.tfvars
```

**Once Instance is Back:**
```bash
# Verify connection
ssh -i ~/.ssh/labsuser.pem ec2-user@13.219.216.230

# Check pod status
kubectl get pods
kubectl logs -l app.kubernetes.io/name=ml-model --tail=50

# Test endpoints
kubectl get svc
NODE_PORT=$(kubectl get svc wms-model-ml-model -o jsonpath='{.spec.ports[0].nodePort}')
curl http://13.219.216.230:$NODE_PORT/health
curl http://13.219.216.230:$NODE_PORT/metrics
```

**Time Spent:** ~50 minutes
**Status:** BLOCKED - waiting for instance recovery

---

## 🚀 Task #16: Training Pipeline

[To be filled during testing]

---

## 🛠️ Phase 2: Core Scripts

[To be filled during script creation]

---

## 🧹 Phase 8: Cleanup Script

[To be filled during cleanup script creation]

---

## 📌 Important Notes

### Session Information
- Lab session: 4 hours
- Started: [timestamp]
- AWS Region: us-east-1
- Instance Type: t3.small

### Cost Tracking
- EC2 t3.small: $0.0208/hour
- EIP: $0.005/hour (always charged while allocated)
- S3: ~$0.12/month
- ECR: ~$0.10/month

### Cleanup Reminder
**CRITICAL:** Run cleanup script at end of session to avoid charges!

```bash
# When done testing:
bash devops/scripts/cleanup-aws.sh
```

---

**Last Updated:** 2026-02-07
**Status:** In Progress - Phase 5
