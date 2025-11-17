# CI/CD Infrastructure Guide

**Feature**: 001-conversational-flight-search  
**Last Updated**: 2025-11-17  
**Status**: Operational

---

## Overview

This document describes the CI/CD infrastructure for the Conversational Flight Search project, including automated pipelines, deployment processes, and rollback procedures.

## Continuous Integration Pipelines

### 1. Code Quality Pipeline (`ci-quality.yml`)

**Trigger**: Pull requests and pushes to `main`/`develop`  
**Purpose**: Enforce code quality standards and test coverage

**Checks**:
- **Ruff**: Python linting for code quality issues
- **Black**: Code formatting verification  
- **isort**: Import statement sorting
- **mypy**: Static type checking
- **Bandit**: Security vulnerability scanning
- **pip-audit**: Dependency vulnerability audit
- **pytest**: Unit tests with >80% coverage requirement

**Exit Criteria**: All checks pass, coverage ≥80%

### 2. AI Quality Pipeline (`ai-quality.yml`)

**Trigger**: Changes to `prompts/`, `models/`, or `agents/` directories  
**Purpose**: Validate AI-specific quality requirements

**Checks**:
- Prompt regression tests using golden datasets
- Intent extraction accuracy validation (≥80%)
- Pydantic schema validation tests
- Guardrail effectiveness tests
- LLM response format validation

**Exit Criteria**: Accuracy ≥80%, all validations pass

### 3. Integration Tests Pipeline (`ci-integration.yml`)

**Trigger**: Pull requests to `main`  
**Purpose**: Verify end-to-end user story flows

**Setup**: Spins up Redis and FastAPI containers

**Checks**:
- User story flow tests
- HTTP endpoint verification
- WebSocket endpoint tests
- Session management tests
- Mocked external API integration

**Exit Criteria**: All integration tests pass

### 4. Performance Gating Pipeline (`ci-performance.yml`)

**Trigger**: Pull requests to `main`  
**Purpose**: Ensure performance requirements are met

**Checks**:
- Load tests with 100 concurrent users (Locust)
- P95 latency measurement (must be <5s)
- Memory leak detection

**Exit Criteria**: P95 <5s, no memory leaks detected

### 5. Security Pipeline (`ci-security.yml`)

**Trigger**: Pull requests, pushes, and daily at 2 AM UTC  
**Purpose**: Detect security vulnerabilities

**Checks**:
- Dependency vulnerability scanning (pip-audit, Snyk)
- Container image scanning (Trivy)
- Secret detection (TruffleHog)
- Code security scanning (Bandit)
- Hardcoded secret detection

**Exit Criteria**: No HIGH/CRITICAL vulnerabilities, no secrets exposed

---

## Continuous Deployment

### Environments

#### Staging
- **URL**: `https://int-travel-planner-staging.up.railway.app`
- **Trigger**: Automatic on merge to `main`
- **Purpose**: Pre-production validation, stakeholder demos
- **Configuration**: Real Amadeus test API, OpenAI production keys

#### Production
- **URL**: `https://int-travel-planner.up.railway.app`
- **Trigger**: Manual approval via workflow dispatch
- **Purpose**: Live user-facing environment
- **Configuration**: Production API keys, full monitoring

### Deployment Pipeline (`cd-deploy.yml`)

**Staging Deployment**:
1. Build Docker image (production target)
2. Run smoke tests against image
3. Deploy to Railway staging environment
4. Wait for deployment (30s)
5. Run post-deployment health checks
6. Run smoke tests on live staging

**Production Deployment**:
1. Build Docker image
2. Run smoke tests
3. Deploy to Railway production
4. Wait for deployment (30s)
5. Run post-deployment health checks
6. **Monitor error rates for 10 minutes**
7. Auto-rollback if error rate >5%
8. Tag release on success

**Deployment Strategy**: Rolling update with health checks

---

## Branch Protection Rules

**Applies to**: `main` branch

**Required Checks**:
- ✅ `ci-quality` - Code quality pipeline
- ✅ `ci-integration` - Integration tests
- ✅ `ci-performance` - Performance gating
- ✅ `ci-security` - Security scanning
- ✅ 1+ code review approval
- ✅ No merge conflicts
- ✅ Branch up-to-date with main

**Restrictions**:
- Direct commits to `main` blocked
- Force push disabled
- Deletion disabled

---

## Rollback Procedures

### Automatic Rollback

Triggers when production deployment meets any of:
- Health check failures during monitoring window
- Error rate >5% in first 10 minutes
- Smoke tests fail post-deployment

