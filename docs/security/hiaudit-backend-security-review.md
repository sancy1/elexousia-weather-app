# Hi AUDIT Backend Security Review

## Audit context

- **Application:** EL-Exousia Weather Intel
- **Repository:** https://github.com/sancy1/elexousia-weather-app
- **Audited scope:** `./backend` only
- **Audit tool:** Hi AUDIT Agent
- **Audit job ID:** `fa7aba63`
- **Source files analyzed:** 89
- **Findings reported by Hi AUDIT:** 13 total — 10 Medium, 3 Low
- **Live systems tested:** None
- **Deployment environments tested:** None
- **Render backend tested:** No
- **Vercel frontend tested:** No

This review was limited to the local repository source code, configuration, dependencies, and documentation. No requests were sent to the deployed Render backend, the deployed Vercel frontend, or third-party production services.

## Executive summary

Hi AUDIT Agent completed a repository-only security review of the FastAPI backend. The review identified authorization, session-management, abuse-prevention, information-disclosure, and application-reliability issues.

The most significant security issue is an unauthenticated internal notification-check endpoint that can trigger forecast retrieval and alert generation for every user’s saved locations. Repeated anonymous requests could cause excessive WeatherAPI usage, increased database load, and denial of the intended scheduled workflow.

Other notable findings include a logout flow that can revoke a cookie session while leaving an authenticated bearer session active, a production-accessible debug endpoint that returns a reusable session token, and permissive cross-origin access assumptions.

## Findings overview

| ID        | Severity | Area                             | Finding                                                                          |
| --------- | -------: | -------------------------------- | -------------------------------------------------------------------------------- |
| Medium-1  |   Medium | City resolution                  | Orlando is normalized to Toronto, causing incorrect weather results              |
| Medium-2  |   Medium | Authentication                   | Logout can revoke the cookie session instead of the authenticated bearer session |
| Medium-3  |   Medium | Authorization / abuse prevention | Internal notification-check endpoint is publicly callable                        |
| Medium-4  |   Medium | Data integrity                   | Empty geocoded country code overrides a user-supplied country code               |
| Medium-5  |   Medium | Session security                 | Debug token route remains available in production                                |
| Medium-6  |   Medium | Chat reliability                 | Active chat streams are not registered for cancellation                          |
| Medium-9  |   Medium | City resolution                  | Southeast Asia is incorrectly matched as East Asia                               |
| Medium-10 |   Medium | Data integrity                   | Saving a city can discard the country selected in the city picker                |
| Medium-12 |   Medium | AI integration                   | Gemini tool-binding path omits required thought configuration                    |
| Medium-13 |   Medium | Session security                 | Debug response can return another user’s session token                           |
| Low-7     |      Low | Geocoding                        | Missing geocoding timezone is treated as UTC                                     |
| Low-8     |      Low | API correctness                  | Empty conversation update reports success without updating anything              |
| Low-11    |      Low | AI agent                         | Tool-call input is mistaken for the resolved city                                |

## Primary validated finding

### Medium-3: Internal notification check is publicly callable

**Hi AUDIT classification:** Confirmed, 97% confidence  
**Affected component:** `app/api/routes/notifications.py`  
**Affected endpoint:** `POST /api/notifications/check`  
**Severity:** High in the context of production exposure and abuse potential

#### Issue

The notification-check endpoint is intended to support a scheduled background workflow, but it is publicly callable without authentication or a scheduler-specific control. An anonymous caller can trigger the endpoint and cause the application to retrieve forecasts for every user’s saved location and commit any resulting alerts.

#### Evidence

Hi AUDIT identified the route registration at `app/api/routes/notifications.py:485`:

```python
@router.post("/check")
```

The handler selects saved locations, retrieves forecasts, and writes alerts. It does not require an authenticated user, administrator role, or scheduler-specific shared secret.

#### Reproduction steps

