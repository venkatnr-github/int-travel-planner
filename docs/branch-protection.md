# Branch Protection Setup

**Repository**: int-travel-planner  
**Branch**: `main`  
**Last Updated**: 2025-11-17

---

## Overview

Branch protection rules enforce code quality and security by requiring all changes to `main` go through pull requests with automated checks and code review.

---

## Configuration Steps

### 1. Navigate to Branch Protection Settings

```bash
# Via GitHub Web UI:
# 1. Go to repository: https://github.com/<USERNAME>/int-travel-planner
# 2. Click "Settings" → "Branches"
# 3. Click "Add rule" under "Branch protection rules"
# 4. Enter branch name pattern: main
```

### 2. Required Status Checks

Enable: **✅ Require status checks to pass before merging**

**Required checks** (select all):
- `ci-quality` - Code quality pipeline
- `ci-integration` - Integration tests
- `ci-performance` - Performance gating
- `ci-security` - Security scanning

**Additional settings**:
- ✅ Require branches to be up to date before merging

### 3. Require Pull Request Reviews

Enable: **✅ Require a pull request before merging**

**Settings**:
- Required approving reviews: **1**
- ✅ Dismiss stale pull request approvals when new commits are pushed
- ✅ Require review from Code Owners (if CODEOWNERS file exists)

### 4. Require Linear History

Enable: **✅ Require linear history**

This ensures clean commit history with no merge commits.

### 5. Restrict Who Can Push

Enable: **✅ Restrict who can push to matching branches**

**Restrictions**:
- Only allow administrators to push directly
- All other contributors must use pull requests

### 6. Additional Protections

Enable:
- ✅ Require conversation resolution before merging
- ✅ Do not allow bypassing the above settings (even for administrators)
- ✅ Lock branch (optional - prevents any modifications)

---

## Enforcement Rules

### Pull Request Requirements

**Before merge**:
1. All CI checks must pass (quality, integration, performance, security)
2. 1+ code review approval from team member
3. All review comments resolved
4. Branch up-to-date with `main`
5. No merge conflicts

### CI Pipeline Gates

**Quality Gate**:
- Ruff linting passes
- Black formatting verified
- isort import order correct
- mypy type checking passes
- Bandit security scan passes
- pip-audit vulnerability scan passes
- pytest coverage ≥80%

**Integration Gate**:
- All user story flows pass
- HTTP/WebSocket endpoints verified
- Session management tests pass

**Performance Gate**:
- P95 latency <5s
- Load tests with 100 concurrent users pass
- No memory leaks detected

**Security Gate**:
- No HIGH/CRITICAL vulnerabilities in dependencies
- No secrets exposed in code
- Container images pass Trivy scan

---

## Automated Actions

### On PR Open
- All CI pipelines triggered automatically
- Copilot code review initiated (via .github/copilot-instructions.md)

### On PR Update
- Stale reviews dismissed
- CI pipelines re-run
- Branch protection re-evaluated

### On Merge to Main
- Staging deployment triggered automatically (cd-deploy.yml)
- Release tagged (if production deployment)

---

## Exception Handling

### Emergency Hotfix Process

If critical production issue requires immediate fix:

```bash
# 1. Create hotfix branch from main
git checkout -b hotfix/critical-issue main

# 2. Make minimal fix
# ... edit files ...

# 3. Run checks locally
ruff check app/ tests/
pytest tests/ --cov=app --cov-report=term-missing

# 4. Create PR with [HOTFIX] tag
gh pr create --title "[HOTFIX] Fix critical production issue" --body "Emergency fix for..."

# 5. Request expedited review
# Tag reviewer with @mention in PR description

# 6. Merge immediately after 1 approval + passing CI
gh pr merge --auto --squash
```

**Note**: Even hotfixes must pass CI checks. Administrator override only for catastrophic failure.

---

## Verification

### Check Protection Status

```bash
# Via GitHub CLI
gh api repos/:owner/:repo/branches/main/protection

# Expected output should show:
# - required_status_checks enabled
# - required_pull_request_reviews enabled
# - enforce_admins: true
# - restrictions enabled
```

### Test Protection Rules

```bash
# 1. Try direct push to main (should fail)
git checkout main
echo "test" >> README.md
git commit -am "Test direct push"
git push origin main
# Expected: ERROR - protected branch

# 2. Try PR without checks (should block merge)
git checkout -b test-protection
echo "test" >> README.md
git commit -am "Test PR"
git push origin test-protection
gh pr create --title "Test PR" --body "Testing protection"
# Expected: Merge blocked until CI passes
```

---

## Monitoring

### Check CI Pipeline Status

```bash
# View recent workflow runs
gh run list --limit 10

# Check specific workflow
gh run view <run-id>

# Watch live run
gh run watch
```

### Review Protected Branch Analytics

GitHub Settings → Insights → Pulse:
- Failed checks per week
- Average time to merge
- Review turnaround time

---

## Troubleshooting

### Issue: CI Checks Not Running

**Cause**: Workflow not triggering on PR  
**Fix**:
```bash
# Check workflow trigger configuration in .github/workflows/*.yml
# Should include: on: [pull_request]

# Re-trigger manually
gh workflow run ci-quality.yml
```

### Issue: Required Check Not Listed

**Cause**: Workflow hasn't run yet  
**Fix**:
1. Create test PR to trigger workflows
2. Wait for workflows to complete
3. Return to branch protection settings
4. Required checks will now appear in dropdown

### Issue: Can't Merge Despite Passing CI

**Cause**: Branch not up-to-date  
**Fix**:
```bash
# Update branch
git checkout feature-branch
git pull origin main
git push origin feature-branch
```

---

## Additional Resources

- [GitHub Branch Protection Documentation](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches)
- [GitHub Required Status Checks](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/collaborating-on-repositories-with-code-quality-features/about-status-checks)
- [Project CI/CD Guide](../ci-cd.md)

---

**Last Reviewed**: 2025-11-17  
**Next Review**: 2025-12-17
