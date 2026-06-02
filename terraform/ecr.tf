# ECR

resource "aws_ecr_repository" "main" {
  name                 = var.ecr_repository_name
  image_tag_mutability = var.ecr_image_tag_mutability

  image_scanning_configuration {
    scan_on_push = var.ecr_scan_on_push
  }

  tags = {
    Name = "infra-dev/backend-api"
  }
}

locals {
  ecr_repository_url = aws_ecr_repository.main.repository_url
  ecr_repository_arn = aws_ecr_repository.main.arn
}
