package telemetry

import (
	"github.com/ganizanisitara/open-moniker/resolver-go/internal/config"
)

// Emitter is the interface for telemetry emission
type Emitter interface {
	Stop()
	GetStats() (emitted, dropped, errors, queueDepth int64)
}

// noOpEmitter is a no-op implementation of Emitter
type noOpEmitter struct{}

func (e *noOpEmitter) Stop() {}

func (e *noOpEmitter) GetStats() (emitted, dropped, errors, queueDepth int64) {
	return 0, 0, 0, 0
}

// NewNoOpEmitter returns a no-op emitter that discards all events
func NewNoOpEmitter() Emitter {
	return &noOpEmitter{}
}

// NewFromConfig creates an emitter from telemetry config.
// Returns a no-op emitter if telemetry is disabled or config is nil.
func NewFromConfig(cfg *config.TelemetryConfig) (Emitter, error) {
	if cfg == nil || !cfg.Enabled {
		return NewNoOpEmitter(), nil
	}
	// Telemetry sinks not yet implemented — return no-op
	return NewNoOpEmitter(), nil
}
