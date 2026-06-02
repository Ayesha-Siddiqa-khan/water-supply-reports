output "project_name" {
  description = "The name of the project"
  value       = var.project_name
}

output "environment" {
  description = "The deployment environment"
  value       = var.environment
}

output "region" {
  description = "The AWS region"
  value       = var.region
}

output "ec2_key_pair_name" {
  description = "EC2 key pair name used by instances"
  value       = local.ec2_key_name
}

output "ecr_repository_url" {
  description = "ECR repository URL"
  value       = local.ecr_repository_url
}

output "ecr_repository_arn" {
  description = "ECR repository ARN"
  value       = local.ecr_repository_arn
}
