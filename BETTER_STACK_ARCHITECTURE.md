# Architecture Better Stack - Plan d'Implémentation Complet

## État Actuel vs Better Stack

### MODULES EXISTANTS ✓
- Uptime Monitoring basique (Monitor, Check)
- Incidents basiques
- Status Pages simples
- Escalation rules
- Notifications (email, Telegram, webhooks)
- Stripe integration

### MODULES MANQUANTS ✗
1. **Incident Management complet** (Slack/Teams workflows, AI post-mortems, MTTA/MTTR)
2. **On-call Management** (calendriers, rotations, overrides, request cover)
3. **Logs & Traces** (VRL, SQL, PromQL, live tail, anomalies, S3)
4. **Metrics** (dashboards collaboratifs, derived metrics, PromQL)
5. **Error Tracking** (Sentry SDK compatible, AI prompts, release tracking)
6. **Call Routing** (numéros, transcriptions, workflows)
7. **Data Warehouse** (ClickHouse, NVMe/S3 tiers, SQL API)
8. **AI Features** (root cause analysis, post-mortems, MCP server)
9. **Advanced Status Pages** (CSS/JS, white-label, SSO, IP restrict)
10. **SSO/RBAC** (Google/Azure/Okta, SCIM, audit logs)
11. **Terraform Provider**
12. **Transaction Monitoring** (Playwright)

---

## Architecture Globale

```
┌─────────────────────────────────────────────────────────────┐
│                     API Gateway (FastAPI)                    │
│  /api/uptime  /api/incidents  /api/logs  /api/metrics       │
│  /api/errors  /api/warehouse  /api/oncall  /api/call        │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
┌───────▼────────┐  ┌────────▼────────┐  ┌────────▼────────┐
│  PostgreSQL    │  │  ClickHouse     │  │  S3-compatible  │
│  (metadata)    │  │  (metrics/logs) │  │  (long-term)    │
└────────────────┘  └─────────────────┘  └─────────────────┘
        │                     │                     │
┌───────▼────────┐  ┌────────▼────────┐  ┌────────▼────────┐
│  Redis         │  │  Celery/ARQ     │  │  MinIO/S3       │
│  (cache/queue) │  │  (async tasks)  │  │  (storage)      │
└────────────────┘  └─────────────────┘  └─────────────────┘
```

---

## Modèle de Données par Module

### 1. INCIDENT MANAGEMENT

```python
class Incident(Base):
    id: UUID
    title: str
    status: Enum(OPEN, ACKNOWLEDGED, RESOLVED)
    severity: Enum(SEV1, SEV2, SEV3, SEV4)
    created_at, acknowledged_at, resolved_at: DateTime

    # MTTA/MTTR
    time_to_acknowledge: int  # seconds
    time_to_resolve: int  # seconds

    # AI Features
    root_cause_analysis: JSONB
    ai_postmortem: Text

    # Slack/Teams
    slack_channel_id: str
    slack_thread_ts: str
    teams_channel_id: str

    # Relationships
    responder_id: UUID  # FK User (on-call)
    service_id: UUID  # FK Service
    escalation_level: int

    # Timeline
    timeline_events: JSONB[]  # [{ts, type, user, action}]

    # Roles
    commander_id: UUID
    deputy_id: UUID
    lead_id: UUID

class Service(Base):
    id: UUID
    name: str
    team_id: UUID
    escalation_policy_id: UUID
    runbook_url: str
    metadata: JSONB

class IncidentRole(Base):
    id: UUID
    incident_id: UUID
    role_type: Enum(COMMANDER, DEPUTY, LEAD)
    user_id: UUID
    assigned_at: DateTime
```

### 2. ON-CALL MANAGEMENT

```python
class OnCallSchedule(Base):
    id: UUID
    name: str
    team_id: UUID
    timezone: str

    # Rotation
    rotation_type: Enum(DAILY, WEEKLY, CUSTOM)
    rotation_start: DateTime
    rotation_interval_hours: int

    # Calendar sync
    google_calendar_id: str
    outlook_calendar_id: str

class OnCallShift(Base):
    id: UUID
    schedule_id: UUID
    user_id: UUID
    start_time: DateTime
    end_time: DateTime

    # Override
    is_override: bool
    overridden_by_id: UUID
    override_reason: str

class CoverRequest(Base):
    id: UUID
    requester_id: UUID
    shift_id: UUID
    reason: str
    status: Enum(PENDING, ACCEPTED, REJECTED)
    potential_covers: UUID[]  # User IDs
```

