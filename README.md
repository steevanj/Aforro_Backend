# Aforro Backend Developer Assignment

A production-oriented Django REST API implementation for the Aforro Backend Developer Round-2 assignment.

The project demonstrates:

* Django REST Framework APIViews
* PostgreSQL database
* Redis caching
* Celery asynchronous processing
* Transaction-safe order creation
* Inventory concurrency handling
* Query optimization
* Product search and autocomplete
* Pagination
* Database constraints
* Seed data generation
* Docker-based development
* Automated API tests

---

# 1. Project Overview

The application manages products, categories, stores, store-level inventory, and orders.

The main workflow is:

```text
Client
   |
   v
Django REST API
   |
   +--------------------+
   |                    |
   v                    v
PostgreSQL            Redis
   |                    |
   |                    +--> Inventory Cache
   |                    +--> Product Autocomplete Cache
   |
   +--> Products
   +--> Categories
   +--> Stores
   +--> Inventory
   +--> Orders
   +--> Order Items
   |
   v
Celery + Redis
   |
   +--> Asynchronous Order Confirmation
```

The most important business rule is safe inventory handling during order creation.

If all requested products have enough inventory:

```text
Order -> CONFIRMED
Stock -> Deducted
Celery -> Triggered
```

If any requested product has insufficient inventory:

```text
Order -> REJECTED
Stock -> Not Deducted
```

The entire operation is handled inside a database transaction.

---

# 2. Technology Stack

| Technology            | Purpose                            |
| --------------------- | ---------------------------------- |
| Python                | Backend programming language       |
| Django                | Web framework                      |
| Django REST Framework | REST API development               |
| PostgreSQL            | Primary relational database        |
| Redis                 | Caching and Celery broker          |
| Celery                | Asynchronous background processing |
| Docker                | Containerization                   |
| Faker                 | Dummy data generation              |
| Gunicorn              | Production WSGI server             |

---

# 3. Project Structure

```text
aforro_backend/
│
├── manage.py
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .env
├── .gitignore
├── README.md
│
├── config/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   ├── celery.py
│   ├── asgi.py
│   └── wsgi.py
│
├── products/
│   ├── migrations/
│   ├── admin.py
│   ├── apps.py
│   ├── models.py
│   └── serializers.py
│
├── stores/
│   ├── migrations/
│   ├── management/
│   │   └── commands/
│   │       └── seed_data.py
│   ├── admin.py
│   ├── apps.py
│   ├── cache.py
│   ├── models.py
│   ├── serializers.py
│   ├── urls.py
│   └── views.py
│
├── orders/
│   ├── migrations/
│   ├── admin.py
│   ├── apps.py
│   ├── models.py
│   ├── serializers.py
│   ├── tasks.py
│   ├── urls.py
│   ├── views.py
│   └── tests.py
│
└── search/
    ├── migrations/
    ├── apps.py
    ├── pagination.py
    ├── serializers.py
    ├── urls.py
    ├── views.py
    └── tests.py
```

---

# 4. Data Models

## Category

```text
Category
--------
id
name
```

Category names are unique.

---

## Product

```text
Product
-------
id
title
description
price
category
created_at
```

`created_at` was added because the search API requires a `newest` sorting option.

---

## Store

```text
Store
-----
id
name
location
```

---

## Inventory

```text
Inventory
---------
id
store
product
quantity
```

A database-level unique constraint is applied to:

```text
(store, product)
```

Therefore, a store cannot have multiple inventory rows for the same product.

---

## Order

```text
Order
-----
id
store
status
created_at
```

Possible statuses:

```text
PENDING
CONFIRMED
REJECTED
```

---

## OrderItem

```text
OrderItem
---------
id
order
product
quantity_requested
```

A unique constraint prevents the same product from appearing multiple times within the same order.

---

# 5. Prerequisites

For local development, install:

```text
Python 3.11+
PostgreSQL
Redis
Git
```

Alternatively, Docker can be used to run PostgreSQL and Redis.

---

