variable "project_name" {
  description = "Name of the project"
  type        = string
  default     = "infra-dev"
}

variable "environment" {
  description = "Deployment environment"
  type        = string
  default     = "dev"
}

variable "region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "public_subnet_cidrs" {
  description = "CIDR blocks for public subnets"
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24"]
}

variable "private_subnet_cidrs" {
  description = "CIDR blocks for private subnets"
  type        = list(string)
  default     = ["10.0.3.0/24", "10.0.4.0/24"]
}

variable "key_pair_mode" {
  description = "EC2 key pair mode: none, existing, or create"
  type        = string
  default     = "existing"

  validation {
    condition     = contains(["none", "existing", "create"], var.key_pair_mode)
    error_message = "key_pair_mode must be one of: none, existing, create."
  }
}

variable "existing_key_pair_name" {
  description = "Existing EC2 key pair name"
  type        = string
  default     = "my-key"
}

variable "key_pair_name" {
  description = "New EC2 key pair name"
  type        = string
  default     = "my-key"
}

variable "public_key" {
  description = "Public SSH key content for creating a new EC2 key pair"
  type        = string
  default     = ""
  sensitive   = true
}

variable "ecr_enabled" {
  description = "Whether ECR is enabled"
  type        = bool
  default     = true
}

variable "ecr_repository_mode" {
  description = "How to configure ECR repository: create or existing"
  type        = string
  default     = "create"

  validation {
    condition     = contains(["create", "existing"], var.ecr_repository_mode)
    error_message = "ecr_repository_mode must be create or existing."
  }
}

variable "ecr_repository_name" {
  description = "ECR repository name"
  type        = string
  default     = "infra-dev/backend-api"
}

variable "ecr_image_tag_mutability" {
  description = "ECR image tag mutability"
  type        = string
  default     = "IMMUTABLE"
}

variable "ecr_scan_on_push" {
  description = "Enable image scan on push"
  type        = bool
  default     = true
}

variable "ec2_instances" {
  description = "List of EC2 instance configurations"
  type = list(object({
    name                = string
    instance_type       = string
    quantity            = number
    subnet_type         = string
    associate_public_ip = bool
    root_volume_size    = number
    root_volume_type    = string
    encrypt_root_volume = bool
  }))
  default = [
    {
      "name" : "wmaster-server",
      "instance_type" : "t3.small",
      "quantity" : 1,
      "subnet_type" : "public",
      "associate_public_ip" : true,
      "root_volume_size" : 8,
      "root_volume_type" : "gp3",
      "encrypt_root_volume" : false
    },
    {
      "name" : "web-server",
      "instance_type" : "t3.micro",
      "quantity" : 1,
      "subnet_type" : "public",
      "associate_public_ip" : true,
      "root_volume_size" : 8,
      "root_volume_type" : "gp3",
      "encrypt_root_volume" : false
    }
  ]
}

variable "iam_users" {
  description = "IAM users to create"
  type = list(object({
    username             = string
    console_access       = bool
    programmatic_access  = bool
    force_password_reset = bool
    mfa_recommended      = bool
    groups               = list(string)
    attached_policies    = list(string)
    tags                 = map(string)
  }))
  default = [
    {
      "username" : "infra-dev-dev-ci-cd-1",
      "console_access" : true,
      "programmatic_access" : true,
      "force_password_reset" : true,
      "mfa_recommended" : true,
      "groups" : [],
      "attached_policies" : [],
      "tags" : {}
    }
  ]
}

variable "iam_groups" {
  description = "IAM groups to create"
  type = list(object({
    name              = string
    description       = optional(string)
    attached_policies = list(string)
    users             = list(string)
  }))
  default = [
    {
      "name" : "infra-dev-dev-group",
      "description" : "",
      "attached_policies" : [],
      "users" : []
    }
  ]
}

variable "iam_roles" {
  description = "IAM roles to create"
  type = list(object({
    name              = string
    type              = string
    trusted_entity    = string
    attached_policies = list(string)
    inline_policies   = list(string)
    tags              = map(string)
  }))
  default = []
}
