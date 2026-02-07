# Branch Protection Setup

This document describes how to enable branch protection for the `main` branch to enforce the automated workflow.

## Why Branch Protection?

Branch protection ensures:
- **No direct pushes** to main (all changes via PR)
- **Required status checks** must pass before merge
- **Code review** before merging (optional but recommended)
- **Consistent workflow** - all data/code goes through validation

## Setup via GitHub UI (Recommended)

### Step 1: Navigate to Settings

1. Go to your repository: `https://github.com/Rafallost/Water-Meters-Segmentation-Autimatization`
2. Click **Settings** tab
3. Click **Branches** in left sidebar
4. Click **Add branch protection rule**

### Step 2: Configure Protection Rule

**Branch name pattern:**
```
main
```

**Required settings:**

✅ **Require a pull request before merging**
- ✅ Require approvals: 0 (auto-approval via workflow)
- ❌ Dismiss stale pull request approvals when new commits are pushed (optional)
- ❌ Require review from Code Owners (optional)

✅ **Require status checks to pass before merging**
- ✅ Require branches to be up to date before merging
- **Required status checks** (add these):
  - `data-qa` (from data-qa.yaml workflow)
  - `train` (from train.yml workflow)
  - `aggregate-results` (from train.yml workflow)

❌ **Require conversation resolution before merging** (optional)

❌ **Require signed commits** (optional)

✅ **Require linear history** (optional but recommended)
- Prevents merge commits, keeps history clean

❌ **Require deployments to succeed before merging** (not needed)

✅ **Lock branch** (optional - prevents ALL pushes except via PR)

❌ **Do not allow bypassing the above settings** (recommended)

✅ **Allow force pushes** → Set to **Everyone** (needed for automated workflows)
- The git hook will prevent accidental force pushes from users
- GitHub Actions needs this to push DVC updates

✅ **Allow deletions** → ❌ Disabled
- Prevents accidental branch deletion

### Step 3: Save Changes

Click **Create** or **Save changes**

## Setup via GitHub CLI (Alternative)

If you have GitHub CLI (`gh`) installed:

```bash
# Create branch protection rule
gh api repos/Rafallost/Water-Meters-Segmentation-Autimatization/branches/main/protection \
  --method PUT \
  --field required_status_checks='{"strict":true,"contexts":["data-qa","train","aggregate-results"]}' \
  --field enforce_admins=false \
  --field required_pull_request_reviews='{"required_approving_review_count":0}' \
  --field restrictions=null \
  --field allow_force_pushes=true \
  --field allow_deletions=false
```

## Setup via GitHub API (Advanced)

Using curl with a personal access token:

```bash
curl -X PUT \
  -H "Authorization: token YOUR_GITHUB_TOKEN" \
  -H "Accept: application/vnd.github+json" \
  https://api.github.com/repos/Rafallost/Water-Meters-Segmentation-Autimatization/branches/main/protection \
  -d '{
    "required_status_checks": {
      "strict": true,
      "contexts": ["data-qa", "train", "aggregate-results"]
    },
    "enforce_admins": false,
    "required_pull_request_reviews": {
      "required_approving_review_count": 0
    },
    "restrictions": null,
    "allow_force_pushes": true,
    "allow_deletions": false
  }'
```

## How It Works After Setup

### For Training Data Updates

```
USER: git push origin main (with training data)
  ↓
GIT HOOK: Detects training data, creates data/YYYYMMDD-HHMMSS branch
  ↓
GITHUB: Push to data/* branch (branch protection doesn't apply)
  ↓
DATA UPLOAD WORKFLOW: Validates, DVC push, creates PR
  ↓
BRANCH PROTECTION: PR must pass status checks
  ↓
TRAINING WORKFLOW: 3 attempts, auto-approve if improved
  ↓
USER/ADMIN: Merge PR (or auto-merge if configured)
  ↓
MAIN BRANCH: Updated with validated data and improved model
```

### For Code Changes

```
USER: Creates feature branch, pushes code
  ↓
USER: Opens PR to main
  ↓
BRANCH PROTECTION: Requires CI checks to pass
  ↓
CI PIPELINE: Runs lint, format, tests
  ↓
REVIEWER: Approves PR (optional)
  ↓
USER: Merges PR
  ↓
MAIN BRANCH: Updated with reviewed code
```

## Verifying Branch Protection

After setup, verify it's working:

```bash
# Try to push directly to main (should fail)
git checkout main
echo "test" >> test.txt
git add test.txt
git commit -m "test: direct push"
git push origin main
# Expected: Error - branch is protected
```

## Troubleshooting

### "Cannot push to protected branch"

✅ **Expected behavior** - branch protection is working!

**Solution:** Create a PR instead:
```bash
git checkout -b fix/my-changes
git push origin fix/my-changes
gh pr create --base main --head fix/my-changes
```

### Status checks not appearing

1. Make sure the workflow files exist and are on `main`
2. Check that workflow names match exactly
3. Run workflows at least once to register them
4. GitHub may take a few minutes to recognize new workflows

### "Allow force pushes" needed for workflows

The `data-upload.yaml` workflow needs to push DVC file updates. Without force push enabled, this will fail. The git hook prevents users from force pushing directly, so this is safe.

## Next Steps

After enabling branch protection:

1. **Test the git hook** - Try pushing training data
2. **Test the workflows** - Verify they create PRs and run training
3. **Test end-to-end** (Task #23) - Complete data → PR → training → merge → deploy flow

See `WORKFLOW_IMPLEMENTATION_PLAN.md` for full testing procedure.

## Benefits

✅ **Safety** - No accidental pushes to main
✅ **Quality** - All changes validated before merge
✅ **Traceability** - Every change has a PR and audit trail
✅ **Automation** - Workflows enforce quality gates
✅ **Collaboration** - PRs enable code review