### 3. LOGS & TRACES

```python
class LogSource(Base):
    id: UUID
    name: str
    team_id: UUID

    # Ingestion
    ingestion_method: Enum(HTTP, VECTOR, FLUENT_BIT, SYSLOG)
    api_key: str

    # VRL Transform
    vrl_pipeline: Text  # VRL code

    # Retention
    retention_days: int = 30
    s3_bucket: str  # custom bucket

    # Derived Metrics
    derived_metrics_enabled: bool
    derived_metrics_nvme: bool  # NVMe vs S3

class LogEvent(Base):
    # Stocké dans ClickHouse, pas PostgreSQL
    timestamp: DateTime
    source_id: UUID
    level: Enum(DEBUG, INFO, WARN, ERROR, FATAL)
    message: Text
    attributes: Map<String, String>  # flexible schema
    trace_id: UUID  # OpenTelemetry

class TraceSpan(Base):
    # Stocké dans ClickHouse
    trace_id: UUID
    span_id: UUID
    parent_span_id: UUID
    service_name: str
    operation_name: str
    start_time: DateTime64
    duration_ns: UInt64
    tags: Map<String, String>
    logs: Array<Struct>

class LogQuery(Base):
    id: UUID
    user_id: UUID
    query_type: Enum(SQL, VRL, PROMQL)
    query_text: Text
    saved_as_dashboard: bool
```

### 4. METRICS

```python
class MetricSeries(Base):
    # Stocké dans ClickHouse
    metric_name: str
    labels: Map<String, String>
    timestamp: DateTime
    value: Float64

    # Retention
    retention_months: int = 13

class Dashboard(Base):
    id: UUID
    name: str
    team_id: UUID
    is_shared: bool

    panels: JSONB[]  # [{type, query, visualization}]

class Alert(Base):
    id: UUID
    name: str
    query: Text  # PromQL
    threshold: float
    condition: Enum(GT, LT, EQ)

    # Anomaly Detection
    use_anomaly_detection: bool
    anomaly_sensitivity: float

    # Actions
    create_incident: bool
    notify_channels: UUID[]
```

### 5. ERROR TRACKING

```python
class ErrorProject(Base):
    id: UUID
    name: str
    team_id: UUID

    # Sentry compatibility
    dsn: str  # Sentry DSN format
    platform: Enum(PYTHON, JAVASCRIPT, JAVA, GO, PHP, RUBY)

    # Pricing
    events_this_month: int
    events_quota: int = 100000  # Free tier

class ErrorEvent(Base):
    id: UUID
    project_id: UUID
    fingerprint: str  # hash for grouping

    # Event data
    timestamp: DateTime
    level: Enum(DEBUG, INFO, WARNING, ERROR, FATAL)
    message: Text
    exception_type: str
    exception_value: str
    stacktrace: JSONB

    # Context
    user_id: str
    user_email: str
    release: str
    environment: str
    tags: JSONB

    # AI
    bugfix_prompt: Text  # AI-generated

    # Integrations
    linear_issue_id: str
    jira_issue_key: str

class ErrorGroup(Base):
    id: UUID
    project_id: UUID
    fingerprint: str

    title: str
    first_seen: DateTime
    last_seen: DateTime
    event_count: int

    status: Enum(UNRESOLVED, IGNORED, RESOLVED)
    assigned_to_id: UUID
    snoozed_until: DateTime
```

### 6. STATUS PAGES (ADVANCED)

```python
class StatusPage(Base):
    id: UUID
    name: str
    subdomain: str
    custom_domain: str

    # Styling ($15/page)
    custom_css: Text
    custom_js: Text
    logo_url: str

    # Security
    is_password_protected: bool  # $50/page
    password_hash: str
    ip_whitelist: str[]  # $250/page
    sso_enabled: bool  # $250/page
    sso_provider: Enum(GOOGLE, AZURE, OKTA)

    # White-label ($250/page)
    is_white_label: bool
    footer_text: str

    # Email
    custom_email_domain: str  # $250/page

    # Analytics
    google_analytics_id: str

    # Subscribers (1000 free, +$40 per 1000)
    subscriber_quota: int = 1000
    subscriber_count: int

    # i18n
    languages: str[]

class StatusPageSubscriber(Base):
    id: UUID
    status_page_id: UUID
    email: str
    phone: str
    notify_incidents: bool
    notify_maintenance: bool
    subscribed_at: DateTime
```

