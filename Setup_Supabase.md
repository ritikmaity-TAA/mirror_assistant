# Local Supabase Setup Guide
### Mirror Assistant Backend

---

## Prerequisites

- **Docker Desktop** installed and running
- **Node.js** (for npm-based CLI install, optional)
- **Python 3.14+** with a virtual environment

---

## 1. Install Supabase CLI

**macOS (Homebrew)**
```bash
brew install supabase/tap/supabase
```

**Windows (Scoop)**
```bash
scoop bucket add supabase https://github.com/supabase/scoop-bucket.git
scoop install supabase
```

**Cross-platform (npm)**
```bash
npm install -g supabase
```

Verify installation:
```bash
supabase --version
```

---

## 2. Initialize Supabase in Your Project

Navigate to the backend root and initialize:

```bash
cd mirror_assistant_backend
supabase init
```

This creates the following structure:

```
mirror_assistant_backend/
├── supabase/
│   ├── config.toml
│   └── migrations/
├── app/
└── ...
```

---

## 3. Start Local Supabase

```bash
supabase start
```

> First run pulls Docker images (~1–2 GB). This takes a few minutes.

On success, the terminal prints:

```
Started supabase local development setup.

Development Tools
  Studio     http://127.0.0.1:54323
  Mailpit    http://127.0.0.1:54324
  MCP        http://127.0.0.1:54321/mc

APIs
  Project URL     http://127.0.0.1:54321
  REST            http://127.0.0.1:54321/rest/v1
  GraphQL         http://127.0.0.1:54321/graphql/v1
  Edge Functions  http://127.0.0.1:54321/functions/v1

Database
  URL    postgresql://postgres:postgres@127.0.0.1:54322/postgres

Authentication Keys
  Publishable    sb_publishable_...
  Secret         sb_secret_...
```

---

## 4. Configure Your .env

Create a `.env` file in `mirror_assistant_backend/`:

```env
SUPABASE_URL=http://127.0.0.1:54321
SUPABASE_SERVICE_ROLE_KEY=sb_secret_...        # Secret key from supabase start output
APP_TIMEZONE=Asia/Kolkata
```

> **Key guide:**
> - `SUPABASE_URL` → Project URL under APIs
> - `SUPABASE_SERVICE_ROLE_KEY` → Secret under Authentication Keys
> - The **Publishable** key is for frontend (Next.js) only
> - The **Storage (S3)** section keys are not needed for this project

---

## 5. Create the Migration

```bash
supabase migration new create_core_tables
```

This creates: `supabase/migrations/<timestamp>_create_core_tables.sql`

Open that file and paste the following SQL:

```sql
-- 1. Create Professionals table
CREATE TABLE professionals (
    professional_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    full_name TEXT,
    email TEXT
);

-- 2. Create Clients table
CREATE TABLE clients (
    client_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    client_name TEXT NOT NULL
);

-- 3. Create Availability table
CREATE TABLE availability_slots (
    slot_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    professional_id UUID REFERENCES professionals(professional_id),
    date DATE NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    status TEXT DEFAULT 'available'
);

-- 4. Create Bookings table
CREATE TABLE bookings (
    booking_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    professional_id UUID REFERENCES professionals(professional_id),
    client_id UUID REFERENCES clients(client_id),
    slot_id UUID REFERENCES availability_slots(slot_id),
    date DATE NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    status TEXT DEFAULT 'scheduled'
);
```

---

## 6. Apply the Migration

```bash
supabase db reset
```

This re-creates the database and runs all migrations from scratch.

> **Note on Windows:** A `502` error at the end of `db reset` is expected — it's just the internal services restarting. As long as the migration line says `Applying migration ...` without a SQL error, it worked.

Verify in Studio at **http://127.0.0.1:54323** → Table Editor.  
You should see: `clients`, `availability_slots`, `bookings`.

---

## 7. Install Python Supabase Client

```bash
pip install supabase python-dotenv
```

---

## 8. Wire Up db/supabase.py

```python
# app/db/supabase.py

from supabase import create_client, Client
from dotenv import load_dotenv
import os

load_dotenv()

def get_supabase_client() -> Client:
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    return create_client(url, key)

supabase: Client = get_supabase_client()
```

---

## Troubleshooting

### Stale Docker containers (common on Windows)

If `supabase start` fails with a container name conflict:

```bash
# Remove a specific container
docker rm -f supabase_vector_mirror_assistant

# Or remove all stale containers for this project at once
docker ps -a --filter "label=com.supabase.cli.project=mirror_assistant" -q | ForEach-Object { docker rm -f $_ }
```

Then run `supabase start` again.

---

### Analytics warning on Windows

```
WARNING: Analytics on Windows requires Docker daemon exposed on tcp://localhost:2375.
```

This is non-blocking. Analytics is not required for this project. You can safely ignore it or disable analytics in `supabase/config.toml`:

```toml
[analytics]
enabled = false
```

---

### Check status and keys at any time

```bash
supabase status
```

---

## CLI Reference

| Command | Description |
|---|---|
| `supabase start` | Start local Supabase instance |
| `supabase stop` | Stop the instance (data preserved in Docker volume) |
| `supabase status` | Show all URLs and keys |
| `supabase db reset` | Drop and recreate DB, re-run all migrations |
| `supabase migration new <name>` | Create a new migration file |
| `supabase migration list` | List all migrations and their status |

---

## Data Model Summary

| Table | Primary Key | Key Relations |
|---|---|---|
| `clients` | `client_id` | — |
| `availability_slots` | `slot_id` | `professional_id` (external) |
| `bookings` | `booking_id` | `client_id → clients`, `slot_id → availability_slots` |

---

*Setup complete*