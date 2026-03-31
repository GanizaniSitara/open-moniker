// Technical Catalog types — CMDB-style infrastructure metadata per application

export interface Environment {
  name: string;
  url: string;
  version: string;
  last_deployed: string;
}

export interface Dependency {
  app_key: string;
  display_name: string;
  type: "data" | "api" | "event" | "batch";
  protocol: string;
  criticality: "critical" | "high" | "medium" | "low";
  notes?: string;
}

export interface ApiEndpoint {
  method: "GET" | "POST" | "PUT" | "DELETE" | "PATCH";
  path: string;
  description: string;
  auth: string;
  rate_limit?: string;
}

export interface DiagramRef {
  name: string;
  file: string;
  type: "architecture" | "sequence" | "deployment" | "data-flow";
  last_updated: string;
}

export interface TechnicalProfile {
  appKey: string;
  infrastructure: {
    hosting: string;
    region: string;
    environments: Environment[];
    compute: string;
    storage: string;
    network_zone: string;
    disaster_recovery: string;
    backup_frequency: string;
  };
  sla: {
    availability_target: string;
    current_availability: string;
    rto_hours: number;
    rpo_hours: number;
    p1_response_minutes: number;
    last_incident: string;
    health_status: "healthy" | "degraded" | "critical";
  };
  dependencies: {
    upstream: Dependency[];
    downstream: Dependency[];
  };
  api_endpoints: ApiEndpoint[];
  diagrams: DiagramRef[];
  tech_debt: {
    score: number;
    modernization_score: number;
    last_assessed: string;
    notes: string[];
    migration_target?: string;
  };
  cmdb: {
    ci_id: string;
    ci_class: string;
    operational_status: string;
    business_criticality: "1-critical" | "2-high" | "3-medium" | "4-low";
    change_group: string;
    assignment_group: string;
    cost_center: string;
    attestation_date: string;
  };
}