### 7. CALL ROUTING

```python
class PhoneNumber(Base):
    id: UUID
    team_id: UUID

    # Number ($250/month per number)
    phone_number: str
    country: Enum(US, CA, UK, DE, FR, etc)

    # Welcome message
    welcome_message_text: str
    welcome_message_audio_url: str

    # Allowlist
    allowed_caller_numbers: str[]

    # Routing
    route_to_oncall: bool
    escalation_policy_id: UUID

class Call(Base):
    id: UUID
    phone_number_id: UUID

    caller_number: str
    start_time: DateTime
    end_time: DateTime
    duration_seconds: int

    # Transcription
    transcription_text: Text
    transcription_language: str
    transcription_confidence: float

    # Incident
    created_incident_id: UUID

    # Recording
    recording_url: str
```

### 8. DATA WAREHOUSE

```python
class WarehousePlan(Base):
    id: UUID
    team_id: UUID

    plan_type: Enum(STANDARD, TURBO_2K, ULTRA_4K, HYPER_6K)

    # Quotas
    max_execution_time_s: int
    max_results_rows: int
    max_memory_gb_per_node: int
    max_nodes: int
    concurrent_s3_queries: int
    concurrent_nvme_queries: int

class WarehouseSource(Base):
    id: UUID
    name: str
    team_id: UUID

    # Storage
    object_storage_gb: float  # $0.05/GB/month
    nvme_storage_gb: float  # $1.00/GB/month
    retention_days: int = 30

    # Custom bucket
    custom_s3_bucket: str  # premium
    s3_access_key: str
    s3_secret_key: str

class WarehouseQuery(Base):
    id: UUID
    user_id: UUID
    source_id: UUID

    query_sql: Text
    execution_time_ms: int
    rows_returned: int
    bytes_scanned: int

    # Caching
    is_cached: bool
    cache_hit: bool
```

### 9. PRICING & BILLING

```python
class Subscription(Base):
    id: UUID
    team_id: UUID

    stripe_subscription_id: str
    status: Enum(ACTIVE, PAST_DUE, CANCELED)

    # Uptime
    responder_count: int  # $34 base + $34 per responder
    monitor_packs: int  # $25 per 50 monitors

    # Status Pages
    status_page_count: int  # 1 free, $15 per additional
    status_page_custom_css_count: int  # $15 each
    status_page_whitelabel_count: int  # $250 each
    status_page_password_count: int  # $50 each
    status_page_ip_restrict_count: int  # $250 each
    status_page_sso_count: int  # $250 each
    status_page_custom_email_count: int  # $250 each
    status_page_subscriber_packs: int  # $40 per 1000

    # Telemetry Bundle
    telemetry_bundle: Enum(NONE, NANO, MICRO, MEGA, TERA)
    telemetry_region: Enum(US_EAST, US_WEST, GERMANY, SINGAPORE)

    # Usage-based
    logs_gb_this_month: float  # $0.10-0.15/GB
    traces_gb_this_month: float
    metrics_1b_this_month: float  # $2.83-7.50/1B

    # Error Tracking
    error_events_this_month: int  # $0.00005 per event after 100k

    # Call Routing
    phone_number_count: int  # $250 per number

    # Warehouse
    warehouse_plan: Enum(STANDARD, TURBO, ULTRA, HYPER)
    warehouse_object_storage_gb: float
    warehouse_nvme_storage_gb: float
    warehouse_custom_bucket: bool  # premium

class UsageRecord(Base):
    id: UUID
    subscription_id: UUID
    period_start: DateTime
    period_end: DateTime

    # Detailed breakdown
    logs_ingested_gb: float
    traces_ingested_gb: float
    metrics_ingested_1b: float
    error_events: int
    call_minutes: int
    warehouse_queries: int
```

