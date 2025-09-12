output "resource_group" {
  value = azurerm_resource_group.rg.name
}

output "function_app_default_hostname" {
  value = azurerm_function_app_flex_consumption.func.default_hostname
}