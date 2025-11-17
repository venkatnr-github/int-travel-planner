# GitHub Secrets Configuration

**Feature**: 001-conversational-flight-search  
**Last Updated**: 2025-11-17

---

## Overview

GitHub Secrets store sensitive credentials used in CI/CD workflows. This document lists all required secrets and how to configure them.

## Required Secrets

### API Keys (Application)

#### `OPENAI_API_KEY`
- **Purpose**: OpenAI GPT-4 API authentication
- **Format**: `sk-proj-...` (starts with `sk-proj-` or `sk-`)
- **How to obtain**: 
  1. Go to [OpenAI API Keys](https://platform.openai.com/api-keys)
  2. Create new secret key
  3. Copy immediately (won't be shown again)
- **Used in**: 
  - `ci-integration.yml` (for integration tests with mocked data)
  - Deployment workflows (staging/production)

#### `OPENAI_ORG_ID` (Optional)
- **Purpose**: OpenAI organization ID (if using organization account)
- **Format**: `org-...`
- **How to obtain**: OpenAI Platform → Settings → Organization
- **Used in**: Same as `OPENAI_API_KEY`

#### `AMADEUS_API_KEY`
- **Purpose**: Amadeus Self-Service API key
- **Format**: Alphanumeric string
- **How to obtain**:
  1. Register at [Amadeus for Developers](https://developers.amadeus.com/register)
  2. Create new self-service app
  3. Copy API Key from app dashboard
- **Used in**: Deployment workflows, integration tests

#### `AMADEUS_API_SECRET`
- **Purpose**: Amadeus API secret (paired with API key)
- **Format**: Alphanumeric string
- **How to obtain**: Same location as `AMADEUS_API_KEY`
- **Used in**: Same as `AMADEUS_API_KEY`

---

### Infrastructure

#### `REDIS_URL`
- **Purpose**: Redis connection string for session storage
- **Format**: `redis://username:password@host:port/db` or `rediss://` for TLS
- **How to obtain**:
  - **Upstash** (recommended): 
    1. Create database at [Upstash Console](https://console.upstash.com/)
    2. Copy connection string from dashboard
  - **Railway**: Deploy Redis service, copy connection URL
  - **Local dev**: `redis://localhost:6379`
- **Used in**: Deployment workflows (staging/production)

#### `REDIS_PASSWORD` (Optional)
- **Purpose**: Redis password if not included in `REDIS_URL`
- **Format**: String
- **Used in**: Deployment workflows if `REDIS_URL` doesn't include password

---

### Monitoring

#### `SENTRY_DSN`
- **Purpose**: Sentry error tracking endpoint
- **Format**: `https://[key]@[org].ingest.sentry.io/[project]`
- **How to obtain**:
  1. Create project at [Sentry.io](https://sentry.io/)
  2. Go to Settings → Projects → [Your Project] → Client Keys (DSN)
  3. Copy DSN
- **Used in**: Deployment workflows, runtime error tracking

#### `PROMETHEUS_ENDPOINT` (Optional)
- **Purpose**: Prometheus metrics push endpoint
- **Format**: `https://prometheus.example.com/api/v1/push`
- **Used in**: Performance monitoring (if enabled)

---

### Deployment

#### `RAILWAY_TOKEN`
- **Purpose**: Railway CLI authentication for deployments
- **Format**: Long alphanumeric token
- **How to obtain**:
  ```bash
  # Install Railway CLI
  npm install -g @railway/cli
  
  # Login and generate token
  railway login
  railway whoami --token
  ```
- **Used in**: `cd-deploy.yml` workflow

#### `RAILWAY_STAGING_PROJECT_ID`
- **Purpose**: Railway project ID for staging environment
- **Format**: UUID-like string
- **How to obtain**:
  ```bash
  # In your project directory
  railway link
  railway status --json | jq -r '.projectId'
  ```
- **Used in**: `cd-deploy.yml` staging job

#### `RAILWAY_PRODUCTION_PROJECT_ID`
- **Purpose**: Railway project ID for production environment
- **Format**: UUID-like string
- **How to obtain**: Same as staging project ID (or separate project)
- **Used in**: `cd-deploy.yml` production job

#### `STAGING_URL`
- **Purpose**: Staging environment URL for health checks
- **Format**: `https://int-travel-planner-staging.up.railway.app`
- **How to obtain**: Railway dashboard → Staging environment → Domain
- **Used in**: `cd-deploy.yml` post-deployment validation

#### `PRODUCTION_URL`
- **Purpose**: Production environment URL for health checks
- **Format**: `https://int-travel-planner.up.railway.app`
- **How to obtain**: Railway dashboard → Production environment → Domain
- **Used in**: `cd-deploy.yml` post-deployment validation

---

### Security Scanning (Optional)

#### `SNYK_TOKEN`
- **Purpose**: Snyk vulnerability scanning authentication
- **Format**: UUID-like token
- **How to obtain**:
  1. Sign up at [Snyk.io](https://snyk.io/)
  2. Account Settings → API Token
  3. Generate token
- **Used in**: `ci-security.yml` workflow
- **Note**: Free tier available, optional for CI

---

## Configuration Steps

### Step 1: Navigate to Repository Secrets

1. Go to: `https://github.com/venkatnr-github/genai`
2. Click: **Settings** → **Secrets and variables** → **Actions**
3. Click: **New repository secret**

### Step 2: Add Each Secret

For each secret listed above:

1. Click **New repository secret**
2. **Name**: Enter exact secret name (e.g., `OPENAI_API_KEY`)
3. **Value**: Paste the secret value
4. Click **Add secret**

### Step 3: Verify Secrets

After adding all secrets, verify the list matches:

```
✅ OPENAI_API_KEY
✅ AMADEUS_API_KEY
✅ AMADEUS_API_SECRET
✅ REDIS_URL
✅ SENTRY_DSN
✅ RAILWAY_TOKEN
✅ RAILWAY_STAGING_PROJECT_ID
✅ RAILWAY_PRODUCTION_PROJECT_ID
✅ STAGING_URL
✅ PRODUCTION_URL
```

Optional secrets (add if using):
```
□ OPENAI_ORG_ID
□ REDIS_PASSWORD
□ PROMETHEUS_ENDPOINT
□ SNYK_TOKEN
```

---

## Environment-Specific Variables

Some values differ between staging and production. Configure these in **Railway** (not GitHub Secrets):

### Railway Environment Variables

**Staging Environment**:
```bash
APP_ENV=staging
LOG_LEVEL=DEBUG
OPENAI_API_KEY=<from-github-secret>
AMADEUS_API_KEY=<from-github-secret>
AMADEUS_API_SECRET=<from-github-secret>
REDIS_URL=<from-github-secret>
SENTRY_DSN=<from-github-secret>
REDIS_SESSION_TTL=3600
RATE_LIMIT_PER_IP=10
ENABLE_MOCK_DATA=false
```

**Production Environment**:
```bash
APP_ENV=production
LOG_LEVEL=INFO
OPENAI_API_KEY=<from-github-secret>
AMADEUS_API_KEY=<from-github-secret>
AMADEUS_API_SECRET=<from-github-secret>
REDIS_URL=<from-github-secret>
SENTRY_DSN=<from-github-secret>
REDIS_SESSION_TTL=3600
RATE_LIMIT_PER_IP=10
ENABLE_MOCK_DATA=false
```

Configure these via Railway CLI or dashboard:
```bash
# Set variable in Railway
railway variables set VARIABLE_NAME=value --environment staging
```

---

## Security Best Practices

### Secret Rotation

Rotate secrets periodically (recommended every 90 days):

1. Generate new secret in provider (OpenAI, Amadeus, etc.)
2. Update GitHub Secret
3. Redeploy affected environments
4. Revoke old secret

### Access Control

- **GitHub Secrets**: Only accessible to repository admins and GitHub Actions
- **Railway Variables**: Only accessible to Railway project members
- Never log secret values (only first 4 chars for debugging)

### Secret Scanning

GitHub Secret Scanning automatically detects:
- AWS keys
- Azure tokens
- OpenAI API keys (sometimes)
- Database connection strings

**If detected**: GitHub will alert and may notify the provider.

---

## Troubleshooting

### Secret Not Found in Workflow

**Error**: `secrets.OPENAI_API_KEY is empty`

**Solution**:
1. Verify secret name matches exactly (case-sensitive)
2. Check secret is set at repository level (not environment level)
3. Confirm workflow has `secrets: inherit` if calling reusable workflow

### Invalid Secret Value

**Error**: `Authentication failed: Invalid API key`

**Solution**:
1. Verify secret copied completely (no truncation)
2. Check for extra spaces before/after value
3. Regenerate secret from provider
4. Test secret manually before adding:
   ```bash
   curl -H "Authorization: Bearer $OPENAI_API_KEY" \
     https://api.openai.com/v1/models
   ```

### Deployment Fails After Secret Update

**Error**: Deployment fails but secret is correct

**Solution**:
1. Restart Railway service to pick up new variables:
   ```bash
   railway restart --service backend --environment staging
   ```
2. Verify Railway variables match GitHub Secrets

---

## Verification Checklist

Before running CI/CD:

- [ ] All required GitHub Secrets configured
- [ ] Railway environment variables set for staging
- [ ] Railway environment variables set for production
- [ ] Test deployments trigger successfully
- [ ] Health checks pass with configured secrets
- [ ] Sentry receiving test events

---

## Related Documentation

- [CI/CD Pipeline Overview](./ci-cd.md)
- [Railway Deployment](./railway-deployment.md)
- [Branch Protection Rules](./branch-protection.md)

---

**Last Reviewed**: 2025-11-17  
**Next Review**: 2026-02-17 (rotate secrets)