# 6. Clone the Repository

```bash
git clone <your-github-repository-url>
cd aforro_backend
```

---

# 7. Create Virtual Environment

Windows:

```powershell
python -m venv venv
```

Activate it:

```powershell
.\venv\Scripts\activate
```

Linux/macOS:

```bash
python3 -m venv venv
source venv/bin/activate
```

---

# 8. Install Dependencies

```bash
pip install -r requirements.txt
```

Example `requirements.txt`:

```text
Django
djangorestframework
psycopg2-binary
django-redis
redis
celery
Faker
gunicorn
```

---

# 9. Environment Variables

Create a `.env` file in the project root.

Example:

```env
DEBUG=True

SECRET_KEY=your-secret-key

POSTGRES_DB=aforro
POSTGRES_USER=aforro
POSTGRES_PASSWORD=aforro
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

REDIS_HOST=localhost
REDIS_PORT=6379
```

For Docker, the database host should be:

```env
POSTGRES_HOST=db
```

and Redis:

```env
REDIS_HOST=redis
```

Do not commit real credentials or secret keys to GitHub.

---

# 10. Database Setup

Create the PostgreSQL database:

```sql
CREATE DATABASE aforro;
```

Then run:

```bash
python manage.py makemigrations
python manage.py migrate
```

---

# 11. Create Admin User

```bash
python manage.py createsuperuser
```

Start Django:

```bash
python manage.py runserver 8000
```

Admin panel:

```text
http://127.0.0.1:8000/admin/
```

---

# 12. Generate Dummy Data

The project provides a Django management command:

```bash
python manage.py seed_data
```

The command generates approximately:

```text
15+ categories
1200+ products
25+ stores
300 inventory products per store
7500+ inventory records
```

The seed operation uses:

```python
bulk_create()
```

to reduce database queries and improve data generation performance.

---

# 13. Running Redis Locally

Start Redis before using caching or Celery.

Default Redis address:

```text
localhost:6379
```

The application uses separate Redis databases:

```text
Redis DB 0 -> Celery
Redis DB 1 -> Django cache
```

---

# 14. Running Celery

Start the Django server:

```bash
python manage.py runserver 8000
```

In another terminal, activate the virtual environment and run:

```bash
celery -A config worker -l info
```

The Celery worker processes asynchronous tasks such as order confirmation.

---

# 15. Running with Docker

The project includes:

```text
Dockerfile
docker-compose.yml
```

The Docker environment contains:

```text
Django
PostgreSQL
Redis
Celery
```

Build and start everything:

```bash
docker compose up --build
```

The API will be available at:

```text
http://127.0.0.1:8000/
```

Run migrations:

```bash
docker compose exec web python manage.py migrate
```

Generate dummy data:

```bash
docker compose exec web python manage.py seed_data
```

Run tests:

```bash
docker compose exec web python manage.py test
```

Stop containers:

```bash
docker compose down
```

To remove database volumes as well:

```bash
docker compose down -v
```

---

# 16. API Endpoints

## 16.1 Create Order

```http
POST /orders/
```

### Request

```json
{
    "store_id": 1,
    "items": [
        {
            "product_id": 10,
            "quantity_requested": 2
        },
        {
            "product_id": 20,
            "quantity_requested": 1
        }
    ]
}
```

### Successful Response

```json
{
    "id": 1,
    "store": 1,
    "status": "CONFIRMED",
    "created_at": "2026-08-12T12:00:00Z",
    "items": [
        {
            "id": 1,
            "product": 10,
            "product_title": "Wireless Mouse",
            "quantity_requested": 2
        },
        {
            "id": 2,
            "product": 20,
            "product_title": "Keyboard",
            "quantity_requested": 1
        }
    ]
}
```

### Insufficient Stock Response

If any requested product does not have enough stock:

```json
{
    "id": 2,
    "store": 1,
    "status": "REJECTED",
    "created_at": "2026-08-12T12:05:00Z",
    "items": [
        {
            "id": 3,
            "product": 10,
            "product_title": "Wireless Mouse",
            "quantity_requested": 100
        }
    ]
}
```

