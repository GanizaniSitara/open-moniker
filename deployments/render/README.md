# Render.com Deployment

Complete deployment setup for Render.com with automated scripts.

## Quick Deploy

```bash
cd deployments/render
python3 deploy.py
```

This will automatically:
1. Create PostgreSQL database
2. Create Python admin service
3. Create Java resolver service
4. Configure all environment variables
5. Trigger deployments

## Services

### Python Admin (Port 8050)
- **URL**: `https://moniker-admin-[random].onrender.com`
- **Endpoints**: `/health`, `/resolve/*`, `/catalog`, `/docs`
- **Features**: Admin UI, resolution, dashboard, telemetry

### Java Resolver (Port 8054)
- **URL**: `https://moniker-resolver-java-[random].onrender.com`
- **Endpoints**: `/health`, `/resolve/*`, `/catalog`, `/list/*`
- **Features**: High-performance resolution, telemetry

### PostgreSQL Database
- **Name**: `moniker-telemetry`
- **Plan**: Starter (256MB)
- **Purpose**: Shared telemetry storage

## Testing

Once services are deployed and healthy:

```bash
python3 test_render.py \
  https://moniker-admin-xyz.onrender.com \
  https://moniker-resolver-java-xyz.onrender.com
```

This runs 10 comprehensive tests including:
- Health checks
- Parent node resolution
- Leaf node resolution
- Catalog endpoints
- Load testing (50 requests)

## Manual Deployment

If you prefer using Render dashboard:

1. Create PostgreSQL database manually
2. Create Python service from GitHub repo
3. Create Java service with Docker runtime
4. Set environment variables as shown in `render.yaml`

## Cost Estimate

- Python service: $7/month (Starter)
- Java service: $7/month (Starter)
- PostgreSQL: $7/month (Starter, 256MB)
- **Total**: $21/month

## Monitoring

- Dashboard: https://dashboard.render.com/
- Python logs: View in Render dashboard → moniker-admin → Logs
- Java logs: View in Render dashboard → moniker-resolver-java → Logs
- Database: Connect via connection string in dashboard

## Troubleshooting

### Service won't start
- Check build logs in Render dashboard
- Verify environment variables are set
- Check that sample_config.yaml and sample_catalog.yaml exist in repo

### Health check failing
- Services need 2-3 minutes to start
- Java service takes longer (Maven build)
- Check logs for errors

### Database connection issues
- Ensure database is created first
- Verify environment variables reference correct database
- Check IP allowlist is empty (allow all)

## Files

- `render.yaml` - Infrastructure as code blueprint
- `Dockerfile.java` - Java service container
- `deploy.py` - Automated deployment script
- `test_render.py` - Comprehensive test suite
- `README.md` - This file
