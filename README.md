# PowerShell Master Toolkit

An enterprise-ready, cross-platform interactive dashboard built with **Python** and **Streamlit**, designed to categorize, manage, audit, and quickly execute administrative PowerShell scripts.

The platform leverages an **Odoo-style hybrid data architecture**, allowing deployment either as a public cloud solution (powered by **Supabase PostgreSQL**) or as a completely private, offline, on-premises installation (powered by **SQLite**).

---

## 🚀 Key Features

### Dual Database Mode
Seamlessly switch between Cloud (**Supabase**) or Local (**SQLite**) storage engines using a single environment variable.

### 100% Data Ownership
Operate entirely offline using Docker Desktop while ensuring all application data remains securely stored on local infrastructure.

### Dynamic Indexing
Automated sequence management assigns structured numbering and strict ordering across all 22 technical categories.

### Secure Internet Exposure
Integrated Cloudflare Tunnel support enables secure external access without exposing firewall rules or public IP addresses.

### DevOps Automation
GitHub Actions automatically build and publish container images to GitHub Container Registry (GHCR).

---

## 📁 Repository Structure

```text
.
├── .github/
│   └── workflows/
│       └── docker-image.yml
│
├── services/
│   ├── auth.py
│   ├── repository.py
│   ├── repo_supabase.py
│   └── repo_sqlite.py
│
├── database/
│   └── ps_toolkit.db
│
├── app.py
├── Dockerfile
├── requirements.txt
└── README.md
```

### Components

| File | Description |
|--------|------------|
| `app.py` | Streamlit user interface |
| `auth.py` | Authentication and administrator security logic |
| `repository.py` | Data routing engine selecting SQLite or Supabase |
| `repo_sqlite.py` | Local database provider |
| `repo_supabase.py` | Cloud database provider |
| `Dockerfile` | Container image definition |
| `docker-image.yml` | GitHub Actions CI/CD workflow |

---

# 🛠️ Option 1: On-Premises Deployment (Docker Desktop)

Ideal for organizations requiring:

- Complete data privacy
- Offline operation
- Local database management
- Fast performance

## Prerequisites

Install:

- Docker Desktop for Windows
- Docker Desktop for macOS
- Docker Engine for Linux

---

## Create Deployment Folder

```text
powershell-toolkit/
├── docker-compose.yml
└── .env
```

---

## docker-compose.yml

```yaml
version: "3.8"

services:
  ps-toolkit:
    image: ghcr.io/thoubicimran/ps-toolkit:latest
    container_name: powershell_toolkit_app

    ports:
      - "8501:8501"

    environment:
      DATABASE_MODE: local
      PS_TOOLKIT_ADMIN_PASSWORD_HASH: ${PS_TOOLKIT_ADMIN_PASSWORD_HASH}

    volumes:
      - ./database:/app/database

    restart: unless-stopped
```

---

## .env

```env
# Administrator Password Hash
PS_TOOLKIT_ADMIN_PASSWORD_HASH=your_secure_pbkdf2_password_hash_here
```

---

## Start Application

Open PowerShell or Command Prompt:

```bash
docker compose up -d
```

---

## Access Application

Open:

```text
http://localhost:8501
```

or

```text
http://127.0.0.1:8501
```

---

## Initial Data Import

1. Open **Administration**
2. Authenticate using administrator credentials
3. Navigate to **Import / Export Utilities**
4. Upload your:

```text
ps_toolkit.json
```

5. Click:

```text
Import Commands
```

The system will automatically load all PowerShell commands into the SQLite database.

---

# 🌐 Option 2: Secure Internet Access Using Cloudflare Tunnel

Cloudflare Tunnel enables secure external access without:

- Port forwarding
- Exposing your public IP
- Firewall configuration changes

---

## Updated docker-compose.yml