---

## Endpoints API Complets

### UPTIME (existant + étendre)
- GET /api/uptime/monitors
- POST /api/uptime/monitors
- GET /api/uptime/monitors/{id}
- PATCH /api/uptime/monitors/{id}
- DELETE /api/uptime/monitors/{id}
- GET /api/uptime/monitors/{id}/checks
- POST /api/uptime/heartbeats/{id}/beat  # NEW: CRON heartbeats
- POST /api/uptime/transaction-tests  # NEW: Playwright

### INCIDENTS
- GET /api/incidents
- POST /api/incidents
- GET /api/incidents/{id}
- PATCH /api/incidents/{id}/acknowledge
- PATCH /api/incidents/{id}/resolve
- POST /api/incidents/{id}/assign-role  # NEW
- GET /api/incidents/{id}/timeline
- POST /api/incidents/{id}/timeline-event
- GET /api/incidents/{id}/postmortem  # AI-generated
- GET /api/incidents/metrics/mtta-mttr

### ON-CALL
- GET /api/oncall/schedules
- POST /api/oncall/schedules
- GET /api/oncall/schedules/{id}/shifts
- POST /api/oncall/schedules/{id}/shifts
- POST /api/oncall/shifts/{id}/override
- POST /api/oncall/cover-requests
- PATCH /api/oncall/cover-requests/{id}/accept
- GET /api/oncall/who-is-oncall

### LOGS
- POST /api/logs/ingest  # HTTP ingestion
- POST /api/logs/query  # SQL/VRL/PromQL
- GET /api/logs/live-tail
- POST /api/logs/sources
- GET /api/logs/sources/{id}
- PATCH /api/logs/sources/{id}/vrl-pipeline
- POST /api/logs/derived-metrics

### TRACES
- POST /api/traces/ingest  # OpenTelemetry
- GET /api/traces/{trace_id}
- GET /api/traces/search

### METRICS
- POST /api/metrics/ingest  # Prometheus remote write
- POST /api/metrics/query  # PromQL
- GET /api/metrics/dashboards
- POST /api/metrics/dashboards
- POST /api/metrics/alerts

### ERRORS
- POST /api/errors/{project_id}/store  # Sentry protocol
- GET /api/errors/projects
- POST /api/errors/projects
- GET /api/errors/projects/{id}/events
- GET /api/errors/projects/{id}/groups
- PATCH /api/errors/groups/{id}/snooze
- PATCH /api/errors/groups/{id}/resolve
- GET /api/errors/events/{id}/bugfix-prompt  # AI

### STATUS PAGES
- GET /api/status-pages
- POST /api/status-pages
- PATCH /api/status-pages/{id}/styling  # CSS/JS
- PATCH /api/status-pages/{id}/security  # Password/IP/SSO
- POST /api/status-pages/{id}/subscribers
- GET /api/status-pages/{id}/analytics

### CALL ROUTING
- POST /api/call/numbers
- GET /api/call/numbers
- POST /api/call/incoming-webhook  # Twilio webhook
- GET /api/call/calls/{id}/transcription

### WAREHOUSE
- POST /api/warehouse/sources
- POST /api/warehouse/query  # SQL
- GET /api/warehouse/query/{id}/results
- PATCH /api/warehouse/sources/{id}/storage  # NVMe/S3 config

### INTEGRATIONS
- POST /api/integrations/slack/install
- POST /api/integrations/slack/command  # /incident
- POST /api/integrations/teams/install
- POST /api/integrations/linear/connect
- POST /api/integrations/jira/connect

### SSO/AUTH
- GET /api/auth/sso/google
- GET /api/auth/sso/azure
- GET /api/auth/sso/okta
- POST /api/auth/scim/v2/Users  # SCIM provisioning
- GET /api/auth/audit-logs

### TERRAFORM
- Implement Terraform provider: `terraform-provider-betterstack`

---

## Logique de Facturation Exacte

### Pricing Calculator

