import { TechnicalProfile } from "./tech-catalog-types";

const profiles: TechnicalProfile[] = [
  // ── Murex ──────────────────────────────────────────────────────────
  {
    appKey: "murex",
    infrastructure: {
      hosting: "On-Premises",
      region: "LDN-DC1",
      environments: [
        { name: "Production", url: "https://murex.internal.firm.com", version: "3.1.115", last_deployed: "2026-02-28" },
        { name: "UAT", url: "https://murex-uat.internal.firm.com", version: "3.1.117", last_deployed: "2026-03-10" },
        { name: "DR", url: "https://murex-dr.internal.firm.com", version: "3.1.115", last_deployed: "2026-02-28" },
      ],
      compute: "Bare-metal cluster (64 cores / 512 GB RAM x 8 nodes)",
      storage: "Oracle RAC 19c — 12 TB allocated",
      network_zone: "Restricted (Zone A)",
      disaster_recovery: "Active-passive, LDN-DC2 failover",
      backup_frequency: "Hourly incremental / Daily full",
    },
    sla: {
      availability_target: "99.95%",
      current_availability: "99.92%",
      rto_hours: 1,
      rpo_hours: 0.25,
      p1_response_minutes: 15,
      last_incident: "2026-01-14",
      health_status: "degraded",
    },
    dependencies: {
      upstream: [
        { app_key: "data_warehouse", display_name: "Data Warehouse", type: "data", protocol: "JDBC", criticality: "high", notes: "EOD price feed" },
      ],
      downstream: [
        { app_key: "risk_engine", display_name: "Risk Engine", type: "data", protocol: "Kafka", criticality: "critical", notes: "Real-time trade events" },
        { app_key: "settlement_system", display_name: "Settlement System", type: "event", protocol: "MQ", criticality: "high" },
        { app_key: "compliance_monitor", display_name: "Compliance Monitor", type: "event", protocol: "Kafka", criticality: "high", notes: "Trade surveillance feed" },
      ],
    },
    api_endpoints: [
      { method: "GET", path: "/api/v2/trades", description: "Query trade blotter", auth: "mTLS + JWT", rate_limit: "500 req/s" },
      { method: "POST", path: "/api/v2/trades", description: "Submit new trade", auth: "mTLS + JWT", rate_limit: "100 req/s" },
      { method: "GET", path: "/api/v2/positions", description: "Real-time position snapshot", auth: "mTLS + JWT" },
      { method: "GET", path: "/api/v2/health", description: "Health check endpoint", auth: "None" },
    ],
    diagrams: [
      { name: "Murex Integration Architecture", file: "docs/murex-architecture.drawio", type: "architecture", last_updated: "2025-11-20" },
      { name: "Trade Flow Sequence", file: "docs/murex-trade-flow.drawio", type: "sequence", last_updated: "2025-09-15" },
    ],
    tech_debt: {
      score: 78,
      modernization_score: 25,
      last_assessed: "2026-01-30",
      notes: [
        "Oracle RAC nearing end-of-support — migration to PostgreSQL planned",
        "Monolithic deployment — no container support",
        "Custom MQ adapters need rewrite for Kafka-native integration",
      ],
      migration_target: "Murex MX.3 Cloud (2027 Q2)",
    },
    cmdb: {
      ci_id: "CI-00142",
      ci_class: "Business Application",
      operational_status: "Operational",
      business_criticality: "1-critical",
      change_group: "CAB-Trading",
      assignment_group: "Trading-Tech-L3",
      cost_center: "CC-4010-Trading",
      attestation_date: "2026-01-15",
    },
  },

  // ── Risk Engine ────────────────────────────────────────────────────
  {
    appKey: "risk_engine",
    infrastructure: {
      hosting: "AWS EKS",
      region: "eu-west-1",
      environments: [
        { name: "Production", url: "https://risk.internal.firm.com", version: "5.4.2", last_deployed: "2026-03-12" },
        { name: "UAT", url: "https://risk-uat.internal.firm.com", version: "5.5.0-rc1", last_deployed: "2026-03-15" },
        { name: "Dev", url: "https://risk-dev.internal.firm.com", version: "5.5.0-dev", last_deployed: "2026-03-17" },
      ],
      compute: "EKS managed — 12 x m6i.4xlarge (spot + on-demand mix)",
      storage: "Amazon Aurora PostgreSQL 15 — 2 TB",
      network_zone: "Private VPC (10.20.0.0/16)",
      disaster_recovery: "Multi-AZ Aurora, cross-region read replicas",
      backup_frequency: "Continuous (Aurora backtrack) + Daily snapshots",
    },
    sla: {
      availability_target: "99.99%",
      current_availability: "99.98%",
      rto_hours: 0.5,
      rpo_hours: 0,
      p1_response_minutes: 10,
      last_incident: "2025-11-02",
      health_status: "healthy",
    },
    dependencies: {
      upstream: [
        { app_key: "murex", display_name: "Murex", type: "data", protocol: "Kafka", criticality: "critical", notes: "Real-time trade events" },
        { app_key: "data_warehouse", display_name: "Data Warehouse", type: "data", protocol: "S3", criticality: "high", notes: "EOD market data snapshots" },
        { app_key: "portfolio_manager", display_name: "Portfolio Manager", type: "api", protocol: "gRPC", criticality: "medium", notes: "Portfolio composition lookups" },
      ],
      downstream: [
        { app_key: "client_reporting", display_name: "Client Reporting", type: "data", protocol: "Kafka", criticality: "high", notes: "Risk metrics for client reports" },
        { app_key: "compliance_monitor", display_name: "Compliance Monitor", type: "api", protocol: "REST", criticality: "medium" },
      ],
    },
    api_endpoints: [
      { method: "GET", path: "/api/v1/risk/var", description: "Value-at-Risk calculations", auth: "OAuth2", rate_limit: "200 req/s" },
      { method: "POST", path: "/api/v1/risk/simulate", description: "Run stress test scenario", auth: "OAuth2", rate_limit: "20 req/s" },
      { method: "GET", path: "/api/v1/risk/exposure/{portfolio}", description: "Portfolio exposure breakdown", auth: "OAuth2" },
    ],
    diagrams: [
      { name: "Risk Engine Deployment", file: "docs/risk-engine-deployment.drawio", type: "deployment", last_updated: "2026-01-08" },
      { name: "Risk Calculation Data Flow", file: "docs/risk-data-flow.drawio", type: "data-flow", last_updated: "2025-12-12" },
    ],
    tech_debt: {
      score: 22,
      modernization_score: 88,
      last_assessed: "2026-02-20",
      notes: [
        "Well-containerised, Helm-managed deployments",
        "Legacy Python 3.9 batch jobs need migration to 3.12",
      ],
    },
    cmdb: {
      ci_id: "CI-00287",
      ci_class: "Business Application",
      operational_status: "Operational",
      business_criticality: "1-critical",
      change_group: "CAB-Risk",
      assignment_group: "Risk-Quant-L3",
      cost_center: "CC-4020-Risk",
      attestation_date: "2026-02-01",
    },
  },

  // ── Client Reporting ───────────────────────────────────────────────
  {
    appKey: "client_reporting",
    infrastructure: {
      hosting: "AWS ECS Fargate",
      region: "eu-west-1",
      environments: [
        { name: "Production", url: "https://reports.internal.firm.com", version: "2.8.0", last_deployed: "2026-03-05" },
        { name: "UAT", url: "https://reports-uat.internal.firm.com", version: "2.9.0-beta", last_deployed: "2026-03-14" },
      ],
      compute: "Fargate tasks — 4 vCPU / 8 GB per task, auto-scaled 2-20",
      storage: "RDS PostgreSQL 16 — 500 GB + S3 report archive",
      network_zone: "Private VPC (10.30.0.0/16)",
      disaster_recovery: "Multi-AZ RDS, S3 cross-region replication",
      backup_frequency: "Daily RDS snapshots / S3 versioning",
    },
    sla: {
      availability_target: "99.9%",
      current_availability: "99.95%",
      rto_hours: 2,
      rpo_hours: 1,
      p1_response_minutes: 30,
      last_incident: "2025-08-19",
      health_status: "healthy",
    },
    dependencies: {
      upstream: [
        { app_key: "risk_engine", display_name: "Risk Engine", type: "data", protocol: "Kafka", criticality: "high", notes: "Risk metrics for client reports" },
        { app_key: "portfolio_manager", display_name: "Portfolio Manager", type: "api", protocol: "REST", criticality: "high", notes: "Portfolio holdings data" },
        { app_key: "data_warehouse", display_name: "Data Warehouse", type: "data", protocol: "JDBC", criticality: "medium", notes: "Historical performance data" },
      ],
      downstream: [],
    },
    api_endpoints: [
      { method: "GET", path: "/api/v1/reports", description: "List available reports", auth: "OAuth2" },
      { method: "POST", path: "/api/v1/reports/generate", description: "Trigger report generation", auth: "OAuth2", rate_limit: "10 req/min" },
      { method: "GET", path: "/api/v1/reports/{id}/download", description: "Download generated report", auth: "OAuth2" },
    ],
    diagrams: [
      { name: "Reporting Pipeline", file: "docs/reporting-pipeline.drawio", type: "data-flow", last_updated: "2025-10-01" },
    ],
    tech_debt: {
      score: 35,
      modernization_score: 72,
      last_assessed: "2026-02-10",
      notes: [
        "PDF generation library (wkhtmltopdf) deprecated — migrating to Puppeteer",
        "Report templates use legacy Jinja2 — React-PDF evaluation underway",
      ],
    },
    cmdb: {
      ci_id: "CI-00315",
      ci_class: "Business Application",
      operational_status: "Operational",
      business_criticality: "2-high",
      change_group: "CAB-Operations",
      assignment_group: "Client-Ops-L2",
      cost_center: "CC-4030-ClientOps",
      attestation_date: "2026-02-15",
    },
  },

  // ── Portfolio Manager ──────────────────────────────────────────────
  {
    appKey: "portfolio_manager",
    infrastructure: {
      hosting: "AWS EKS",
      region: "eu-west-1",
      environments: [
        { name: "Production", url: "https://pm.internal.firm.com", version: "4.1.0", last_deployed: "2026-03-11" },
        { name: "UAT", url: "https://pm-uat.internal.firm.com", version: "4.2.0-rc2", last_deployed: "2026-03-16" },
        { name: "Dev", url: "https://pm-dev.internal.firm.com", version: "4.2.0-dev", last_deployed: "2026-03-17" },
      ],
      compute: "EKS managed — 6 x c6i.2xlarge",
      storage: "Amazon Aurora PostgreSQL 16 — 800 GB",
      network_zone: "Private VPC (10.20.0.0/16)",
      disaster_recovery: "Multi-AZ Aurora, automated failover",
      backup_frequency: "Continuous (Aurora) + Weekly cross-region snapshot",
    },
    sla: {
      availability_target: "99.95%",
      current_availability: "99.97%",
      rto_hours: 1,
      rpo_hours: 0.25,
      p1_response_minutes: 15,
      last_incident: "2025-12-03",
      health_status: "healthy",
    },
    dependencies: {
      upstream: [
        { app_key: "data_warehouse", display_name: "Data Warehouse", type: "data", protocol: "S3", criticality: "high", notes: "Reference & market data" },
      ],
      downstream: [
        { app_key: "risk_engine", display_name: "Risk Engine", type: "api", protocol: "gRPC", criticality: "medium", notes: "Portfolio composition lookups" },
        { app_key: "client_reporting", display_name: "Client Reporting", type: "api", protocol: "REST", criticality: "high", notes: "Portfolio holdings data" },
        { app_key: "compliance_monitor", display_name: "Compliance Monitor", type: "event", protocol: "Kafka", criticality: "medium", notes: "Order events for surveillance" },
      ],
    },
    api_endpoints: [
      { method: "GET", path: "/api/v2/portfolios", description: "List all portfolios", auth: "OAuth2" },
      { method: "GET", path: "/api/v2/portfolios/{id}/holdings", description: "Get portfolio holdings", auth: "OAuth2" },
      { method: "POST", path: "/api/v2/portfolios/{id}/rebalance", description: "Trigger rebalance", auth: "OAuth2 + MFA", rate_limit: "5 req/min" },
      { method: "PUT", path: "/api/v2/portfolios/{id}/constraints", description: "Update investment constraints", auth: "OAuth2 + MFA" },
    ],
    diagrams: [
      { name: "Portfolio Manager Architecture", file: "docs/pm-architecture.drawio", type: "architecture", last_updated: "2026-01-20" },
      { name: "Rebalance Sequence", file: "docs/pm-rebalance-sequence.drawio", type: "sequence", last_updated: "2025-11-05" },
    ],
    tech_debt: {
      score: 15,
      modernization_score: 92,
      last_assessed: "2026-03-01",
      notes: [
        "Fully containerised with GitOps (ArgoCD)",
        "Minor: some legacy REST endpoints still on v1 schema",
      ],
    },
    cmdb: {
      ci_id: "CI-00198",
      ci_class: "Business Application",
      operational_status: "Operational",
      business_criticality: "1-critical",
      change_group: "CAB-Portfolio",
      assignment_group: "PM-Tech-L3",
      cost_center: "CC-4040-Portfolio",
      attestation_date: "2026-03-01",
    },
  },

  // ── Compliance Monitor ─────────────────────────────────────────────
  {
    appKey: "compliance_monitor",
    infrastructure: {
      hosting: "AWS ECS Fargate",
      region: "eu-west-1",
      environments: [
        { name: "Production", url: "https://compliance.internal.firm.com", version: "1.12.0", last_deployed: "2026-03-08" },
        { name: "UAT", url: "https://compliance-uat.internal.firm.com", version: "1.13.0-beta", last_deployed: "2026-03-13" },
      ],
      compute: "Fargate tasks — 2 vCPU / 4 GB, auto-scaled 3-15",
      storage: "Amazon OpenSearch — 1 TB (audit logs) + DynamoDB (rules engine)",
      network_zone: "Restricted VPC (10.40.0.0/16)",
      disaster_recovery: "Multi-AZ OpenSearch, DynamoDB global tables",
      backup_frequency: "OpenSearch hourly snapshots / DynamoDB continuous backup",
    },
    sla: {
      availability_target: "99.99%",
      current_availability: "99.99%",
      rto_hours: 0.5,
      rpo_hours: 0,
      p1_response_minutes: 5,
      last_incident: "2025-06-22",
      health_status: "healthy",
    },
    dependencies: {
      upstream: [
        { app_key: "murex", display_name: "Murex", type: "event", protocol: "Kafka", criticality: "critical", notes: "Trade surveillance feed" },
        { app_key: "portfolio_manager", display_name: "Portfolio Manager", type: "event", protocol: "Kafka", criticality: "medium", notes: "Order events for surveillance" },
        { app_key: "risk_engine", display_name: "Risk Engine", type: "api", protocol: "REST", criticality: "medium" },
      ],
      downstream: [],
    },
    api_endpoints: [
      { method: "GET", path: "/api/v1/alerts", description: "List compliance alerts", auth: "OAuth2", rate_limit: "100 req/s" },
      { method: "GET", path: "/api/v1/rules", description: "List active surveillance rules", auth: "OAuth2" },
      { method: "POST", path: "/api/v1/rules", description: "Create surveillance rule", auth: "OAuth2 + Admin" },
    ],
    diagrams: [
      { name: "Compliance Event Flow", file: "docs/compliance-event-flow.drawio", type: "data-flow", last_updated: "2025-12-18" },
    ],
    tech_debt: {
      score: 28,
      modernization_score: 80,
      last_assessed: "2026-02-15",
      notes: [
        "OpenSearch version 2.5 — upgrade to 2.11 planned for Q2",
        "Rules engine DSL needs documentation and test coverage",
      ],
    },
    cmdb: {
      ci_id: "CI-00356",
      ci_class: "Business Application",
      operational_status: "Operational",
      business_criticality: "1-critical",
      change_group: "CAB-Compliance",
      assignment_group: "Compliance-Dev-L2",
      cost_center: "CC-4050-Compliance",
      attestation_date: "2026-02-20",
    },
  },

  // ── Data Warehouse ─────────────────────────────────────────────────
  {
    appKey: "data_warehouse",
    infrastructure: {
      hosting: "Snowflake (AWS)",
      region: "eu-west-1 (AWS Frankfurt)",
      environments: [
        { name: "Production", url: "https://firm.eu-west-1.snowflakecomputing.com/PROD", version: "8.x (managed)", last_deployed: "2026-03-01" },
        { name: "UAT", url: "https://firm.eu-west-1.snowflakecomputing.com/UAT", version: "8.x (managed)", last_deployed: "2026-03-10" },
        { name: "Dev", url: "https://firm.eu-west-1.snowflakecomputing.com/DEV", version: "8.x (managed)", last_deployed: "2026-03-17" },
      ],
      compute: "Snowflake Multi-Cluster Warehouse (XL, auto-scale 1-6)",
      storage: "Snowflake managed — ~45 TB compressed",
      network_zone: "Snowflake Private Link",
      disaster_recovery: "Snowflake replication to us-east-1",
      backup_frequency: "Snowflake Time Travel (90 days) + Fail-safe (7 days)",
    },
    sla: {
      availability_target: "99.9%",
      current_availability: "99.94%",
      rto_hours: 4,
      rpo_hours: 1,
      p1_response_minutes: 30,
      last_incident: "2025-10-08",
      health_status: "healthy",
    },
    dependencies: {
      upstream: [],
      downstream: [
        { app_key: "murex", display_name: "Murex", type: "data", protocol: "JDBC", criticality: "high", notes: "EOD price feed" },
        { app_key: "risk_engine", display_name: "Risk Engine", type: "data", protocol: "S3", criticality: "high", notes: "EOD market data snapshots" },
        { app_key: "portfolio_manager", display_name: "Portfolio Manager", type: "data", protocol: "S3", criticality: "high", notes: "Reference & market data" },
        { app_key: "client_reporting", display_name: "Client Reporting", type: "data", protocol: "JDBC", criticality: "medium", notes: "Historical performance data" },
        { app_key: "research_portal", display_name: "Research Portal", type: "data", protocol: "Snowflake SQL", criticality: "medium", notes: "Backtesting datasets" },
      ],
    },
    api_endpoints: [
      { method: "GET", path: "/api/v1/datasets", description: "List available datasets", auth: "Service Account" },
      { method: "GET", path: "/api/v1/datasets/{name}/schema", description: "Get dataset schema", auth: "Service Account" },
      { method: "POST", path: "/api/v1/pipelines/trigger", description: "Trigger ETL pipeline run", auth: "Service Account + Admin" },
    ],
    diagrams: [
      { name: "Data Warehouse Architecture", file: "docs/dw-architecture.drawio", type: "architecture", last_updated: "2026-02-01" },
      { name: "ETL Pipeline Data Flow", file: "docs/dw-etl-flow.drawio", type: "data-flow", last_updated: "2025-12-20" },
    ],
    tech_debt: {
      score: 40,
      modernization_score: 65,
      last_assessed: "2026-01-25",
      notes: [
        "Legacy dbt models (v0.21) — upgrade to dbt-core 1.7 in progress",
        "Some pipelines still use Airflow 1.x DAGs — migration to Airflow 2 underway",
        "Data quality checks inconsistent across domains",
      ],
    },
    cmdb: {
      ci_id: "CI-00089",
      ci_class: "Infrastructure Service",
      operational_status: "Operational",
      business_criticality: "1-critical",
      change_group: "CAB-DataPlatform",
      assignment_group: "Data-Eng-L3",
      cost_center: "CC-4060-DataPlatform",
      attestation_date: "2026-01-31",
    },
  },

  // ── Research Portal ────────────────────────────────────────────────
  {
    appKey: "research_portal",
    infrastructure: {
      hosting: "AWS EKS",
      region: "eu-west-1",
      environments: [
        { name: "Production", url: "https://research.internal.firm.com", version: "3.2.1", last_deployed: "2026-03-06" },
        { name: "Dev", url: "https://research-dev.internal.firm.com", version: "3.3.0-dev", last_deployed: "2026-03-16" },
      ],
      compute: "EKS — 4 x p4d.24xlarge (GPU) + 8 x r6i.4xlarge (CPU)",
      storage: "S3 (research datasets) + EFS (notebooks) — ~8 TB",
      network_zone: "Private VPC (10.50.0.0/16)",
      disaster_recovery: "S3 cross-region replication, stateless compute",
      backup_frequency: "S3 versioning + Daily EFS backup",
    },
    sla: {
      availability_target: "99.5%",
      current_availability: "99.7%",
      rto_hours: 4,
      rpo_hours: 2,
      p1_response_minutes: 60,
      last_incident: "2026-02-14",
      health_status: "healthy",
    },
    dependencies: {
      upstream: [
        { app_key: "data_warehouse", display_name: "Data Warehouse", type: "data", protocol: "Snowflake SQL", criticality: "medium", notes: "Backtesting datasets" },
      ],
      downstream: [],
    },
    api_endpoints: [
      { method: "GET", path: "/api/v1/notebooks", description: "List research notebooks", auth: "OAuth2" },
      { method: "POST", path: "/api/v1/jobs", description: "Submit compute job", auth: "OAuth2", rate_limit: "20 req/min" },
      { method: "GET", path: "/api/v1/jobs/{id}/status", description: "Get job status", auth: "OAuth2" },
      { method: "GET", path: "/api/v1/datasets", description: "Browse available research datasets", auth: "OAuth2" },
    ],
    diagrams: [
      { name: "Research Platform Architecture", file: "docs/research-architecture.drawio", type: "architecture", last_updated: "2025-11-10" },
    ],
    tech_debt: {
      score: 30,
      modernization_score: 75,
      last_assessed: "2026-02-05",
      notes: [
        "JupyterHub version 3.x — upgrade to 4.x for RBAC improvements",
        "GPU scheduling could benefit from Karpenter migration",
      ],
    },
    cmdb: {
      ci_id: "CI-00412",
      ci_class: "Business Application",
      operational_status: "Operational",
      business_criticality: "3-medium",
      change_group: "CAB-Research",
      assignment_group: "Quant-Research-L2",
      cost_center: "CC-4070-Research",
      attestation_date: "2026-02-10",
    },
  },

  // ── Settlement System ──────────────────────────────────────────────
  {
    appKey: "settlement_system",
    infrastructure: {
      hosting: "On-Premises",
      region: "LDN-DC1",
      environments: [
        { name: "UAT", url: "https://settle-uat.internal.firm.com", version: "0.9.0-beta", last_deployed: "2026-03-14" },
        { name: "Dev", url: "https://settle-dev.internal.firm.com", version: "0.9.1-dev", last_deployed: "2026-03-17" },
      ],
      compute: "VMware cluster — 4 x (8 vCPU / 32 GB RAM)",
      storage: "SQL Server 2022 — 200 GB provisioned",
      network_zone: "Restricted (Zone B)",
      disaster_recovery: "SQL Always-On AG — LDN-DC2",
      backup_frequency: "Daily full / 6-hourly differential",
    },
    sla: {
      availability_target: "99.9%",
      current_availability: "N/A",
      rto_hours: 2,
      rpo_hours: 0.5,
      p1_response_minutes: 30,
      last_incident: "N/A",
      health_status: "degraded",
    },
    dependencies: {
      upstream: [
        { app_key: "murex", display_name: "Murex", type: "event", protocol: "MQ", criticality: "critical", notes: "Settlement instructions from trade lifecycle" },
      ],
      downstream: [],
    },
    api_endpoints: [
      { method: "GET", path: "/api/v1/settlements", description: "List settlement instructions", auth: "mTLS" },
      { method: "POST", path: "/api/v1/settlements/match", description: "Trigger matching engine", auth: "mTLS" },
    ],
    diagrams: [
      { name: "Settlement System Design", file: "docs/settlement-architecture.drawio", type: "architecture", last_updated: "2026-03-01" },
      { name: "Settlement Matching Flow", file: "docs/settlement-matching.drawio", type: "sequence", last_updated: "2026-02-20" },
    ],
    tech_debt: {
      score: 55,
      modernization_score: 40,
      last_assessed: "2026-03-10",
      notes: [
        "Pre-production — architecture under active development",
        "SQL Server chosen for SWIFT adapter compatibility — cloud migration deferred to post-launch",
        "No CI/CD pipeline yet — manual deployment process",
      ],
      migration_target: "AWS ECS (post go-live, 2027 Q1)",
    },
    cmdb: {
      ci_id: "CI-00478",
      ci_class: "Business Application",
      operational_status: "Build",
      business_criticality: "2-high",
      change_group: "CAB-Operations",
      assignment_group: "Settlement-Dev-L2",
      cost_center: "CC-4080-Settlement",
      attestation_date: "2026-03-10",
    },
  },
];

export function getAllTechnicalProfiles(): TechnicalProfile[] {
  return profiles;
}

export function getTechnicalProfile(appKey: string): TechnicalProfile | undefined {
  return profiles.find((p) => p.appKey === appKey);
}
