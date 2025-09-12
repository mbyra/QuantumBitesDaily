output "resource_group" {
  value = azurerm_resource_group.rg.name
}

output "function_app_default_hostname" {
  value = azurerm_linux_function_app.func.default_hostname
}