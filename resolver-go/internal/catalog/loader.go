package catalog

import (
	"fmt"
	"os"

	"gopkg.in/yaml.v3"
)

// CatalogYAML represents the structure of a catalog YAML file
// The catalog YAML is a flat map of path -> node (no "nodes" wrapper)
type CatalogYAML map[string]*CatalogNodeYAML

// CatalogNodeYAML represents a node in the YAML file
type CatalogNodeYAML struct {
	DisplayName          string                 `yaml:"display_name"`
	Description          string                 `yaml:"description"`
	TechnicalDescription string                 `yaml:"technical_description"`
	AssetClass           string                 `yaml:"asset_class"`
	UpdateFrequency      string                 `yaml:"update_frequency"`
	Domain               *string                `yaml:"domain"`
	Vendor               *string                `yaml:"vendor"`
	Maturity             *string                `yaml:"maturity"`
	Ownership            *OwnershipYAML         `yaml:"ownership"`
	SourceBinding        *SourceBindingYAML     `yaml:"source_binding"`
	AccessPolicy         *AccessPolicyYAML      `yaml:"access_policy"`
	Documentation        *Documentation         `yaml:"documentation"`
	Schema               map[string]interface{} `yaml:"schema"`
	Classification       string                 `yaml:"classification"`
	Tags                 []string               `yaml:"tags"`
	Status               string                 `yaml:"status"`
	IsLeaf               bool                   `yaml:"is_leaf"`
	Successor            *string                `yaml:"successor"`
	DeprecationMessage   *string                `yaml:"deprecation_message"`
	MigrationGuideURL    *string                `yaml:"migration_guide_url"`
	SunsetDeadline       *string                `yaml:"sunset_deadline"`
	Metadata             map[string]interface{} `yaml:"metadata"`
	DataQuality          map[string]interface{} `yaml:"data_quality"`
	SLAData              map[string]interface{} `yaml:"sla"`
	FreshnessData        map[string]interface{} `yaml:"freshness"`
}

// OwnershipYAML represents ownership in YAML
type OwnershipYAML struct {
	AccountableOwner *string `yaml:"accountable_owner"`
	DataSpecialist   *string `yaml:"data_specialist"`
	SupportChannel   *string `yaml:"support_channel"`
	ADOP             *string `yaml:"adop"`
	ADS              *string `yaml:"ads"`
	ADAL             *string `yaml:"adal"`
	ADOPName         *string `yaml:"adop_name"`
	ADSName          *string `yaml:"ads_name"`
	ADALName         *string `yaml:"adal_name"`
	UI               *string `yaml:"ui"`
}

// SourceBindingYAML represents a source binding in YAML
type SourceBindingYAML struct {
	Type              string                 `yaml:"type"`
	Config            map[string]interface{} `yaml:"config"`
	AllowedOperations []string               `yaml:"allowed_operations"`
	Schema            map[string]interface{} `yaml:"schema"`
	ReadOnly          *bool                  `yaml:"read_only"`
}

// AccessPolicyYAML represents access policy in YAML
type AccessPolicyYAML struct {
	RequiredSegments       []int    `yaml:"required_segments"`
	MinFilters             *int     `yaml:"min_filters"`
	BlockedPatterns        []string `yaml:"blocked_patterns"`
	MaxRowsWarn            *int     `yaml:"max_rows_warn"`
	MaxRowsBlock           *int     `yaml:"max_rows_block"`
	CardinalityMultipliers []int    `yaml:"cardinality_multipliers"`
	BaseRowCount           *int     `yaml:"base_row_count"`
	DenialMessage          *string  `yaml:"denial_message"`
}

// LoadCatalog loads a catalog from a YAML file
func LoadCatalog(path string) ([]*CatalogNode, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, fmt.Errorf("read catalog file: %w", err)
	}

	var catalogYAML CatalogYAML
	if err := yaml.Unmarshal(data, &catalogYAML); err != nil {
		return nil, fmt.Errorf("parse catalog YAML: %w", err)
	}

	nodes := make([]*CatalogNode, 0, len(catalogYAML))
	for path, nodeYAML := range catalogYAML {
		if nodeYAML != nil {
			node := convertYAMLToNode(path, nodeYAML)
			nodes = append(nodes, node)
		}
	}

	return nodes, nil
}