```python
def calculate_monthly_cost(subscription: Subscription) -> float:
    total = 0.0

    # 1. Uptime Monitoring
    if subscription.responder_count > 0:
        base_responder = 34.00  # First responder
        additional = (subscription.responder_count - 1) * 34.00
        total += base_responder + additional

    # Additional monitors (50-pack)
    total += subscription.monitor_packs * 25.00

    # 2. Status Pages
    if subscription.status_page_count > 1:
        total += (subscription.status_page_count - 1) * 15.00

    total += subscription.status_page_custom_css_count * 15.00
    total += subscription.status_page_whitelabel_count * 250.00
    total += subscription.status_page_password_count * 50.00
    total += subscription.status_page_ip_restrict_count * 250.00
    total += subscription.status_page_sso_count * 250.00
    total += subscription.status_page_custom_email_count * 250.00
    total += subscription.status_page_subscriber_packs * 40.00

    # 3. Telemetry Bundle
    bundle_prices = {
        "NANO": 30.00,
        "MICRO": 120.00,
        "MEGA": 250.00,
        "TERA": 500.00
    }
    if subscription.telemetry_bundle in bundle_prices:
        total += bundle_prices[subscription.telemetry_bundle]

    # 4. Overage - Logs/Traces
    region_costs = {
        "GERMANY": {"logs": 0.10, "traces": 0.10},
        "US_EAST": {"logs": 0.10, "traces": 0.10}
    }

    bundle_quotas = {
        "NANO": {"logs": 50, "traces": 50, "metrics": 2.5},
        "MICRO": {"logs": 210, "traces": 210, "metrics": 11},
        "MEGA": {"logs": 450, "traces": 450, "metrics": 30},
        "TERA": {"logs": 925, "traces": 925, "metrics": 70}
    }

    if subscription.telemetry_bundle:
        quota = bundle_quotas.get(subscription.telemetry_bundle, {})

        logs_overage = max(0, subscription.logs_gb_this_month - quota.get("logs", 0))
        traces_overage = max(0, subscription.traces_gb_this_month - quota.get("traces", 0))

        region_cost = region_costs.get(subscription.telemetry_region, region_costs["GERMANY"])
        total += logs_overage * region_cost["logs"]
        total += traces_overage * region_cost["traces"]

    # 5. Metrics overage
    metrics_overage = max(0, subscription.metrics_1b_this_month - quota.get("metrics", 0))
    total += metrics_overage * 5.00  # $5 per 1B

    # 6. Error Tracking
    error_overage = max(0, subscription.error_events_this_month - 100000)
    total += error_overage * 0.00005

    # 7. Call Routing
    total += subscription.phone_number_count * 250.00

    # 8. Warehouse
    warehouse_plans = {
        "STANDARD": 0.0,
        "TURBO": 2000.00,
        "ULTRA": 4000.00,
        "HYPER": 6000.00
    }
    total += warehouse_plans.get(subscription.warehouse_plan, 0.0)

    # Warehouse storage
    total += subscription.warehouse_object_storage_gb * 0.05  # per GB/month
    total += subscription.warehouse_nvme_storage_gb * 1.00  # per GB/month

    if subscription.warehouse_custom_bucket:
        total += 250.00

    return total
```

---

## Mapping Fonctionnalités ↔ Modules

