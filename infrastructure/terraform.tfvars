# Terraform Variables for AWS Infrastructure
# IMPORTANT: Update these values before running terraform apply

# AWS Configuration
aws_region        = "us-east-1"
availability_zone = "us-east-1a"

# EC2 Configuration
instance_type = "t3.large" # 8GB RAM, 2 vCPU - required for ML workloads

# Your IP address for SSH access - NOW AUTO-DETECTED!
# No longer needed - automatically detected via https://api.ipify.org
# See devops/terraform/modules/vpc/my_ip.tf for implementation
# my_ip = "46.112.74.13/32" # Commented out - auto-detected now!

# SSH key pair name (pre-created by AWS Academy Learner Lab)
key_name = "vockey"

# S3 bucket names (globally unique - account ID already appended)
dvc_bucket    = "wms-dvc-data-055677744286"
mlflow_bucket = "wms-mlflow-artifacts-055677744286"

# GitHub repository (leave as-is unless you forked the repo)
github_repo = "Rafallost/Water-Meters-Segmentation-Autimatization"

# Monitoring Configuration (Prometheus + Grafana)
# Requires t3.large or larger (you have t3.large - OK!)
# Adds ~500MB RAM usage, ~2GB disk, +3 min startup time
install_monitoring = true
grafana_password   = "WMS-Monitoring-2026!" # Change in production!
