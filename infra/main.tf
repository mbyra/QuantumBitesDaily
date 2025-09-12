locals {
  tags = {
    project = "QuantumBitesDaily"
    owner   = "Clouditect"
    env     = "prod"
  }
}

resource "azurerm_resource_group" "rg" {
  name     = var.resource_group_name
  location = var.location
  tags     = local.tags
}

resource "azurerm_storage_account" "sa" {
  name                     = var.storage_account_name
  resource_group_name      = azurerm_resource_group.rg.name
  location                 = azurerm_resource_group.rg.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
  min_tls_version          = "TLS1_2"
  tags                     = local.tags
}

# Carousels container
resource "azurerm_storage_container" "carousels" {
  name                  = var.ig_container_name
  storage_account_id    = azurerm_storage_account.sa.id
  container_access_type = "private"
}

# Deployments container (for Flex deployment package)
resource "azurerm_storage_container" "deployments" {
  name                  = "deploymentpackage"
  storage_account_id    = azurerm_storage_account.sa.id
  container_access_type = "private"
}

resource "azurerm_application_insights" "appi" {
  name                = var.app_insights_name
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
  application_type    = "web"
  tags                = local.tags
}

resource "azurerm_key_vault" "kv" {
  name                       = var.key_vault_name
  location                   = azurerm_resource_group.rg.location
  resource_group_name        = azurerm_resource_group.rg.name
  tenant_id                  = data.azurerm_client_config.current.tenant_id
  sku_name                   = "standard"
  purge_protection_enabled   = true
  soft_delete_retention_days = 7
  tags                       = local.tags
}

data "azurerm_client_config" "current" {}

# Allow your current AAD user to manage secrets for initial setup
resource "azurerm_key_vault_access_policy" "you" {
  key_vault_id = azurerm_key_vault.kv.id
  tenant_id    = data.azurerm_client_config.current.tenant_id
  object_id    = data.azurerm_client_config.current.object_id

  secret_permissions = ["Get", "List", "Set", "Delete", "Purge", "Recover"]
}

# Function App (Flex Consumption - Linux)
resource "azurerm_service_plan" "plan" {
  name                = "${var.prefix}-plan-flex"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
  os_type             = "Linux"
  sku_name            = "FC1" # Flex Consumption
  tags                = local.tags
}

resource "azurerm_function_app_flex_consumption" "func" {
  name                = var.function_app_name
  resource_group_name = azurerm_resource_group.rg.name
  location            = azurerm_resource_group.rg.location
  service_plan_id     = azurerm_service_plan.plan.id

  # Flex deployment storage (required)
  storage_container_type      = "blobContainer"
  storage_container_endpoint  = "${azurerm_storage_account.sa.primary_blob_endpoint}${azurerm_storage_container.deployments.name}"
  storage_authentication_type = "StorageAccountConnectionString"
  storage_access_key          = azurerm_storage_account.sa.primary_access_key

  # Flex runtime (this replaces FUNCTIONS_WORKER_RUNTIME)
  runtime_name    = "python"
  runtime_version = "3.12"

  site_config {
    cors {
      allowed_origins = [
        "https://portal.azure.com",
        "https://ms.portal.azure.com",
        "http://localhost:7071",
        "http://127.0.0.1:7071"
      ]
      support_credentials = false
    }
  }

  identity { type = "SystemAssigned" }

  app_settings = {
    # ❌ DO NOT include FUNCTIONS_WORKER_RUNTIME in Flex
    # ❌ Prefer to omit WEBSITE_RUN_FROM_PACKAGE on Flex

    AzureWebJobsFeatureFlags = "EnableWorkerIndexing"

    # Key Vault references
    OPENAI_API_KEY  = "@Microsoft.KeyVault(VaultName=${azurerm_key_vault.kv.name};SecretName=${var.kv_secret_openai_api_key})"
    IG_USER_ID      = "@Microsoft.KeyVault(VaultName=${azurerm_key_vault.kv.name};SecretName=${var.kv_secret_ig_user_id})"
    IG_ACCESS_TOKEN = "@Microsoft.KeyVault(VaultName=${azurerm_key_vault.kv.name};SecretName=${var.kv_secret_ig_access_token})"

    QBD_STORAGE_ACCOUNT    = azurerm_storage_account.sa.name
    QBD_CAROUSEL_CONTAINER = azurerm_storage_container.carousels.name
  }
}

# Grant Function identity access to Key Vault secret resolution
resource "azurerm_key_vault_access_policy" "func_kv" {
  key_vault_id = azurerm_key_vault.kv.id
  tenant_id    = data.azurerm_client_config.current.tenant_id
  object_id    = azurerm_function_app_flex_consumption.func.identity[0].principal_id

  secret_permissions = ["Get", "List"]
}

# Grant Function identity permissions on Storage for blob operations
resource "azurerm_role_assignment" "func_storage_role" {
  scope                = azurerm_storage_account.sa.id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = azurerm_function_app_flex_consumption.func.identity[0].principal_id
}

output "function_app_name" {
  value = azurerm_function_app_flex_consumption.func.name
}

output "key_vault_name" {
  value = azurerm_key_vault.kv.name
}

output "storage_account_name" {
  value = azurerm_storage_account.sa.name
}