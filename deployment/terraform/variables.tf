# Terraform variables

variable "db_password" {
  description = "PostgreSQL database password"
  type        = string
  sensitive   = true
}

# Add other sensitive variables as needed

