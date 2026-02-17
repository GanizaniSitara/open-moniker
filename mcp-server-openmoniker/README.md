# MCP Server for Open Moniker

An [MCP](https://modelcontextprotocol.io/) server that exposes the Open Moniker data catalog to AI coding assistants. Browse the catalog, resolve monikers, inspect ownership, search for data assets, and submit governance requests — all from your editor.

## Quick Start

```bash
# 1. Install dependencies (from repo root)
cd mcp-server-openmoniker
pip install -e .

# 2. Start the server
python server.py                          # default: localhost:8051
python server.py --port 9000              # custom port
python server.py --transport stdio        # stdio mode (for tools that prefer it)
```

The server prints a **write token** on startup. You only need this for write operations (submit/approve/reject requests). Read operations are anonymous.

### Environment Variables

| Variable | Default | Description |
|---|---|---|
| `MCP_PORT` | `8051` | Server port |
| `MCP_HOST` | `0.0.0.0` | Bind address |
| `MCP_WRITE_TOKEN` | *(auto-generated)* | Bearer token for write operations |
| `CATALOG_YAML` | `../sample_catalog.yaml` | Path to catalog definition |
| `DOMAINS_YAML` | `../sample_domains.yaml` | Path to domains definition |
| `MODELS_YAML` | `../sample_models.yaml` | Path to models definition |

---

## Adding to Your AI Tool

The server supports two transports:

- **Streamable HTTP** (default) — network-accessible at `http://localhost:8051/mcp`
- **stdio** — launched as a subprocess by the client

Choose the transport that your tool supports.

---

### Claude Code

Add to your project settings (`.claude/settings.json`) or user settings (`~/.claude/settings.json`):

```json
{
  "mcpServers": {
    "open-moniker": {
      "url": "http://localhost:8051/mcp"
    }
  }
}
```

Or using stdio transport:

```json
{
  "mcpServers": {
    "open-moniker": {
      "command": "python",
      "args": ["server.py", "--transport", "stdio"],
      "cwd": "/path/to/open-moniker/mcp-server-openmoniker"
    }
  }
}
```

Then restart Claude Code. The tools will appear automatically.

---

### Claude Desktop

Edit your Claude Desktop config file:

- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "open-moniker": {
      "command": "python",
      "args": ["server.py", "--transport", "stdio"],
      "cwd": "/path/to/open-moniker/mcp-server-openmoniker"
    }
  }
}
```

Restart Claude Desktop to pick up the new server.

---

### Cursor

Open **Settings → MCP** and add a new server:

**Option A — HTTP (recommended)**

| Field | Value |
|---|---|
| Type | `http` |
| URL | `http://localhost:8051/mcp` |

**Option B — stdio**

| Field | Value |
|---|---|
| Type | `command` |
| Command | `python /path/to/open-moniker/mcp-server-openmoniker/server.py --transport stdio` |

Or edit `.cursor/mcp.json` in your project root:

```json
{
  "mcpServers": {
    "open-moniker": {
      "url": "http://localhost:8051/mcp"
    }
  }
}
```

---

### Windsurf

Open **Settings → MCP** and add a server, or edit `~/.codeium/windsurf/mcp_config.json`:

```json
{
  "mcpServers": {
    "open-moniker": {
      "command": "python",
      "args": ["server.py", "--transport", "stdio"],
      "cwd": "/path/to/open-moniker/mcp-server-openmoniker"
    }
  }
}
```

---

### VS Code (Copilot)

Add to your workspace settings (`.vscode/settings.json`):

```json
{
  "mcp": {
    "servers": {
      "open-moniker": {
        "url": "http://localhost:8051/mcp"
      }
    }
  }
}
```

Or using stdio:

```json
{
  "mcp": {
    "servers": {
      "open-moniker": {
        "type": "stdio",
        "command": "python",
        "args": ["server.py", "--transport", "stdio"],
        "cwd": "/path/to/open-moniker/mcp-server-openmoniker"
      }
    }
  }
}
```

---

### OpenCode

Add to your OpenCode config (`opencode.json` or `~/.config/opencode/config.json`):

```json
{
  "mcpServers": {
    "open-moniker": {
      "url": "http://localhost:8051/mcp"
    }
  }
}
```

Or using stdio:

```json
{
  "mcpServers": {
    "open-moniker": {
      "command": "python",
      "args": ["server.py", "--transport", "stdio"],
      "cwd": "/path/to/open-moniker/mcp-server-openmoniker"
    }
  }
}
```

---

### Zed

Add to your Zed settings (`~/.config/zed/settings.json`):

```json
{
  "context_servers": {
    "open-moniker": {
      "command": {
        "path": "python",
        "args": ["server.py", "--transport", "stdio"],
        "env": {}
      },
      "settings": {}
    }
  }
}
```

---

### Any MCP-Compatible Tool

The server implements the standard MCP protocol. For any tool that supports MCP:

- **HTTP transport**: Point it at `http://localhost:8051/mcp`
- **stdio transport**: Run `python server.py --transport stdio`

---

## Available Tools

Once connected, your AI assistant gets these tools:

### Read Tools (no auth required)

| Tool | Description |
|---|---|
| `resolve_moniker` | Resolve a moniker path to source connection info (type, query, params) |
| `list_children` | List direct children of a catalog path |
| `describe_moniker` | Get full metadata: ownership, schema, data quality, documentation |
| `search_catalog` | Full-text search across paths, names, descriptions, and tags |
| `get_lineage` | Ownership lineage showing where each role is defined |
| `get_catalog_tree` | Browse the catalog as a nested tree |
| `get_catalog_stats` | Summary statistics (counts by status, source type) |
| `get_domains` | List all data domains with metadata |
| `get_models` | List all business models/measures |
| `get_model_detail` | Full details for a specific model (formula, ownership, appearances) |

### Write Tools (require `MCP_WRITE_TOKEN`)

| Tool | Description |
|---|---|
| `submit_request` | Submit a new moniker creation request for governance review |
| `list_requests` | List moniker requests, optionally filtered by status |
| `approve_request` | Approve a pending request and activate the moniker |
| `reject_request` | Reject a pending request |
| `update_node_status` | Change a catalog node's lifecycle status |

### Prompts (conversation templates)

| Prompt | Description |
|---|---|
| `explore_domain` | Walk through a data domain's monikers, ownership, and sources |
| `find_data` | Find data assets by keyword |
| `check_ownership` | Investigate ownership for a moniker or domain |

---

## Example Usage

Once the server is connected to your AI tool, you can ask things like:

- *"What data domains are available?"*
- *"Search the catalog for treasury data"*
- *"Who owns risk.cvar?"*
- *"Resolve the moniker for prices.equity/AAPL"*
- *"Show me the schema for fixed_income/govies/treasury"*
- *"What business models relate to risk analytics?"*
- *"Submit a request for a new moniker under prices"*