Stock is not deducted when the order is rejected.

---

# 17. Order Creation Consistency

Order creation is wrapped in:

```python
transaction.atomic()
```

Inventory rows are locked using:

```python
select_for_update()
```

This prevents concurrent requests from consuming the same stock.

Example:

```text
Initial stock = 10

Request A -> 8
Request B -> 5
```

Without row locking, both requests could potentially see:

```text
stock = 10
```

With:

```python
select_for_update()
```

the database serializes access to the locked inventory row.

The second transaction waits until the first transaction completes before checking the updated stock.

---

# 18. List Store Orders

```http
GET /stores/<store_id>/orders/
```

Example:

```http
GET /stores/1/orders/
```

### Response

```json
[
    {
        "id": 10,
        "status": "CONFIRMED",
        "created_at": "2026-08-12T12:00:00Z",
        "total_items": 3
    },
    {
        "id": 9,
        "status": "REJECTED",
        "created_at": "2026-08-12T11:30:00Z",
        "total_items": 2
    }
]
```

Orders are sorted by newest first.

The item count is calculated using:

```python
annotate(
    total_items=Count("items")
)
```

This avoids executing a separate query for every order.

---

# 19. Store Inventory

```http
GET /stores/<store_id>/inventory/
```

Example:

```http
GET /stores/1/inventory/
```

### Response

```json
[
    {
        "id": 1,
        "product": 20,
        "product_title": "Keyboard",
        "price": "1999.00",
        "category_name": "Electronics",
        "quantity": 25
    },
    {
        "id": 2,
        "product": 10,
        "product_title": "Wireless Mouse",
        "price": "999.00",
        "category_name": "Electronics",
        "quantity": 40
    }
]
```

Results are sorted alphabetically by product title.

The query uses:

```python
select_related(
    "product",
    "product__category"
)
```

to avoid N+1 queries.

---

# 20. Inventory Redis Cache

The inventory API is cached using Redis.

Cache key:

```text
store_inventory:<store_id>
```

Example:

```text
store_inventory:1
```

Cache duration:

```text
5 minutes
```

If the cache exists:

```text
Request
   |
   v
Redis
   |
   v
Return cached result
```

If the cache does not exist:

```text
Request
   |
   v
PostgreSQL
   |
   v
Serialize
   |
   v
Redis
   |
   v
Response
```

---

# 21. Cache Invalidation

Inventory cache must not remain stale after an order changes stock.

After successful inventory deduction, the cache is invalidated using:

```python
transaction.on_commit()
```

This ensures cache invalidation only happens after the database transaction successfully commits.

Example:

```text
Order request
     |
     v
Transaction
     |
     +--> Deduct inventory
     |
     +--> Commit
             |
             v
       Delete Redis cache
```

If the transaction fails, the cache is not unnecessarily invalidated.

---

# 22. Product Search

```http
GET /api/search/products/
```

The search supports:

```text
q
category
min_price
max_price
store_id
in_stock
sort
page
page_size
```

---

# 23. Keyword Search

```http
GET /api/search/products/?q=phone
```

The keyword is searched across:

```text
Product title
Product description
Category name
```

The implementation uses Django `Q()` expressions.

Conceptually:

```python
Q(title__icontains=q)
|
Q(description__icontains=q)
|
Q(category__name__icontains=q)
```

---

# 24. Category Filter

```http
GET /api/search/products/?category=2
```

Filters products belonging to category ID 2.

---

# 25. Price Filters

Minimum price:

```http
GET /api/search/products/?min_price=1000
```

Maximum price:

```http
GET /api/search/products/?max_price=50000
```

Both:

```http
GET /api/search/products/?min_price=1000&max_price=50000
```

---

# 26. Store Filter

```http
GET /api/search/products/?store_id=1
```

When `store_id` is supplied, the response includes:

```text
inventory_quantity
```

for that store.

Example:

