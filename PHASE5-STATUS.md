# Phase 5: AWS Infrastructure - Status

**Data:** 2026-02-05
**Status:** ✅ Wdrożone, wymaga weryfikacji przed Phase 6

---

## ✅ Ukończone

### Infrastructure (Terraform)
- ✅ VPC + public subnet + internet gateway
- ✅ EC2 t3.small instance (Amazon Linux 2)
  - Instance ID: `i-02b7c8bce9328c4fc`
  - Public IP: `52.2.198.107`
  - Region: `us-east-1`
- ✅ Elastic IP allocated
- ✅ Security Groups (SSH from my IP, HTTP:8000 from my IP)
- ✅ S3 buckets:
  - DVC data: `s3://wms-dvc-data-055677744286/`
  - MLflow artifacts: `s3://wms-mlflow-artifacts-055677744286/`
- ✅ ECR repository: `055677744286.dkr.ecr.us-east-1.amazonaws.com/wms-model`

### EC2 Services
- ✅ Docker installed and running
- ✅ k3s cluster installed and running (7 pods healthy)
- ✅ Helm installed
- ✅ MLflow tracking server running on port 5000
  - Backend: SQLite (`/opt/mlflow/mlflow.db`)
  - Artifacts: S3 (`s3://wms-mlflow-artifacts-055677744286/`)
  - Accessible via SSH tunnel: `ssh -L 5000:localhost:5000 ec2-user@52.2.198.107`

### GitHub Actions Runner
- ✅ Self-hosted runner installed at `/opt/runner`
- ✅ Running as systemd service: `github-runner.service`
- ✅ Status: Online, Idle (green in GitHub UI)
- ✅ Runner name: `ip-10-0-1-213`

### DVC Configuration
- ✅ DVC remote updated to correct S3 bucket
- ✅ DVC push tested successfully (21 files pushed)

---

## ⚠️ Problemy rozwiązane podczas wdrożenia

### 1. User-data script failures
- **Problem:** k3s instalacja failowała z powodu SELinux dependency mismatch
- **Fix:** `INSTALL_K3S_SKIP_SELINUX_RPM=true`
- **Commit:** `6cd4670` in DevOps repo

### 2. MLflow urllib3 incompatibility
- **Problem:** urllib3 v2.0 wymaga OpenSSL 1.1.1+, Amazon Linux 2 ma 1.0.2k
- **Fix:** Pin `urllib3<2` w pip install
- **Commit:** `6cd4670` in DevOps repo

### 3. MLflow systemd service PATH issue
- **Problem:** gunicorn nie był w PATH dla systemd service
- **Fix:** Dodano `Environment="PATH=/usr/local/bin:/usr/bin:/bin"` do service
- **Commit:** `6cd4670` in DevOps repo

### 4. GitHub Actions runner GLIBC mismatch
- **Problem:** Runner's bundled Node.js 20 wymaga GLIBC 2.27+, AL2 ma 2.26
- **Fix:** Stworzono custom systemd service używający `./run.sh` zamiast `./runsvc.sh`
- **Service:** `/etc/systemd/system/github-runner.service`

### 5. DVC remote incorrect bucket
- **Problem:** DVC remote wskazywał na stary bucket (036136800740)
- **Fix:** Zaktualizowano do `s3://wms-dvc-data-055677744286/dvc`
- **Commit:** Pending push

---

## 🔄 Weryfikacja przed Phase 6 (DO ZROBIENIA JUTRO)

### Checklist przed rozpoczęciem Phase 6:

1. **Uruchom EC2:**
   ```bash
   aws ec2 start-instances --instance-ids i-02b7c8bce9328c4fc --region us-east-1
   aws ec2 describe-instances --instance-ids i-02b7c8bce9328c4fc --region us-east-1 --query 'Reservations[0].Instances[0].State.Name'
   ```

2. **Sprawdź IP (może się zmienić jeśli nie mamy Elastic IP):**
   ```bash
   aws ec2 describe-instances --instance-ids i-02b7c8bce9328c4fc --region us-east-1 --query 'Reservations[0].Instances[0].PublicIpAddress'
   ```

   **UWAGA:** Mamy Elastic IP, więc powinien pozostać: `52.2.198.107`

3. **SSH do EC2:**
   ```bash
   ssh -i C:\Users\rafal\.ssh\labsuser.pem ec2-user@52.2.198.107
   ```

4. **Weryfikuj serwisy na EC2:**
   ```bash
   # k3s cluster
   sudo systemctl status k3s --no-pager
   sudo /usr/local/bin/k3s kubectl get nodes
   sudo /usr/local/bin/k3s kubectl get pods -A

   # MLflow
   sudo systemctl status mlflow --no-pager
   curl http://localhost:5000/health

   # GitHub Actions runner
   sudo systemctl status github-runner --no-pager
   ```

5. **Weryfikuj MLflow UI (z lokalnej maszyny):**
   ```bash
   # W nowym terminalu - SSH tunnel
   ssh -i C:\Users\rafal\.ssh\labsuser.pem -L 5000:localhost:5000 ec2-user@52.2.198.107

   # W przeglądarce
   http://localhost:5000
   ```

6. **Weryfikuj GitHub Runner:**
   - Otwórz: `https://github.com/Rafallost/Water-Meters-Segmentation-Autimatization/settings/actions/runners`
   - Status powinien być: **Idle** (zielony)

7. **Weryfikuj DVC:**
   ```powershell
   cd D:\school\bsc\Repositories\Water-Meters-Segmentation-Autimatization
   dvc remote list -v
   # Should show: s3://wms-dvc-data-055677744286/dvc
   ```

8. **Sprawdź AWS billing:**
   - AWS Academy → AWS Details → Check "Used" amount
   - Powinno być nadal w budżecie $50

---

## 📝 Notatki do dokumentacji (thesis)

### AWS Academy Learner Lab ograniczenia:
- ❌ Nie można tworzyć IAM roles → Używamy pre-existing `LabInstanceProfile`
- ❌ Nie można tworzyć OIDC providers → GitHub Actions używa environment credentials
- ✅ Można tworzyć: VPC, EC2, S3, ECR, Security Groups, Elastic IPs

### Koszty (szacowane):
- EC2 t3.small: $0.0208/h
- Elastic IP: $0.005/h
- S3 storage: ~$0.023/GB/miesiąc
- S3 transfer OUT: $0.09/GB
- ECR storage: $0.10/GB/miesiąc

### Polecenia do zarządzania EC2:
```bash
# Start
aws ec2 start-instances --instance-ids i-02b7c8bce9328c4fc --region us-east-1

# Stop (oszczędza $0.0208/h compute, ale EIP nadal $0.005/h)
aws ec2 stop-instances --instance-ids i-02b7c8bce9328c4fc --region us-east-1

# Status
aws ec2 describe-instances --instance-ids i-02b7c8bce9328c4fc --region us-east-1 --query 'Reservations[0].Instances[0].State.Name'
```

---

## ➡️ Następne kroki (Phase 6)

**Phase 6: Deployment Stack**
- FastAPI serving layer (`WMS/src/serve/app.py`)
- Dockerfile (`docker/Dockerfile.serve`)
- Helm chart (`helm/ml-model/`)
- Deploy to k3s
- Smoke tests: `/health`, `/predict`, `/metrics`

**Szacowany czas:** 1-2 godziny

---

**Ostatnia aktualizacja:** 2026-02-05 23:40 UTC
**Następna sesja:** Weryfikacja Phase 5 → Start Phase 6
