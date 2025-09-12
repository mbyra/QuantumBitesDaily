resource "azurerm_key_vault_secret" "openai" {
  count        = var.openai_api_key == "" ? 0 : 1
  name         = var.kv_secret_openai_api_key
  value        = var.openai_api_key
  key_vault_id = azurerm_key_vault.kv.id
  content_type = "OpenAI API Key"
  depends_on   = [azurerm_key_vault_access_policy.you]
}

resource "azurerm_key_vault_secret" "ig_user_id" {
  count        = var.ig_user_id == "" ? 0 : 1
  name         = var.kv_secret_ig_user_id
  value        = var.ig_user_id
  key_vault_id = azurerm_key_vault.kv.id
  content_type = "IG User ID"
  depends_on   = [azurerm_key_vault_access_policy.you]
}

resource "azurerm_key_vault_secret" "ig_token" {
  count        = var.ig_access_token == "" ? 0 : 1
  name         = var.kv_secret_ig_access_token
  value        = var.ig_access_token
  key_vault_id = azurerm_key_vault.kv.id
  content_type = "IG Access Token"
  depends_on   = [azurerm_key_vault_access_policy.you]
}