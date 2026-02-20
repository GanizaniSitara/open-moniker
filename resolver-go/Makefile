.PHONY: build test run clean docker-build help

# Go parameters
GOCMD=go
GOBUILD=$(GOCMD) build
GOTEST=$(GOCMD) test
GOCLEAN=$(GOCMD) clean
BINARY_NAME=resolver
BINARY_PATH=bin/$(BINARY_NAME)

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

build: ## Build the resolver binary
	$(GOBUILD) -o $(BINARY_PATH) -v ./cmd/resolver

build-linux: ## Build for Linux (useful for Docker)
	GOOS=linux GOARCH=amd64 $(GOBUILD) -o $(BINARY_PATH) -v ./cmd/resolver

test: ## Run tests
	$(GOTEST) -v ./...

test-coverage: ## Run tests with coverage
	$(GOTEST) -v -coverprofile=coverage.out ./...
	$(GOCMD) tool cover -html=coverage.out -o coverage.html

run: ## Run the resolver (with default config)
	$(GOBUILD) -o $(BINARY_PATH) -v ./cmd/resolver && \
	$(BINARY_PATH) --config ../config.yaml --port 8053

run-dev: ## Run with hot reload (requires air: go install github.com/cosmtrek/air@latest)
	air

clean: ## Remove build artifacts
	$(GOCLEAN)
	rm -f $(BINARY_PATH)
	rm -f coverage.out coverage.html

docker-build: ## Build Docker image
	docker build -f Dockerfile -t moniker-resolver-go:latest ..

docker-run: ## Run Docker container
	docker run -p 8053:8053 -v ../config.yaml:/app/config.yaml:ro \
		moniker-resolver-go:latest

fmt: ## Format code
	$(GOCMD) fmt ./...

lint: ## Run linter (requires golangci-lint)
	golangci-lint run

tidy: ## Tidy go modules
	$(GOCMD) mod tidy

install-tools: ## Install development tools
	$(GOCMD) install github.com/cosmtrek/air@latest
	$(GOCMD) install github.com/golangci/golangci-lint/cmd/golangci-lint@latest