```yaml
version: "3.8"

services:
  ps-toolkit:
    image: ghcr.io/thoubicimran/ps-toolkit:latest
    container_name: powershell_toolkit_app

    ports:
      - "8501:8501"

    environment:
      DATABASE_MODE: local
      PS_TOOLKIT_ADMIN_PASSWORD_HASH: ${PS_TOOLKIT_ADMIN_PASSWORD_HASH}

    volumes:
      - ./database:/app/database

    restart: unless-stopped

  tunnel:
    image: cloudflare/cloudflared:latest
    container_name: powershell_toolkit_tunnel

    restart: unless-stopped

    environment:
      TUNNEL_TOKEN: ${CLOUDFLARE_TUNNEL_TOKEN}

    command: tunnel --no-autoupdate run

    depends_on:
      - ps-toolkit
```

---

## .env

```env
PS_TOOLKIT_ADMIN_PASSWORD_HASH=your_secure_pbkdf2_password_hash_here

CLOUDFLARE_TUNNEL_TOKEN=your_cloudflare_tunnel_token
```

---

## Cloudflare Zero Trust Configuration

Configure your public hostname as follows:

| Setting | Value |
|----------|---------|
| Service Type | HTTP |
| Service URL | ps-toolkit:8501 |
| Protocol | HTTP |

This routes traffic securely to the internal Streamlit container.

---

# ☁️ Option 3: Cloud Deployment (Streamlit Cloud + Supabase)

This mode is intended for public cloud hosting.

The application stores operational data in Supabase PostgreSQL while serving the frontend from Streamlit Community Cloud.

---

## Streamlit Secrets Configuration

```toml
DATABASE_MODE = "cloud"

PS_TOOLKIT_ADMIN_PASSWORD_HASH = "your_admin_hash"

[supabase]
url = "https://your-project-id.supabase.co"
key = "your_service_role_key"
```

---

## Supabase Requirements

Create:

- Categories Table
- Commands Table
- Audit Logs Table
- User Management Table

Enable:

- SSL Connections
- Row-Level Security (RLS)
- Automated Backups

---

# 🔄 CI/CD Pipeline

The repository includes a GitHub Actions workflow located at:

```text
.github/workflows/docker-image.yml
```

Whenever changes are pushed to the `main` branch:

1. GitHub Actions starts automatically.
2. The repository name is normalized for Docker compatibility.
3. Build caching is enabled for fast image creation.
4. Docker image is built.
5. Image is pushed to:

```text
ghcr.io/thoubicimran/ps-toolkit:latest
```

---

## Updating Existing Deployments

To pull the latest version and redeploy:

```bash
docker compose pull && \
docker compose up -d && \
docker image prune -f
```

---

# 🔐 Security Recommendations

### Administrator Access

Use a strong PBKDF2 password hash:

```python
pbkdf2_sha256
```

Never store plain-text passwords.

---

### Cloud Deployments

Store all secrets using:

- Streamlit Secrets
- GitHub Secrets
- Cloudflare Secrets

Never commit credentials into source control.

---

### Database Protection

For production deployments:

- Enable encrypted backups
- Restrict database access
- Implement audit logging
- Enable role-based access control (RBAC)

---

# 📊 Supported Deployment Modes

| Deployment Type | Database | Internet Required | Data Ownership |
|---------------|----------|-------------------|----------------|
| Local Docker | SQLite | No | Full |
| Local + Cloudflare | SQLite | Yes | Full |
| Streamlit Cloud | Supabase | Yes | Shared Cloud |
| Enterprise Server | PostgreSQL | Optional | Full |

---

# ✅ Recommended Deployment Architecture

### Home Lab / Personal Use

```text
Docker Desktop
     │
     ▼
SQLite Database
     │
     ▼
Streamlit Application
```

### Enterprise Deployment

```text
Users
   │
   ▼
Cloudflare Zero Trust
   │
   ▼
Streamlit Application
   │
   ▼
Supabase PostgreSQL
   │
   ▼
Audit & Backup Services
```

---

## License

Copyright © 2026 Thoubic IMRAN

PowerShell Master Toolkit is intended for enterprise PowerShell management, automation governance, administrative auditing, and secure script cataloging.