```json
{
    "id": 10,
    "title": "Wireless Mouse",
    "description": "Wireless mouse",
    "price": "999.00",
    "category": 2,
    "category_name": "Electronics",
    "created_at": "2026-08-12T10:00:00Z",
    "inventory_quantity": 25
}
```

Inventory quantity is retrieved using a database `Subquery` rather than making one query per product.

---

# 27. In-Stock Filter

Products that are in stock:

```http
GET /api/search/products/?store_id=1&in_stock=true
```

Products that are out of stock:

```http
GET /api/search/products/?store_id=1&in_stock=false
```

---

# 28. Product Sorting

## Price

```http
GET /api/search/products/?sort=price
```

Sorts products by lowest price first.

---

## Newest

```http
GET /api/search/products/?sort=newest
```

Sorts products by newest creation time.

---

## Relevance

```http
GET /api/search/products/?q=phone&sort=relevance
```

The current relevance logic prioritizes:

```text
Title prefix match
        ↓
Title contains match
        ↓
Description contains match
```

This provides simple relevance ranking without requiring a dedicated search engine.

---

# 29. Pagination

Default page size:

```text
20 products
```

Example:

```http
GET /api/search/products/?q=phone&page=2
```

Optional page size:

```http
GET /api/search/products/?q=phone&page=1&page_size=50
```

Maximum page size:

```text
100
```

Example response:

```json
{
    "count": 120,
    "next": "http://127.0.0.1:8000/api/search/products/?q=phone&page=2",
    "previous": null,
    "results": [
        {
            "id": 1,
            "title": "Phone Product",
            "description": "Example product",
            "price": "50000.00",
            "category": 2,
            "category_name": "Electronics",
            "created_at": "2026-08-12T10:00:00Z"
        }
    ]
}
```

---

# 30. Autocomplete API

```http
GET /api/search/suggest/?q=xxx
```

The minimum query length is 3 characters.

Example:

```http
GET /api/search/suggest/?q=iph
```

Response:

```json
{
    "results": [
        "iPhone Product 1",
        "iPhone Product 10",
        "Wireless iPhone Charger"
    ]
}
```

A maximum of 10 product titles is returned.

---

# 31. Autocomplete Ranking

Prefix matches are prioritized.

For:

```text
q=iph
```

A product such as:

```text
iPhone Case
```

is prioritized over:

```text
Wireless Charger for iPhone
```

The implementation uses conditional database ordering.

Autocomplete responses are cached in Redis.

Cache key:

```text
product_suggest:<query>
```

Example:

```text
product_suggest:iph
```

---

# 32. Celery Asynchronous Processing

Celery is configured with Redis as the message broker.

The current asynchronous task is:

```text
Order confirmation
```

After a successful order:

```text
POST /orders/
      |
      v
Transaction completes
      |
      v
transaction.on_commit()
      |
      v
Celery task
      |
      v
send_order_confirmation()
```

The task currently represents the notification step using a simple implementation.

In a production environment, it could be replaced with:

```text
Email
SMS
Webhook
Notification service
Message queue
```

---

# 33. Why `transaction.on_commit()`?

The Celery task is intentionally triggered after a successful database commit.

Without `on_commit()`:

```text
Create Order
    |
    v
Trigger Celery
    |
    v
Transaction fails
```

The Celery worker could process an order that was ultimately rolled back.

Using:

```python
transaction.on_commit(
    lambda: send_order_confirmation.delay(order.id)
)
```

ensures that the task is only queued after the database transaction succeeds.

---

# 34. Query Optimization

Several database optimization techniques are used.

## `select_related()`

Used for foreign-key relationships:

```python
.select_related(
    "product",
    "product__category"
)
```

Used by the inventory API.

---

## `prefetch_related()`

Used when retrieving order items:

```python
.prefetch_related(
    "items__product"
)
```

This avoids querying individual order items repeatedly.

---

## `annotate()`

Used for order item counts:

```python
.annotate(
    total_items=Count("items")
)
```

---

## `Subquery()`

