package cache

import (
	"sync"
	"testing"
	"time"
)

// --- Get miss ---

func TestGetMiss(t *testing.T) {
	c := NewInMemory(5 * time.Second)
	val, found := c.Get("nonexistent")
	if found {
		t.Error("expected found=false for missing key")
	}
	if val != nil {
		t.Errorf("expected nil value, got %v", val)
	}
}

// --- Set + Get roundtrip ---

func TestSetAndGet(t *testing.T) {
	c := NewInMemory(5 * time.Second)
	c.Set("key1", "value1")

	val, found := c.Get("key1")
	if !found {
		t.Fatal("expected found=true")
	}
	if val != "value1" {
		t.Errorf("expected 'value1', got %v", val)
	}
}

func TestSetOverwrite(t *testing.T) {
	c := NewInMemory(5 * time.Second)
	c.Set("key", "v1")
	c.Set("key", "v2")

	val, found := c.Get("key")
	if !found {
		t.Fatal("expected found=true")
	}
	if val != "v2" {
		t.Errorf("expected 'v2', got %v", val)
	}
}

func TestSetDifferentTypes(t *testing.T) {
	c := NewInMemory(5 * time.Second)
	c.Set("int", 42)
	c.Set("slice", []string{"a", "b"})
	c.Set("map", map[string]int{"x": 1})

	val, _ := c.Get("int")
	if val.(int) != 42 {
		t.Errorf("expected 42, got %v", val)
	}

	val2, _ := c.Get("slice")
	slice := val2.([]string)
	if len(slice) != 2 {
		t.Errorf("expected slice of length 2, got %d", len(slice))
	}
}

// --- TTL expiry ---

func TestTTLExpiry(t *testing.T) {
	c := NewInMemory(50 * time.Millisecond)
	c.Set("key", "value")

	// Should be found immediately
	_, found := c.Get("key")
	if !found {
		t.Fatal("expected key to be found before TTL")
	}

	// Wait for TTL to expire
	time.Sleep(100 * time.Millisecond)

	_, found = c.Get("key")
	if found {
		t.Error("expected key to be expired after TTL")
	}
}

// --- Custom TTL per entry ---

func TestSetWithTTL(t *testing.T) {
	c := NewInMemory(5 * time.Second) // Default long TTL
	c.SetWithTTL("short", "value", 50*time.Millisecond)

	_, found := c.Get("short")
	if !found {
		t.Fatal("expected key to be found before custom TTL")
	}

	time.Sleep(100 * time.Millisecond)

	_, found = c.Get("short")
	if found {
		t.Error("expected key to expire with custom short TTL")
	}
}

func TestSetWithTTLDoesNotAffectDefaultTTL(t *testing.T) {
	c := NewInMemory(5 * time.Second)
	c.Set("default-ttl", "value")
	c.SetWithTTL("short-ttl", "value", 50*time.Millisecond)

	time.Sleep(100 * time.Millisecond)

	// short-ttl should have expired
	_, found := c.Get("short-ttl")
	if found {
		t.Error("expected short-ttl to be expired")
	}

	// default-ttl should still be valid
	_, found = c.Get("default-ttl")
	if !found {
		t.Error("expected default-ttl to still be present")
	}
}

// --- Delete ---

func TestDelete(t *testing.T) {
	c := NewInMemory(5 * time.Second)
	c.Set("key", "value")
	c.Delete("key")

	_, found := c.Get("key")
	if found {
		t.Error("expected key to be deleted")
	}
}

func TestDeleteNonExistent(t *testing.T) {
	c := NewInMemory(5 * time.Second)
	// Should not panic
	c.Delete("nonexistent")
}

// --- Clear ---

func TestClear(t *testing.T) {
	c := NewInMemory(5 * time.Second)
	c.Set("a", 1)
	c.Set("b", 2)
	c.Set("c", 3)

	c.Clear()

	if c.Size() != 0 {
		t.Errorf("expected size 0 after clear, got %d", c.Size())
	}
	_, found := c.Get("a")
	if found {
		t.Error("expected 'a' to be gone after clear")
	}
}

// --- Size ---

func TestSize(t *testing.T) {
	c := NewInMemory(5 * time.Second)
	if c.Size() != 0 {
		t.Errorf("expected size 0, got %d", c.Size())
	}

	c.Set("a", 1)
	c.Set("b", 2)
	if c.Size() != 2 {
		t.Errorf("expected size 2, got %d", c.Size())
	}

	c.Delete("a")
	if c.Size() != 1 {
		t.Errorf("expected size 1, got %d", c.Size())
	}
}

// --- Cleanup ---

func TestCleanup(t *testing.T) {
	c := NewInMemory(50 * time.Millisecond)
	c.Set("expire-soon", "value")
	c.SetWithTTL("stay", "value", 5*time.Second)

	time.Sleep(100 * time.Millisecond)

	// Before cleanup, size still includes expired entries (they are lazily removed on Get)
	// But Cleanup should remove them
	c.Cleanup()

	if c.Size() != 1 {
		t.Errorf("expected size 1 after cleanup, got %d", c.Size())
	}

	_, found := c.Get("stay")
	if !found {
		t.Error("expected 'stay' to still exist after cleanup")
	}
}

// --- Concurrent read/write safety ---

func TestConcurrentReadWrite(t *testing.T) {
	c := NewInMemory(5 * time.Second)
	var wg sync.WaitGroup

	// Writers
	for i := 0; i < 10; i++ {
		wg.Add(1)
		go func(id int) {
			defer wg.Done()
			for j := 0; j < 100; j++ {
				key := "key"
				c.Set(key, id*100+j)
			}
		}(i)
	}

	// Readers
	for i := 0; i < 10; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			for j := 0; j < 100; j++ {
				c.Get("key")
			}
		}()
	}

	// Deleters
	for i := 0; i < 5; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			for j := 0; j < 50; j++ {
				c.Delete("key")
			}
		}()
	}

	wg.Wait()
	// If we got here without panic or data race, the test passes
}

func TestConcurrentCleanup(t *testing.T) {
	c := NewInMemory(10 * time.Millisecond)
	var wg sync.WaitGroup

	// Writer goroutine
	wg.Add(1)
	go func() {
		defer wg.Done()
		for i := 0; i < 100; i++ {
			c.Set("key", i)
		}
	}()

	// Cleanup goroutine
	wg.Add(1)
	go func() {
		defer wg.Done()
		for i := 0; i < 50; i++ {
			c.Cleanup()
		}
	}()

	wg.Wait()
}