| FONCTIONNALITÉ BETTER STACK | MODULE | IMPLÉMENTÉ | PRIORITÉ |
|------------------------------|--------|------------|----------|
| Uptime monitoring HTTP/HTTPS | Uptime | ✓ | P0 |
| Heartbeat monitoring (CRON) | Uptime | ✗ | P1 |
| Transaction monitoring (Playwright) | Uptime | ✗ | P1 |
| SSL/DNS monitoring | Uptime | ✗ | P1 |
| Incident creation/resolve | Incidents | ✓ | P0 |
| MTTA/MTTR tracking | Incidents | ✗ | P0 |
| AI post-mortems | Incidents | ✗ | P0 |
| Root cause analysis | Incidents | Partial | P0 |
| Slack workflows | Integrations | ✗ | P0 |
| MS Teams workflows | Integrations | ✗ | P1 |
| On-call schedules | On-call | ✗ | P0 |
| On-call rotations | On-call | ✗ | P0 |
| Cover requests | On-call | ✗ | P1 |
| Status pages basic | Status Pages | ✓ | P0 |
| Status pages CSS/JS | Status Pages | ✗ | P1 |
| Status pages white-label | Status Pages | ✗ | P2 |
| Status pages SSO | Status Pages | ✗ | P2 |
| Log ingestion (HTTP) | Logs | ✗ | P0 |
| Log ingestion (Vector/Fluent) | Logs | ✗ | P1 |
| VRL transformation | Logs | ✗ | P0 |
| Live tail | Logs | ✗ | P0 |
| Log queries (SQL) | Logs | ✗ | P0 |
| Log queries (VRL) | Logs | ✗ | P1 |
| Anomaly detection | Logs | ✗ | P1 |
| Custom S3 bucket | Logs | ✗ | P2 |
| Derived metrics | Logs | ✗ | P1 |
| Trace ingestion (OTLP) | Traces | ✗ | P0 |
| Trace visualization | Traces | ✗ | P1 |
| Metrics ingestion (Prometheus) | Metrics | ✗ | P0 |
| PromQL queries | Metrics | ✗ | P0 |
| Dashboards | Metrics | ✗ | P0 |
| Metric alerts | Metrics | ✗ | P1 |
| Error tracking (Sentry SDK) | Errors | ✗ | P0 |
| Error grouping | Errors | ✗ | P0 |
| AI bugfix prompts | Errors | ✗ | P1 |
| Release tracking | Errors | ✗ | P1 |
| Linear/Jira integration | Errors | ✗ | P2 |
| Phone numbers | Call Routing | ✗ | P2 |
| Call transcriptions | Call Routing | ✗ | P2 |
| Data warehouse (ClickHouse) | Warehouse | ✗ | P1 |
| NVMe tier | Warehouse | ✗ | P1 |
| S3 tier | Warehouse | ✗ | P1 |
| SQL API | Warehouse | ✗ | P1 |
| SSO (Google/Azure/Okta) | Auth | ✗ | P1 |
| RBAC | Auth | ✗ | P1 |
| SCIM provisioning | Auth | ✗ | P2 |
| Audit logs | Auth | ✗ | P1 |
| Terraform provider | Infrastructure | ✗ | P2 |
| MCP server | Infrastructure | ✗ | P2 |

---

## Contraintes Techniques

### Stack Additions Requises

```python
# requirements.txt additions
clickhouse-driver==0.2.6  # Data Warehouse
clickhouse-connect==0.6.22
opentelemetry-api==1.21.0  # Traces
opentelemetry-sdk==1.21.0
opentelemetry-instrumentation==0.42b0
prometheus-client==0.19.0  # Metrics
sentry-sdk==1.40.0  # Error tracking compatibility
twilio==8.11.0  # Call routing
boto3==1.34.22  # S3 integration
playwright==1.40.0  # Transaction monitoring
slack-sdk==3.26.2  # Slack integration
msgraph-core==1.0.0  # MS Teams
msal==1.26.0  # Azure SSO
google-auth==2.26.2  # Google SSO
PyJWT==2.8.0  # SSO tokens
python-jose[cryptography]==3.3.0  # Already present
anthropic==0.18.1  # AI features
```

### Infrastructure

```yaml
# docker-compose.yml additions
services:
  clickhouse:
    image: clickhouse/clickhouse-server:23.12
    ports:
      - "8123:8123"  # HTTP
      - "9000:9000"  # Native
    volumes:
      - clickhouse_data:/var/lib/clickhouse
    environment:
      CLICKHOUSE_DB: telemetry
      CLICKHOUSE_USER: admin
      CLICKHOUSE_PASSWORD: ${CLICKHOUSE_PASSWORD}

  minio:
    image: minio/minio:latest
    ports:
      - "9001:9001"  # Console
      - "9000:9000"  # S3 API
    command: server /data --console-address ":9001"
    volumes:
      - minio_data:/data
    environment:
      MINIO_ROOT_USER: admin
      MINIO_ROOT_PASSWORD: ${MINIO_PASSWORD}

  vector:
    image: timberio/vector:0.35.0-alpine
    ports:
      - "8686:8686"  # Log ingestion
    volumes:
      - ./vector.toml:/etc/vector/vector.toml:ro

volumes:
  clickhouse_data:
  minio_data:
```

---

## Checklist Conformité 100%

