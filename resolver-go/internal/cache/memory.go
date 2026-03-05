package cache

import (
	"sync"
	"time"
)

// Entry represents a cached entry with expiration
type Entry struct {
	Value     interface{}
	ExpiresAt time.Time
}

// InMemory is a simple thread-safe in-memory cache
type InMemory struct {
	entries map[string]*Entry
	mu      sync.RWMutex
	ttl     time.Duration
}

// NewInMemory creates a new in-memory cache
func NewInMemory(ttl time.Duration) *InMemory {
	return &InMemory{
		entries: make(map[string]*Entry),
		ttl:     ttl,
	}
}

// Get retrieves a value from the cache
func (c *InMemory) Get(key string) (interface{}, bool) {
	c.mu.RLock()
	defer c.mu.RUnlock()

	entry, ok := c.entries[key]
	if !ok {
		return nil, false
	}

	// Check expiration
	if time.Now().After(entry.ExpiresAt) {
		return nil, false
	}

	return entry.Value, true
}

// Set stores a value in the cache
func (c *InMemory) Set(key string, value interface{}) {
	c.mu.Lock()
	defer c.mu.Unlock()

	c.entries[key] = &Entry{
		Value:     value,
		ExpiresAt: time.Now().Add(c.ttl),
	}
}

// SetWithTTL stores a value with a custom TTL
func (c *InMemory) SetWithTTL(key string, value interface{}, ttl time.Duration) {
	c.mu.Lock()
	defer c.mu.Unlock()

	c.entries[key] = &Entry{
		Value:     value,
		ExpiresAt: time.Now().Add(ttl),
	}
}

// Delete removes a value from the cache
func (c *InMemory) Delete(key string) {
	c.mu.Lock()
	defer c.mu.Unlock()

	delete(c.entries, key)
}

// Clear clears all entries
func (c *InMemory) Clear() {
	c.mu.Lock()
	defer c.mu.Unlock()

	c.entries = make(map[string]*Entry)
}

// Size returns the number of entries in the cache
func (c *InMemory) Size() int {
	c.mu.RLock()
	defer c.mu.RUnlock()

	return len(c.entries)
}

// Cleanup removes expired entries
func (c *InMemory) Cleanup() {
	c.mu.Lock()
	defer c.mu.Unlock()

	now := time.Now()
	for key, entry := range c.entries {
		if now.After(entry.ExpiresAt) {
			delete(c.entries, key)
		}
	}
}

// StartCleanup starts a background goroutine that periodically cleans up expired entries
func (c *InMemory) StartCleanup(interval time.Duration) {
	go func() {
		ticker := time.NewTicker(interval)
		defer ticker.Stop()

		for range ticker.C {
			c.Cleanup()
		}
	}()
}
