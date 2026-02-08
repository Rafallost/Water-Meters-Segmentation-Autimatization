# Known Issues

This document tracks known issues and their workarounds.

---

## GitHub Actions: Bot-created PRs don't trigger training workflow

**Status:** Known limitation, workaround available

**Issue:**
When the `data-upload.yaml` workflow creates a PR using `github-actions[bot]`, the `train.yml` workflow doesn't automatically run on that PR. This is a GitHub security feature to prevent infinite workflow loops.

**Affected workflows:**
- `data-upload.yaml` creates PR → `train.yml` should run but doesn't

**Impact:**
- Users must manually trigger training after uploading data via `data/**` branches
- Training doesn't start automatically on bot-created PRs

**Current workaround:**
1. After PR is created, checkout the PR branch locally
2. Push an empty commit as yourself (not bot):
   ```bash
   git checkout <pr-branch>
   git commit --allow-empty -m "ci: trigger training workflow"
   git push
   ```
3. This triggers `train.yml` because the commit is from a user, not a bot

**Proper fix (TODO):**
Modify `data-upload.yaml` to use a Personal Access Token (PAT) instead of `GITHUB_TOKEN` when creating PRs:

1. Create PAT in GitHub Settings → Developer settings → Personal access tokens
   - Permissions: `Contents: Read/Write`, `Pull requests: Read/Write`, `Workflows: Read/Write`
   - Expiration: 90 days minimum (or longer for production)

2. Add to GitHub Secrets: `GH_PAT`

3. Update `.github/workflows/data-upload.yaml` line ~101:
   ```yaml
   - name: Create or Update Pull Request
     uses: actions/github-script@v7
     with:
       github-token: ${{ secrets.GH_PAT }}  # ← Add this line
       script: |
         # ... rest unchanged
   ```

**References:**
- GitHub Docs: [Triggering a workflow from a workflow](https://docs.github.com/en/actions/using-workflows/triggering-a-workflow#triggering-a-workflow-from-a-workflow)
- Related: PR #7, PR #4 (training didn't auto-start)

**Date discovered:** 2026-02-08

---

## End of known issues

