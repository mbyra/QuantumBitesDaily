# QuantumBitesDaily – Azure Functions + Terraform

Daily Instagram carousel generator posting physics & space facts at **09:00 Paris time** (see DST note).

## What you get
- **Terraform** infra (RG, Storage + private container `carousels`, Key Vault with references, Linux Function App Flex Consumption, CORS for Portal/localhost, MSI + roles).
- **Functions (Python)**: timer (07:00 UTC) + HTTP manual trigger.
- **Pipeline**: OpenAI text + images → render slides → store in Blob → Instagram carousel publish.

## Deploy
```bash
cd infra
terraform init
terraform apply -auto-approve
```

Set secrets (names are configurable in `variables.tf`):
```bash
KV_NAME=$(terraform output -raw key_vault_name)
az keyvault secret set --vault-name "$KV_NAME" --name "openai-api-key" --value "<OPENAI>"
az keyvault secret set --vault-name "$KV_NAME" --name "ig-user-id" --value "<IG_USER_ID>"
az keyvault secret set --vault-name "$KV_NAME" --name "ig-access-token" --value "<IG_LONG_LIVED_TOKEN>"
```

Publish Functions:
```bash
cd ../function_app
func azure functionapp publish $(terraform -chdir=../infra output -raw function_app_name) --python
```

## Manual run
`POST https://<app>.azurewebsites.net/api/HttpRunNow?code=<FUNCTION_KEY>` with optional `{ "topic": "gravitational waves" }`.

## DST note
Timer schedules on Linux run in UTC. `0 0 7 * * *` = 07:00 UTC (≈ 09:00 Paris in summer, 08:00 in winter). For strict 09:00 Paris, use Logic Apps to call `HttpRunNow` in `Europe/Paris` timezone.

## CORS
Portal + localhost are whitelisted.




TODO:
* seed kv automatically while creating the infra 