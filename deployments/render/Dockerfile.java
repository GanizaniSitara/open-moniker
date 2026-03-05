# Multi-stage build for Java resolver
FROM maven:3.9-eclipse-temurin-21-alpine AS builder

WORKDIR /build

# Copy resolver source
COPY resolver-java /build/resolver-java
COPY sample_config.yaml /build/
COPY sample_catalog.yaml /build/

# Build JAR
WORKDIR /build/resolver-java
RUN mvn clean package -DskipTests

# Runtime stage
FROM eclipse-temurin:21-jre-alpine

WORKDIR /app

# Copy JAR and config files
COPY --from=builder /build/resolver-java/target/resolver-java-*.jar /app/resolver.jar
COPY --from=builder /build/sample_config.yaml /app/
COPY --from=builder /build/sample_catalog.yaml /app/

# Expose port
EXPOSE 8054

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=60s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost:8054/health || exit 1

# Start resolver
CMD ["java", \
     "-Dserver.port=8054", \
     "-Dmoniker.config-file=/app/sample_config.yaml", \
     "-Dmoniker.telemetry.enabled=true", \
     "-jar", "/app/resolver.jar"]