func convertYAMLToNode(path string, yaml *CatalogNodeYAML) *CatalogNode {
	node := &CatalogNode{
		Path:            path,
		DisplayName:     yaml.DisplayName,
		Description:     yaml.Description,
		AssetClass:      yaml.AssetClass,
		UpdateFrequency: yaml.UpdateFrequency,
		Domain:          yaml.Domain,
		Vendor:          yaml.Vendor,
		Maturity:        yaml.Maturity,
		Classification:  yaml.Classification,
		Tags:            yaml.Tags,
		IsLeaf:          yaml.IsLeaf,
		Successor:       yaml.Successor,
	}

	// Set technical description
	if yaml.TechnicalDescription != "" {
		td := yaml.TechnicalDescription
		node.TechnicalDescription = &td
	}

	// Set documentation
	if yaml.Documentation != nil {
		node.Documentation = yaml.Documentation
	}

	// Set node-level schema (separate from source_binding schema)
	if yaml.Schema != nil {
		node.DataSchema = &DataSchema{}
		// Parse columns if present
		if cols, ok := yaml.Schema["columns"]; ok {
			if colList, ok := cols.([]interface{}); ok {
				for _, c := range colList {
					if cm, ok := c.(map[string]interface{}); ok {
						col := ColumnSchema{
							Name:        stringFromMap(cm, "name"),
							DataType:    stringFromMap(cm, "type"),
							Description: stringFromMap(cm, "description"),
						}
						if st, ok := cm["semantic_type"].(string); ok {
							col.SemanticType = &st
						}
						if pk, ok := cm["primary_key"].(bool); ok {
							col.PrimaryKey = pk
						}
						if fk, ok := cm["foreign_key"].(string); ok {
							col.ForeignKey = &fk
						}
						node.DataSchema.Columns = append(node.DataSchema.Columns, col)
					}
				}
			}
		}
		if tags, ok := yaml.Schema["semantic_tags"]; ok {
			if tagList, ok := tags.([]interface{}); ok {
				for _, t := range tagList {
					if s, ok := t.(string); ok {
						node.DataSchema.SemanticTags = append(node.DataSchema.SemanticTags, s)
					}
				}
			}
		}
		if uc, ok := yaml.Schema["use_cases"]; ok {
			if ucList, ok := uc.([]interface{}); ok {
				for _, u := range ucList {
					if s, ok := u.(string); ok {
						node.DataSchema.UseCases = append(node.DataSchema.UseCases, s)
					}
				}
			}
		}
	}

	// Set default classification
	if node.Classification == "" {
		node.Classification = "internal"
	}

	// Parse status
	if yaml.Status != "" {
		node.Status = NodeStatus(yaml.Status)
	} else {
		node.Status = NodeStatusActive
	}

	// Convert ownership
	if yaml.Ownership != nil {
		node.Ownership = &Ownership{
			AccountableOwner: yaml.Ownership.AccountableOwner,
			DataSpecialist:   yaml.Ownership.DataSpecialist,
			SupportChannel:   yaml.Ownership.SupportChannel,
			ADOP:             yaml.Ownership.ADOP,
			ADS:              yaml.Ownership.ADS,
			ADAL:             yaml.Ownership.ADAL,
			ADOPName:         yaml.Ownership.ADOPName,
			ADSName:          yaml.Ownership.ADSName,
			ADALName:         yaml.Ownership.ADALName,
			UI:               yaml.Ownership.UI,
		}
	}

	// Convert source binding
	if yaml.SourceBinding != nil {
		readOnly := true
		if yaml.SourceBinding.ReadOnly != nil {
			readOnly = *yaml.SourceBinding.ReadOnly
		}

		node.SourceBinding = &SourceBinding{
			SourceType:        SourceType(yaml.SourceBinding.Type),
			Config:            yaml.SourceBinding.Config,
			AllowedOperations: yaml.SourceBinding.AllowedOperations,
			Schema:            yaml.SourceBinding.Schema,
			ReadOnly:          readOnly,
		}
		// Auto-detect leaf node when source_binding is present
		node.IsLeaf = true
	}

	// Convert access policy
	if yaml.AccessPolicy != nil {
		baseRowCount := 100
		if yaml.AccessPolicy.BaseRowCount != nil {
			baseRowCount = *yaml.AccessPolicy.BaseRowCount
		}

		node.AccessPolicy = &AccessPolicy{
			RequiredSegments:       yaml.AccessPolicy.RequiredSegments,
			MinFilters:             0,
			BlockedPatterns:        yaml.AccessPolicy.BlockedPatterns,
			MaxRowsWarn:            yaml.AccessPolicy.MaxRowsWarn,
			MaxRowsBlock:           yaml.AccessPolicy.MaxRowsBlock,
			CardinalityMultipliers: yaml.AccessPolicy.CardinalityMultipliers,
			BaseRowCount:           baseRowCount,
			DenialMessage:          yaml.AccessPolicy.DenialMessage,
		}

		if yaml.AccessPolicy.MinFilters != nil {
			node.AccessPolicy.MinFilters = *yaml.AccessPolicy.MinFilters
		}
	}

	// Copy deprecation fields
	if yaml.DeprecationMessage != nil {
		node.DeprecationMessage = yaml.DeprecationMessage
	}
	if yaml.MigrationGuideURL != nil {
		node.MigrationGuideURL = yaml.MigrationGuideURL
	}
	if yaml.SunsetDeadline != nil {
		node.SunsetDeadline = yaml.SunsetDeadline
	}

	// Copy metadata
	if yaml.Metadata != nil {
		node.Metadata = yaml.Metadata
	}

	// Parse data quality
	if yaml.DataQuality != nil {
		node.DataQuality = parseDataQuality(yaml.DataQuality)
	}

	// Parse SLA
	if yaml.SLAData != nil {
		node.SLA = parseSLA(yaml.SLAData)
	}

	// Parse freshness
	if yaml.FreshnessData != nil {
		node.Freshness = parseFreshness(yaml.FreshnessData)
	}

	return node
}

