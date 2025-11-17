## Description
<!-- Provide a brief description of the changes in this PR -->


## Related Issues
<!-- Link related issues using #issue_number -->
Closes #

## Type of Change
<!-- Check all that apply -->
- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Refactoring (no functional changes)
- [ ] Documentation update
- [ ] CI/CD infrastructure change

---

## Implementation Checklist

### Code Quality
- [ ] Code follows project style guidelines (Ruff, Black, isort)
- [ ] All functions have type hints (mypy passes)
- [ ] No security vulnerabilities (Bandit passes)
- [ ] No hardcoded secrets or API keys
- [ ] Error handling follows conversational error pattern (user-friendly messages)

### AI Quality (if applicable)
- [ ] Prompts loaded from versioned files (not hardcoded)
- [ ] LLM responses validated against Pydantic schemas
- [ ] Retry logic implemented for malformed outputs
- [ ] Token usage tracked and logged
- [ ] Guardrails implemented for out-of-scope requests

### Testing
- [ ] Unit tests added/updated (>80% coverage maintained)
- [ ] Integration tests pass (if applicable)
- [ ] Performance tests pass (p95 <5s if applicable)
- [ ] Golden datasets updated (if prompts changed)

### Security
- [ ] Input validation enforced (length, format, injection detection)
- [ ] PII redacted in logs
- [ ] Rate limiting applied where appropriate
- [ ] External API calls include timeout configuration
- [ ] Dependency vulnerabilities checked (pip-audit passes)

### Performance
- [ ] No blocking I/O in async functions
- [ ] Cost implications documented for LLM calls
- [ ] Conversation history pruning implemented (if applicable)
- [ ] Database queries use indexed fields (if applicable)

### Documentation
- [ ] Code comments added for complex logic
- [ ] API documentation updated (if applicable)
- [ ] README updated (if applicable)
- [ ] CHANGELOG updated (if applicable)

### Agent Patterns (if applicable)
- [ ] All agent tools return typed Pydantic models (not plain dicts)
- [ ] Tool invocations logged with structured metadata
- [ ] Tool errors caught and converted to user-friendly messages
- [ ] Agent orchestrator validates tool outputs

### API Clients (if applicable)
- [ ] Timeout configuration set (default: 10s)
- [ ] Retry with exponential backoff implemented (3 retries, base delay 1s)
- [ ] Graceful degradation/mock fallback when service unavailable
- [ ] OAuth tokens cached and refreshed before expiry
- [ ] Rate limit errors logged properly

### Redis/Session Management (if applicable)
- [ ] TTL set on all session keys (default: 3600s)
- [ ] Session data serialized via Pydantic `.model_dump_json()`
- [ ] Redis connection failures handled gracefully
- [ ] Expired sessions return clear user message

---

## Testing Performed
<!-- Describe the testing you performed -->

### Manual Testing
- [ ] Tested locally with `docker-compose up`
- [ ] Tested all affected endpoints/features
- [ ] Verified error handling scenarios

### Automated Testing
- [ ] All unit tests pass locally
- [ ] Integration tests pass locally (if applicable)
- [ ] Performance tests pass locally (if applicable)

### Test Output
```bash
# Paste test output here (optional)
```

---

## Screenshots/Recordings
<!-- Add screenshots or recordings if applicable -->


---

## Deployment Considerations

### Breaking Changes
<!-- List any breaking changes and migration steps -->
- [ ] No breaking changes
- [ ] Breaking changes documented below:


### Configuration Changes
<!-- List any new environment variables or config changes -->
- [ ] No configuration changes required
- [ ] New environment variables added (documented below):


### Database Migrations
<!-- List any database schema changes -->
- [ ] No database migrations required
- [ ] Migrations added (documented below):


---

## Reviewer Checklist
<!-- For reviewers -->

- [ ] Code reviewed for quality and correctness
- [ ] Tests reviewed and sufficient
- [ ] Documentation reviewed and adequate
- [ ] Security considerations addressed
- [ ] Performance implications considered
- [ ] Breaking changes identified and documented
- [ ] Deployment risks assessed

---

## Additional Notes
<!-- Any additional context for reviewers -->


---

**Copilot Review**: This PR will be automatically reviewed by GitHub Copilot using the guidelines in [.github/copilot-instructions.md](/.github/copilot-instructions.md)
