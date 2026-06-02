terraform {
  required_version = ">= 1.6"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }
}

provider "aws" {
  region = "us-east-1"
  default_tags {
    tags = {
      Project     = "infra-dev"
      Environment = "dev"
      ManagedBy   = "TerraPilot"
    }
  }
}

resource "random_id" "suffix" {
  byte_length = 4
}
