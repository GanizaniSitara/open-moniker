# Management Landing Page — Card Layout Design

**Status:** Accepted
**Ticket:** OM-14
**Date:** 2026-03-27

## Overview

The management service landing page (`GET /`) displays a card grid that
links operators to each administration UI.  This document records what
cards exist, why they exist, and the rules for adding new ones.

## Current cards

| Card | Route | Purpose |
|------|-------|---------|
| **Domains** | `/domains/ui` | CRUD for data domains (ownership, confidentiality, PII flags) |
| **Catalog** | `/config/ui` | Edit monikers, source bindings, ownership |
| **Business Models** | `/models/ui` | Manage measures, metrics, and fields |
| **Applications** | `/docs#/Applications` | Register applications and map them to datasets/fields |
| **Review Queue** | `/requests/ui` | Approve/reject moniker requests |

A separate **API Documentation** section links to the Swagger UI at `/docs`.

## Design rules

### 1. One card per domain concept

Each card corresponds to a single top-level entity in the catalog
(domains, catalog nodes, models, applications, requests).  Do **not**
add a card that merely links to the same data from a different angle
(e.g. "Catalog Paths" duplicating "Catalog", or a raw API link for
data that already has a management UI).

### 2. No duplicate API-endpoint cards

Raw JSON endpoints (`/domains`, `/catalog`, `/tree`, etc.) are already
discoverable through Swagger UI.  Giving them their own cards on the
landing page is redundant and was removed in OM-14.

### 3. Cards must link to a management UI

Each admin card should link to an interactive HTML page (`/*/ui`) or,
if no UI exists yet, to the Swagger section for that resource.  Once a
proper UI is built, update the link.

### 4. Adding a new card — checklist

1. Confirm the new entity is a **first-class domain concept**, not a
   view over an existing one.
2. Ensure no existing card already covers the same data.
3. Add the card to the Administration grid in
   `management_app.py:root()`.
4. Update this document's table above.
5. If the entity has a full management UI, link to `/new-thing/ui`.
   Otherwise link to `/docs#/TagName` until one is built.

## History

- **OM-14 (2026-03-27):** Removed the duplicate "API Endpoints"
  4-card section (Catalog Tree, Domains, Models, Catalog Paths) that
  duplicated the Administration cards.  Added Applications card.  Wired
  the applications module into the management service.