### Phase 1: Core Infrastructure (Semaine 1-2)
- [ ] ClickHouse deployment + schema
- [ ] MinIO/S3 integration
- [ ] Vector log ingestion pipeline
- [ ] PostgreSQL schema extensions
- [ ] Redis pub/sub for real-time features

### Phase 2: Incidents & On-call (Semaine 3-4)
- [ ] Incident models étendus (MTTA/MTTR, roles, timeline)
- [ ] On-call schedules + rotations
- [ ] Cover requests
- [ ] Slack integration (OAuth, /incident command, channel creation)
- [ ] MS Teams integration
- [ ] AI post-mortem generation (Anthropic API)
- [ ] Root cause analysis AI

### Phase 3: Logs & Traces (Semaine 5-6)
- [ ] Log ingestion API (HTTP, Vector)
- [ ] VRL pipeline execution
- [ ] ClickHouse log storage
- [ ] SQL query API
- [ ] Live tail WebSocket
- [ ] Anomaly detection alerts
- [ ] OpenTelemetry trace ingestion
- [ ] Trace storage + visualization
- [ ] Derived metrics generation

### Phase 4: Metrics & Dashboards (Semaine 7)
- [ ] Prometheus remote write endpoint
- [ ] PromQL query engine
- [ ] Dashboard CRUD
- [ ] Metric alerts
- [ ] Anomaly detection for metrics

### Phase 5: Error Tracking (Semaine 8)
- [ ] Sentry SDK compatibility layer
- [ ] Error event ingestion
- [ ] Fingerprinting + grouping
- [ ] AI bugfix prompts
- [ ] Release tracking
- [ ] Linear/Jira integrations

### Phase 6: Status Pages Advanced (Semaine 9)
- [ ] Custom CSS/JS injection
- [ ] White-label mode
- [ ] Password protection
- [ ] IP restrictions
- [ ] SSO integration
- [ ] Custom email domain
- [ ] Subscriber management (quota tracking)
- [ ] Multi-language i18n

### Phase 7: Call Routing (Semaine 10)
- [ ] Twilio integration
- [ ] Phone number provisioning
- [ ] Incoming call webhooks
- [ ] Call transcription (Whisper API)
- [ ] Incident auto-creation from calls
- [ ] Allowlist management

### Phase 8: Data Warehouse (Semaine 11)
- [ ] ClickHouse warehouse schema
- [ ] NVMe tier (local SSD)
- [ ] S3 tier (MinIO)
- [ ] SQL query API
- [ ] Query limits enforcement (by plan)
- [ ] Custom bucket support
- [ ] Query caching

### Phase 9: Pricing & Billing (Semaine 12)
- [ ] Subscription model complet
- [ ] Usage tracking (logs GB, metrics 1B, errors)
- [ ] Stripe invoice items pour overages
- [ ] Bundle quotas enforcement
- [ ] Per-feature pricing (status page addons)
- [ ] Telemetry region pricing

### Phase 10: Auth & Security (Semaine 13)
- [ ] Google SSO
- [ ] Azure SSO
- [ ] Okta SSO
- [ ] RBAC implementation
- [ ] SCIM v2 provisioning
- [ ] Audit logs
- [ ] API key management
- [ ] VPC peering (Enterprise)

### Phase 11: APIs & Integrations (Semaine 14)
- [ ] REST API complète (tous endpoints)
- [ ] Webhooks sortants
- [ ] Terraform provider
- [ ] MCP server (Claude Code integration)
- [ ] API documentation (OpenAPI/Swagger)

### Phase 12: Testing & Launch (Semaine 15-16)
- [ ] Unit tests (>80% coverage)
- [ ] Integration tests
- [ ] Load testing (10k monitors, 1M events/min)
- [ ] Security audit
- [ ] GDPR compliance check
- [ ] SOC2 documentation
- [ ] Production deployment
- [ ] Monitoring setup (dogfooding)

---

## Résumé Exécutif

**Gap Analysis**: 73% des fonctionnalités Better Stack manquent
**Effort Estimé**: 16 semaines (4 mois) avec 2 développeurs
**Coût Infrastructure**: ~$500/mois (ClickHouse, S3, Twilio)
**Priorité P0**: Incidents, On-call, Logs, Metrics, Errors (8 semaines)
**Conformité Pricing**: 100% des prix, quotas, limites identiques