Used to retrieve store-specific inventory quantity during product search.

This avoids:

```text
1 query per product
```

---

## `bulk_create()`

Used during seed data generation and order item creation.

This reduces database round trips.

---

## `bulk_update()`

Used to update multiple inventory rows after an order.

---

## `select_for_update()`

Used during order creation to lock inventory rows and prevent concurrent stock modifications.

---

# 35. Database Constraints

The database enforces important business rules.

Inventory:

```text
Unique(store, product)
```

This ensures one inventory row per store/product combination.

Order items:

```text
Unique(order, product)
```

This prevents duplicate product lines in an order.

These rules are enforced at the database level rather than relying only on application validation.

---

# 36. Error Handling

DRF validation handles invalid request data.

Examples include:

```text
Missing store_id
Missing items
Empty items
Quantity <= 0
Duplicate products
```

Example:

```json
{
    "items": [
        {
            "product_id": 10,
            "quantity_requested": 0
        }
    ]
}
```

Returns a validation error because requested quantities must be greater than zero.

---

# 37. Assumptions and Design Decisions

## Product `created_at`

The original Product requirements did not explicitly mention a creation timestamp, but the search API requires `newest` sorting.

Therefore:

```text
Product.created_at
```

was added.

This allows deterministic newest-first sorting.

---

## Rejected Orders

A rejected order is still stored in the database.

Reason:

The requirement explicitly states:

> If any product has insufficient stock, the order must be created with REJECTED status.

Therefore the order and its requested items are retained for historical/audit purposes.

---

## Rejected Order Inventory

No inventory is deducted when an order is rejected.

The stock validation is completed before modifying inventory.

---

## Transaction Boundary

The following operations are inside one `transaction.atomic()` block:

```text
Inventory locking
Stock validation
Order creation
Order item creation
Inventory deduction
Order status update
```

This ensures database consistency.

---

## Concurrency

Inventory rows are locked using:

```python
select_for_update()
```

This prevents race conditions when multiple users attempt to purchase the same stock simultaneously.

---

## Duplicate Products in an Order

Duplicate product IDs in the incoming request are rejected.

For example, this is invalid:

```json
{
    "items": [
        {
            "product_id": 10,
            "quantity_requested": 2
        },
        {
            "product_id": 10,
            "quantity_requested": 3
        }
    ]
}
```

Instead, the client should send:

```json
{
    "items": [
        {
            "product_id": 10,
            "quantity_requested": 5
        }
    ]
}
```

---

## Search Technology

The assignment allows either full-text search or multi-field `icontains`.

The implementation uses:

```text
title__icontains
description__icontains
category__name__icontains
```

This keeps the project simple and avoids unnecessary infrastructure.

For a very large product catalog, PostgreSQL full-text search with GIN indexes or Elasticsearch/OpenSearch would be a better choice.

---

## Redis Usage

Redis is used for caching:

```text
Store inventory
Product autocomplete
```

This reduces repeated database queries for frequently accessed data.

---

## Cache Invalidation

Inventory cache is invalidated after successful inventory modification.

The invalidation is registered with:

```python
transaction.on_commit()
```

so stale cache data is not removed due to a transaction that eventually rolls back.

---

## Celery

Celery is used for asynchronous order confirmation.

The task is triggered only after a successful order transaction.

---

# 38. Testing

The project includes API tests covering the main business logic.

Recommended test cases include:

```text
1. Successful order creation
2. Insufficient stock
3. Multiple products with one insufficient product
4. Duplicate product validation
5. Inventory API
6. Product search
7. Autocomplete
```

Run tests locally:

```bash
python manage.py test
```

With Docker:

```bash
docker compose exec web python manage.py test
```

---

# 39. Important Transaction Test

A critical test verifies atomic inventory behavior.

Example:

```text
Product A stock = 10
Product B stock = 2

Request:
Product A = 5
Product B = 5
```

Expected:

```text
Order = REJECTED

Product A = 10
Product B = 2
```

