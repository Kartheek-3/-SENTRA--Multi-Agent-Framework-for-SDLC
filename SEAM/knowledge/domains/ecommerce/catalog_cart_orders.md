---
title: Ecommerce Catalog Cart And Orders
category: domain
domain: ecommerce
topic: catalog_cart_orders
source: SEAM curated/validated knowledge repository
version: 1.0
status: VALIDATED
created_at: 2026-09-19
updated_at: 2026-09-19
---

# Ecommerce Catalog Cart And Orders

Description: Domain guidance for shopping applications with product catalogs, carts, and orders.

Principles:
- Product catalog, cart, order, payment, and inventory are separate concepts.
- Cart contents are provisional; orders are durable business records.
- Order totals should be calculated server-side from trusted price and tax data.

Recommended practices:
- Store product SKU, display name, active status, and current price separately from order line snapshots.
- Copy price and product label onto order items at purchase time.
- Track order states such as pending, paid, fulfilled, cancelled, and refunded.
- Make cart updates idempotent where possible.

Common mistakes:
- Using the cart as the final order record.
- Trusting client-submitted prices.
- Losing order history when product catalog details change.

Applicable project types: online stores, retail checkout apps, marketplace prototypes.

Relevant technologies: React, FastAPI, SQL databases, REST APIs.
