variable "prefix" {
  description = "Short prefix for resource names"
  type        = string
  default     = "qbd"
}

variable "location" {
  description = "Azure region"
  type        = string
  default     = "francecentral"
}

variable "resource_group_name" {
  description = "Resource group name"
  type        = string
  default     = "rg-qbd-prod"
}

variable "storage_account_name" {
  description = "Storage account name (must be globally unique, 3-24 lower-case letters/numbers)"
  type        = string
  default     = "qbdstorprod001"
}

variable "key_vault_name" {
  description = "Key Vault name (3-24 alphanumeric)"
  type        = string
  default     = "kv-qbd-prod"
}

variable "app_insights_name" {
  type    = string
  default = "appi-qbd-prod"
}

variable "function_app_name" {
  type    = string
  default = "fa-qbd-prod"
}

variable "ig_container_name" {
  description = "Blob container to store generated carousels"
  type        = string
  default     = "carousels"
}

# IG + OpenAI secret names in Key Vault (you will set the secret values after creation)
variable "kv_secret_openai_api_key" {
  type    = string
  default = "openai-api-key"
}

variable "kv_secret_ig_user_id" {
  type    = string
  default = "ig-user-id"
}

variable "kv_secret_ig_access_token" {
  type    = string
  default = "ig-access-token"
}

variable "subscription_id" {
  type = string
}

variable "tenant_id" {
  type = string
}