Even though Product A had sufficient stock, its inventory must not be deducted because Product B was unavailable.

This verifies the transaction requirement.

---

# 40. API Summary

| Method | Endpoint                        | Purpose                |
| ------ | ------------------------------- | ---------------------- |
| POST   | `/orders/`                      | Create an order        |
| GET    | `/stores/<store_id>/orders/`    | List store orders      |
| GET    | `/stores/<store_id>/inventory/` | List store inventory   |
| GET    | `/api/search/products/`         | Search/filter products |
| GET    | `/api/search/suggest/?q=xxx`    | Product autocomplete   |

---

# 41. Example Complete Workflow

## Step 1 — Start services

```bash
docker compose up --build
```

## Step 2 — Run migrations

```bash
docker compose exec web python manage.py migrate
```

## Step 3 — Generate data

```bash
docker compose exec web python manage.py seed_data
```

## Step 4 — Search products

```http
GET /api/search/products/?q=phone
```

## Step 5 — Check inventory

```http
GET /stores/1/inventory/
```

## Step 6 — Create order

```http
POST /orders/
```

with:

```json
{
    "store_id": 1,
    "items": [
        {
            "product_id": 10,
            "quantity_requested": 2
        }
    ]
}
```

## Step 7 — Check orders

```http
GET /stores/1/orders/
```

## Step 8 — Celery processes confirmation

The Celery worker receives the task after the order transaction commits.

---

# 42. Scalability Considerations

For larger production workloads, the following improvements could be introduced.

### Database

* PostgreSQL connection pooling
* Read replicas for read-heavy APIs
* Additional targeted indexes
* Database query monitoring
* Partitioning for very large order tables if required

### Search

The current implementation uses `icontains`.

For millions of products, consider:

```text
PostgreSQL Full-Text Search
        or
Elasticsearch/OpenSearch
```

with appropriate indexes.

### Caching

Redis can be scaled separately from Django.

Frequently requested data can be cached with appropriate TTLs and invalidation strategies.

### Background Processing

Celery workers can be scaled horizontally:

```text
Django
  |
  v
Redis
  |
  +--> Celery Worker 1
  +--> Celery Worker 2
  +--> Celery Worker 3
```

### API Scaling

Django API containers can be scaled horizontally behind a load balancer.

---

# 43. Future Improvements

Potential improvements include:

```text
Authentication and authorization
API rate limiting
Advanced PostgreSQL full-text search
Search ranking using SearchRank
Elasticsearch/OpenSearch
Order cancellation
Inventory reservation
Payment integration
Order status history
Structured logging
Monitoring
Health-check endpoints
API documentation using OpenAPI/Swagger
CI/CD pipeline
Production secret management
```

---

# 44. Engineering Trade-offs

The implementation intentionally avoids over-engineering.

For example:

```text
Simple search
instead of Elasticsearch
```

because the assignment accepts `icontains`.

```text
Redis cache
instead of a distributed search cache
```

because the dataset is relatively small.

```text
APIViews
instead of ViewSets
```

because explicit business logic is easier to understand for the order workflow.

```text
bulk_create/bulk_update
instead of individual database writes
```

because seed generation and inventory updates benefit significantly from fewer database round trips.

The goal is to keep the implementation clear while still addressing correctness, concurrency, performance, and scalability.

---

# 45. Final Architecture
c:\Users\steec\OneDrive\Pictures\Screenshots\Screenshot 2026-08-12 182418.png
# 46. Conclusion

This project demonstrates a complete backend module using Django REST Framework with a focus on:

```text
Correctness
Performance
Concurrency
Database consistency
Caching
Asynchronous processing
Scalability
Containerization
Testing
```

The most important engineering decisions are:

```text
transaction.atomic()
select_for_update()
select_related()
prefetch_related()
annotate()
Subquery()
bulk_create()
bulk_update()
Redis caching
transaction.on_commit()
Celery
PostgreSQL constraints
```

These choices ensure that the API is not only functional but also designed with real-world backend concerns in mind.
