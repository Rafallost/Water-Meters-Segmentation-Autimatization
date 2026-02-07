# Git Hook Setup - Automatic Data Branch Creation

## Overview

This git hook automatically creates timestamped `data/YYYYMMDD-HHMMSS` branches when you try to push training data to main, enabling the automated workflow without manual branch creation.

## Installation

### Windows (Git Bash)

```bash
# Run from repo root
./devops/scripts/install-git-hooks.bat
```

Or manually:
```bash
cp devops/scripts/install-git-hooks.sh .git/hooks/pre-push
chmod +x .git/hooks/pre-push  # If using Git Bash
```

### Linux/Mac

```bash
# Run from repo root
./devops/scripts/install-git-hooks.sh
```

## How It Works

### Before Hook Installation

```bash
# User workflow (manual)
git checkout -b data/20260207-160000  # ❌ Must create branch manually
git add WMS/data/training/images/new.jpg
git commit -m "Add training data"
git push origin data/20260207-160000
```

### After Hook Installation

```bash
# User workflow (automatic)
git add WMS/data/training/images/new.jpg
git commit -m "Add training data"
git push origin main  # ✅ Just push to main!

# Hook automatically:
# - Detects training data changes
# - Creates data/20260207-163045 branch
# - Pushes to that branch instead
# - Blocks push to main
```

## What Happens After Hook Triggers

1. **Hook creates branch** `data/20260207-163045`
2. **GitHub Actions** detects push to `data/**`
3. **Data QA** validates images and masks
4. **If PASS:**
   - DVC adds and pushes data to S3
   - Creates Pull Request automatically
   - Training pipeline runs (up to 3 attempts)
   - Quality gate evaluates model
   - PR auto-approved if model improves
5. **If FAIL:**
   - Comments error on branch
   - No PR created

## Fallback Options

If you don't want to install the hook, you have 2 fallbacks:

### Option 1: Magic Branch
```bash
git push origin data/staging  # Workflow creates timestamped branch
```

### Option 2: Manual Branch Creation
```bash
git checkout -b data/$(date +%Y%m%d-%H%M%S)
git push origin data/$(date +%Y%m%d-%H%M%S)
```

## Testing the Hook

```bash
# 1. Create a test image (copy existing)
cp WMS/data/training/images/image001.jpg WMS/data/training/images/test_image.jpg
cp WMS/data/training/masks/image001.png WMS/data/training/masks/test_image.png

# 2. Commit
git add WMS/data/training/
git commit -m "test: hook automation"

# 3. Try to push to main
git push origin main

# Expected output:
# 🔍 Checking for training data changes...
#
# ╔════════════════════════════════════════════════════════════╗
# ║  🚫 Direct push to main with training data blocked        ║
# ╚════════════════════════════════════════════════════════════╝
#
# Training data changes detected. Creating data branch...
# 📦 Creating branch: data/20260207-164530
# 🚀 Pushing to data/20260207-164530...
# ✅ Success! Your changes are now on branch: data/20260207-164530
#
# Next steps:
#   1. GitHub Actions will validate your data
#   2. If valid, a Pull Request will be created automatically
#   ...
```

## Troubleshooting

### Hook doesn't execute
```bash
# Make sure hook is executable
chmod +x .git/hooks/pre-push

# Verify hook exists
ls -la .git/hooks/pre-push
```

### Push still goes to main
- Check if you're pushing code changes (not training data)
- Hook only triggers on changes to `WMS/data/training/**`
- Code changes can still go directly to main (until branch protection is enabled)

### Branch protection conflict
- If branch protection is enabled, push to main will be blocked
- Hook will create branch automatically
- This is expected behavior

## Uninstalling

```bash
# Remove the hook
rm .git/hooks/pre-push

# Or disable temporarily
mv .git/hooks/pre-push .git/hooks/pre-push.disabled
```

## How This Fits in the Full Workflow

```
┌────────────────────────────────────────────────────────────┐
│ USER                                                       │
│                                                            │
│ git add WMS/data/training/new_image.jpg                   │
│ git commit -m "Add training data"                         │
│ git push origin main ← Just push normally!                │
└────────────────┬───────────────────────────────────────────┘
                 │
                 ▼
┌────────────────────────────────────────────────────────────┐
│ GIT HOOK (pre-push)                                        │
│                                                            │
│ ✓ Detects training data changes                           │
│ ✓ Creates data/YYYYMMDD-HHMMSS branch                     │
│ ✓ Pushes to new branch                                    │
│ ✗ Blocks push to main                                     │
└────────────────┬───────────────────────────────────────────┘
                 │
                 ▼
┌────────────────────────────────────────────────────────────┐
│ GITHUB ACTIONS                                             │
│                                                            │
│ 1. Data QA Validation                                     │
│ 2. DVC Add & Push (if valid)                              │
│ 3. Create Pull Request                                    │
│ 4. Training Pipeline (3 attempts)                         │
│ 5. Quality Gate Evaluation                                │
│ 6. Auto-approve if improved                               │
└────────────────┬───────────────────────────────────────────┘
                 │
                 ▼
┌────────────────────────────────────────────────────────────┐
│ ADMIN/USER                                                 │
│                                                            │
│ Review PR → Merge to main                                 │
└────────────────┬───────────────────────────────────────────┘
                 │
                 ▼
┌────────────────────────────────────────────────────────────┐
│ DEPLOYMENT                                                 │
│                                                            │
│ 1. Build Docker image                                     │
│ 2. Push to ECR                                            │
│ 3. Deploy to k3s                                          │
│ 4. Smoke tests                                            │
└────────────────────────────────────────────────────────────┘
```

## Benefits

✅ **Zero manual work** - just `git push origin main`
✅ **No branch naming** - automatic timestamping
✅ **Can't forget** - hook always runs
✅ **Safety net** - blocks accidental pushes to main
✅ **Consistent** - everyone uses same workflow

## Next Steps

After installing the hook:
1. Enable GitHub branch protection (Task #19)
2. Implement data upload workflow (Task #21)
3. Add training retry logic (Task #22)
4. Test end-to-end (Task #23)

See `WORKFLOW_IMPLEMENTATION_PLAN.md` for full implementation details.