**Process**:
```bash
railway rollback --service backend --environment production
```

### Manual Rollback

If issues detected after monitoring window:

```bash
# 1. Identify last good deployment
railway logs --service backend --environment production

# 2. Rollback to previous version
railway rollback --service backend --environment production

# 3. Verify health
curl -f https://int-travel-planner.up.railway.app/health/ready

# 4. Monitor for 10 minutes
watch -n 60 'curl -s https://int-travel-planner.up.railway.app/health/ready'
```

### Emergency Rollback

Critical production issues:

```bash
# Immediate rollback
railway rollback --service backend --environment production --confirm

# Switch to maintenance mode (if implemented)
railway variables set MAINTENANCE_MODE=true --environment production

# Investigate logs
railway logs --service backend --environment production --tail 1000

# Fix issue, redeploy
railway up --service backend --environment production
```

---

## GitHub Secrets Configuration

**Required Secrets** (Configure via GitHub Settings → Secrets):

### API Keys
- `OPENAI_API_KEY` - OpenAI GPT-4 API key
- `OPENAI_ORG_ID` - OpenAI organization ID
- `AMADEUS_API_KEY` - Amadeus self-service API key
- `AMADEUS_API_SECRET` - Amadeus API secret

### Infrastructure
- `REDIS_URL` - Redis connection string (Upstash)
- `REDIS_PASSWORD` - Redis password (if required)

### Monitoring
- `SENTRY_DSN` - Sentry error tracking DSN
- `PROMETHEUS_ENDPOINT` - Prometheus metrics endpoint (optional)

### Deployment
- `RAILWAY_TOKEN` - Railway CLI authentication token
- `RAILWAY_STAGING_PROJECT_ID` - Staging project ID
- `RAILWAY_PRODUCTION_PROJECT_ID` - Production project ID
- `STAGING_URL` - Staging environment URL
- `PRODUCTION_URL` - Production environment URL

### Security Scanning
- `SNYK_TOKEN` - Snyk vulnerability scanning token (optional)

---

## Monitoring & Alerts

### Health Endpoints

- `/health/ready` - Readiness probe (checks Redis, external APIs)
- `/health/live` - Liveness probe (basic server health)

### Metrics Exposed

- `http_requests_total` - Total HTTP requests
- `http_request_duration_seconds` - Request latency histogram
- `llm_calls_total` - Total LLM API calls
- `llm_token_usage_total` - Token usage for cost tracking
- `tool_invocations_total` - Agent tool invocation count
- `tool_errors_total` - Tool error count

### Error Tracking

- **Sentry**: Real-time error tracking with stack traces
- **Release Tagging**: Errors tagged with deployment version

---

## Cost Optimization

### CI/CD Costs

- **GitHub Actions**: Free tier (2000 min/month) - staying within limits
- **Railway Staging**: ~$5/month (minimal resources)
- **Docker Registry**: GitHub Packages (free)
- **Total**: <$15/month

### Optimization Strategies

- Cache Docker layers aggressively
- Use mock data in CI tests (avoid OpenAI/Amadeus API costs)
- Run security scans daily (not on every PR)
- Minimize workflow run time

---

## Troubleshooting

### CI Pipeline Failures

**Code Quality Failure**:
```bash
# Run locally to debug
cd backend
ruff check app/ tests/
black --check app/ tests/
mypy app/
```

**Integration Test Failure**:
```bash
# Run locally with docker-compose
docker-compose -f docker-compose.test.yml up
pytest tests/integration/ -v
```

**Performance Test Failure**:
```bash
# Run load tests locally
locust -f tests/load/locustfile.py --headless --users 100 --host http://localhost:8000
```

### Deployment Failures

**Health Check Failing**:
- Check Railway logs: `railway logs --service backend --environment staging`
- Verify environment variables set correctly
- Check Redis connection

**Rollback Failed**:
- Manual revert to last known good commit
- Force deploy: `railway up --service backend --environment production --force`

---

## Maintenance

### Regular Tasks

- **Weekly**: Review security scan results
- **Monthly**: Update dependencies (`pip-audit`, `npm audit`)
- **Quarterly**: Review and optimize CI/CD costs

### Updating Workflows

1. Make changes to `.github/workflows/*.yml`
2. Test in feature branch PR
3. Merge to main after all checks pass
4. Monitor first few runs for issues

---

## Contact & Support

- **CI/CD Issues**: Open issue with `ci-cd` label
- **Deployment Issues**: Check Railway dashboard or logs
- **Security Alerts**: Immediate attention required

**Last Reviewed**: 2025-11-17  
**Next Review**: 2025-12-17
