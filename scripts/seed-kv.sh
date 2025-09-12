#!/usr/bin/env bash
set -euo pipefail
KV_NAME=$(terraform -chdir=../infra output -raw key_vault_name)

az keyvault secret set --vault-name "$KV_NAME" --name "openai-api-key"   --value "${OPENAI_API_KEY:?missing}"
az keyvault secret set --vault-name "$KV_NAME" --name "ig-user-id"       --value "${IG_USER_ID:?missing}"
az keyvault secret set --vault-name "$KV_NAME" --name "ig-access-token"  --value "${IG_ACCESS_TOKEN:?missing}"
echo "Secrets seeded into $KV_NAME."