func parseDataQuality(data map[string]interface{}) *DataQuality {
	dq := &DataQuality{}
	if v, ok := data["dq_owner"].(string); ok {
		dq.DQOwner = &v
	}
	if v, ok := data["quality_score"].(float64); ok {
		dq.QualityScore = &v
	}
	// yaml.v3 may decode integers as int, so handle both
	if v, ok := data["quality_score"].(int); ok {
		f := float64(v)
		dq.QualityScore = &f
	}
	if v, ok := data["last_validated"].(string); ok {
		dq.LastValidated = &v
	}
	if rules, ok := data["validation_rules"].([]interface{}); ok {
		for _, r := range rules {
			if s, ok := r.(string); ok {
				dq.ValidationRules = append(dq.ValidationRules, s)
			}
		}
	}
	if issues, ok := data["known_issues"].([]interface{}); ok {
		for _, i := range issues {
			if s, ok := i.(string); ok {
				dq.KnownIssues = append(dq.KnownIssues, s)
			}
		}
	}
	return dq
}

func parseSLA(data map[string]interface{}) *SLA {
	s := &SLA{}
	if v, ok := data["freshness"].(string); ok {
		s.Freshness = &v
	}
	if v, ok := data["availability"].(string); ok {
		s.Availability = &v
	}
	if v, ok := data["support_hours"].(string); ok {
		s.SupportHours = &v
	}
	if v, ok := data["escalation_contact"].(string); ok {
		s.EscalationContact = &v
	}
	return s
}

func parseFreshness(data map[string]interface{}) *Freshness {
	f := &Freshness{}
	if v, ok := data["last_loaded"].(string); ok {
		f.LastLoaded = &v
	}
	if v, ok := data["refresh_schedule"].(string); ok {
		f.RefreshSchedule = &v
	}
	if v, ok := data["source_system"].(string); ok {
		f.SourceSystem = &v
	}
	if deps, ok := data["upstream_dependencies"].([]interface{}); ok {
		for _, d := range deps {
			if s, ok := d.(string); ok {
				f.UpstreamDependencies = append(f.UpstreamDependencies, s)
			}
		}
	}
	return f
}

// stringFromMap safely extracts a string value from a map
func stringFromMap(m map[string]interface{}, key string) string {
	if v, ok := m[key]; ok {
		if s, ok := v.(string); ok {
			return s
		}
	}
	return ""
}
