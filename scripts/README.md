# Scripts

This directory contains utility scripts organized by purpose.

## Directory Structure

```
scripts/
├── setup/          # Setup and configuration scripts
├── deploy/          # Deployment and operations scripts
└── README.md        # This file
```

## Setup Scripts (`setup/`)

### `update_env.sh`
Updates `.env` file with values from Terraform outputs.

**Usage:**
```bash
./scripts/setup/update_env.sh
```

**Prerequisites:**
- Terraform infrastructure deployed
- `jq` installed (for JSON parsing)

**What it does:**
- Reads Terraform outputs
- Updates `.env` file with:
  - Cognito configuration
  - DynamoDB table names
  - S3 bucket names
  - Gateway URL

### Other Setup Scripts
- `update_env_from_terraform.sh` - Alternative env update script
- `update_env_complete.sh` - Complete env update with all values

## Deployment Scripts (`deploy/`)

### `deploy_agentcore.sh`
Deploys the AgentCore supervisor agent.

**Usage:**
```bash
./scripts/deploy/deploy_agentcore.sh
```

**Prerequisites:**
- Virtual environment activated
- AgentCore CLI installed
- `.bedrock_agentcore.yaml` configured
- AWS credentials configured

**What it does:**
- Checks AgentCore configuration
- Deploys supervisor agent to AgentCore Runtime
- Specialized agents run automatically in background threads (same container)
- Verifies deployment

### `start_dev.sh`
Start AgentCore in development mode for local testing.

**Usage:**
```bash
./scripts/deploy/start_dev.sh
```

**What it does:**
- Activates virtual environment
- Loads `.env` file
- Verifies AWS credentials
- Starts `agentcore dev` server

### `initialize_s3_vectors.py`
Initializes S3 Vector knowledge base and ingests sample articles.

**Usage:**
```bash
python scripts/deploy/initialize_s3_vectors.py
```

**Prerequisites:**
- Infrastructure deployed (S3 Vector bucket created)
- AWS credentials configured
- `.env` file configured with `VECTOR_BUCKET_NAME`

**What it does:**
- Creates S3 Vector indexes
- Ingests sample articles from `knowledge-base/sample-articles.json`
- Validates knowledge base setup

### `manage_knowledge_base.py`
Manage knowledge base articles (add, update, delete).

**Usage:**
```bash
python scripts/deploy/manage_knowledge_base.py
```

**Commands:**
- `add` - Add new article
- `update` - Update existing article
- `delete` - Delete article
- `list` - List all articles
- `search` - Search articles

## Setup Scripts (`setup/`)

### `setup_venv.sh`
Create and setup virtual environment (alternative to `setup.sh`).

**Usage:**
```bash
./scripts/setup/setup_venv.sh
```

**Note:** The main `setup.sh` script in the root directory is recommended for new developers.

## Quick Reference

**For new developers:**
1. Run `./setup.sh` (main setup)
2. Deploy infrastructure: `cd infrastructure/minimal && terraform apply`
3. Update env: `./scripts/setup/update_env.sh`
4. Initialize knowledge base: `python scripts/deploy/initialize_s3_vectors.py`
5. Deploy AgentCore: `./scripts/deploy/deploy_agentcore.sh`

**For testing:**
- See `tests/README.md` for test scripts