1. Start the FastAPI backend locally.
2. Send an unauthenticated request to the notification-check endpoint.
3. Observe that the endpoint begins its notification-check workflow.
4. Repeat the request and observe that the workflow can be triggered outside its intended schedule.

No live Render or Vercel systems were accessed during this review.

#### Impact

An attacker could repeatedly invoke the endpoint to:

- Trigger unnecessary WeatherAPI requests.
- Consume third-party API quotas or increase operating costs.
- Create avoidable database load.
- Interfere with the intended scheduled notification workflow.
- Potentially generate duplicate or unexpected notifications.

This creates an abuse-prevention and resource-exhaustion risk, particularly if the endpoint is exposed publicly in production.

#### Severity

**High** in a production context because the endpoint is unauthenticated, triggers external API calls, affects all users’ saved locations, and can be invoked repeatedly.

Hi AUDIT labeled the finding Medium. I classify it as High after considering its reachability, external API cost, database impact, and potential for abuse in the deployed environment.

#### Proposed mitigation

Apply one of the following controls:

1. Remove the public route and run the notification check exclusively through a protected background scheduler.
2. If the route must remain, require authentication and restrict access to an administrator or service account.
3. Alternatively, require a cryptographically random shared secret supplied through a secure environment variable and validate it before executing the workflow.
4. Add per-source rate limiting and monitoring for repeated invocation attempts.
5. Add an integration test that verifies unauthenticated requests are rejected.

## Secondary finding

### Medium-2: Logout revokes the cookie session instead of the authenticated bearer session

**Hi AUDIT classification:** Confirmed, 91% confidence  
**Affected component:** `app/api/routes/auth.py`  
**Affected endpoint:** Logout flow  
**Severity:** Medium

#### Issue

The authentication flow prioritizes a valid bearer token, but logout prioritizes the session cookie. A caller authenticated with bearer session B could send another cookie session A. Logout may delete session A and clear the cookie while bearer session B remains usable.

#### Impact

This can leave an authenticated bearer session active after a logout request. If the cookie belongs to another user, their session could be revoked instead of the caller’s active bearer session.

#### Proposed mitigation

Use the same authenticated session identity for both authentication and logout. After identifying the caller through the bearer token or cookie, revoke only the session associated with the authenticated caller and reject requests where the presented cookie does not match that identity.

## Remediation plan

| Priority | Finding                              | Recommended action                                                                                          |
| -------: | ------------------------------------ | ----------------------------------------------------------------------------------------------------------- |
|        1 | Medium-3                             | Remove or authenticate the internal notification-check endpoint                                             |
|        2 | Medium-5 / Medium-13                 | Remove or environment-gate the debug token endpoint; never return reusable session tokens                   |
|        3 | Medium-2                             | Align logout with the authenticated bearer session                                                          |
|        4 | Medium-4 / Medium-10                 | Validate and preserve user-selected country and location data                                               |
|        5 | Medium-1 / Medium-9 / Low-11         | Correct city normalization, region matching, and resolved-city event handling                               |
|        6 | Medium-6 / Medium-12 / Low-7 / Low-8 | Improve chat cancellation, Gemini tool configuration, timezone handling, and conversation-update validation |

## Scope and limitations

This review covered the backend source code under `./backend`, including FastAPI routes, authentication, OAuth, PostgreSQL access, external weather API integration, AI chat and agent components, dependencies, and configuration.

It did not include:

- Live testing of the Render backend.
- Live testing of the Vercel frontend.
- Penetration testing of third-party services.
- Review of frontend source code.
- Full root-level infrastructure review.
- Dynamic exploitation against production systems.

Findings should be revalidated after code or configuration changes. A disappearing warning alone does not prove that a security control is correct; the changed code, relevant tests, and application behavior must also be reviewed.

## Historical remediation note

During preparation for this review, an earlier environment-example file was found to have exposed credentials in Git history. The affected credentials were rotated, the current repository was sanitized, and GitHub secret scanning was checked. No live systems were tested during this review.
