#!/bin/bash
# Update .env file with values from Terraform outputs

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
INFRA_DIR="$PROJECT_ROOT/infrastructure/minimal"
ENV_FILE="$PROJECT_ROOT/.env"

echo "🔧 Updating .env file from Terraform outputs..."
echo ""

# Check if Terraform state exists
if [ ! -f "$INFRA_DIR/terraform.tfstate" ]; then
    echo "❌ Error: Terraform state file not found."
    echo "   Please run 'terraform apply' in infrastructure/minimal first."
    exit 1
fi

cd "$INFRA_DIR"

# Check if jq is installed
if ! command -v jq &> /dev/null; then
    echo "⚠️  jq is not installed. Installing via brew..."
    if command -v brew &> /dev/null; then
        brew install jq
    else
        echo "❌ Error: jq is required. Please install it manually: https://stedolan.github.io/jq/download/"
        exit 1
    fi
fi

echo "📋 Fetching Terraform outputs..."

# Get outputs as JSON
OUTPUTS_JSON=$(terraform output -json 2>/dev/null)

if [ -z "$OUTPUTS_JSON" ]; then
    echo "❌ Error: Could not get Terraform outputs"
    exit 1
fi

# Update .env file
echo "📝 Updating .env file..."

# Extract values and update .env
COGNITO_USER_POOL_ID=$(echo "$OUTPUTS_JSON" | jq -r '.cognito_user_pool_id.value // empty')
COGNITO_CLIENT_ID=$(echo "$OUTPUTS_JSON" | jq -r '.cognito_client_id.value // empty')
COGNITO_DOMAIN=$(echo "$OUTPUTS_JSON" | jq -r '.cognito_domain.value // empty')
TICKETS_TABLE=$(echo "$OUTPUTS_JSON" | jq -r '.tickets_table_name.value // empty')
KNOWLEDGE_BASE_BUCKET=$(echo "$OUTPUTS_JSON" | jq -r '.knowledge_base_bucket_name.value // empty')
VECTOR_BUCKET_NAME=$(echo "$OUTPUTS_JSON" | jq -r '.vector_bucket_name.value // empty')
GATEWAY_URL=$(echo "$OUTPUTS_JSON" | jq -r '.gateway_url.value // empty')

# Update or add values in .env
if [ -f "$ENV_FILE" ]; then
    # Remove old values if they exist
    sed -i.bak '/^COGNITO_USER_POOL_ID=/d' "$ENV_FILE"
    sed -i.bak '/^COGNITO_CLIENT_ID=/d' "$ENV_FILE"
    sed -i.bak '/^COGNITO_DOMAIN=/d' "$ENV_FILE"
    sed -i.bak '/^TICKETS_TABLE=/d' "$ENV_FILE"
    sed -i.bak '/^KNOWLEDGE_BASE_BUCKET=/d' "$ENV_FILE"
    sed -i.bak '/^VECTOR_BUCKET_NAME=/d' "$ENV_FILE"
    sed -i.bak '/^AGENTCORE_GATEWAY_URL=/d' "$ENV_FILE"
    rm -f "$ENV_FILE.bak"
fi

# Append new values
{
    echo ""
    echo "# Terraform outputs (auto-generated)"
    [ -n "$COGNITO_USER_POOL_ID" ] && echo "COGNITO_USER_POOL_ID=$COGNITO_USER_POOL_ID"
    [ -n "$COGNITO_CLIENT_ID" ] && echo "COGNITO_CLIENT_ID=$COGNITO_CLIENT_ID"
    [ -n "$COGNITO_DOMAIN" ] && echo "COGNITO_DOMAIN=$COGNITO_DOMAIN"
    [ -n "$TICKETS_TABLE" ] && echo "TICKETS_TABLE=$TICKETS_TABLE"
    [ -n "$KNOWLEDGE_BASE_BUCKET" ] && echo "KNOWLEDGE_BASE_BUCKET=$KNOWLEDGE_BASE_BUCKET"
    [ -n "$VECTOR_BUCKET_NAME" ] && echo "VECTOR_BUCKET_NAME=$VECTOR_BUCKET_NAME"
    [ -n "$GATEWAY_URL" ] && echo "AGENTCORE_GATEWAY_URL=$GATEWAY_URL"
} >> "$ENV_FILE"

echo "✅ .env file updated successfully!"
echo ""
echo "Updated values:"
[ -n "$COGNITO_USER_POOL_ID" ] && echo "  - COGNITO_USER_POOL_ID"
[ -n "$COGNITO_CLIENT_ID" ] && echo "  - COGNITO_CLIENT_ID"
[ -n "$TICKETS_TABLE" ] && echo "  - TICKETS_TABLE"
[ -n "$VECTOR_BUCKET_NAME" ] && echo "  - VECTOR_BUCKET_NAME"
[ -n "$GATEWAY_URL" ] && echo "  - AGENTCORE_GATEWAY_URL"

