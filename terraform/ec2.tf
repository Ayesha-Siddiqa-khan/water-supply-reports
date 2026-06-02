# EC2 Instances (Multiple)

data "aws_key_pair" "existing" {
  key_name = var.existing_key_pair_name
}

locals {
  ec2_key_name = data.aws_key_pair.existing.key_name
}

locals {
  ec2_instance_base_names = [for item in var.ec2_instances : item.name]
  ec2_duplicate_names = toset([
    for name in local.ec2_instance_base_names : name
    if length([for candidate in local.ec2_instance_base_names : candidate if candidate == name]) > 1
  ])

  ec2_instances_expanded = {
    for inst in flatten([
      for item_index, item in var.ec2_instances : [
        for idx in range(item.quantity) : {
          key                 = contains(local.ec2_duplicate_names, item.name) ? "${item.name}-${item_index + 1}-${idx + 1}" : "${item.name}-${idx + 1}"
          name                = contains(local.ec2_duplicate_names, item.name) ? "${item.name}-${item_index + 1}-${idx + 1}" : "${item.name}-${idx + 1}"
          instance_type       = item.instance_type
          subnet_type         = item.subnet_type
          associate_public_ip = item.associate_public_ip
          root_volume_size    = item.root_volume_size
          root_volume_type    = item.root_volume_type
          encrypt_root_volume = item.encrypt_root_volume
        }
      ]
    ]) : inst.key => inst
  }
}

resource "aws_instance" "main" {
  for_each = local.ec2_instances_expanded

  ami           = data.aws_ssm_parameter.ami.value
  instance_type = each.value.instance_type

  subnet_id = each.value.subnet_type == "public" ? aws_subnet.public[0].id : aws_subnet.private[0].id

  associate_public_ip_address = each.value.associate_public_ip
  key_name                    = local.ec2_key_name
  root_block_device {
    volume_size           = each.value.root_volume_size
    volume_type           = each.value.root_volume_type
    encrypted             = each.value.encrypt_root_volume
    delete_on_termination = true
  }

  tags = {
    Name = each.value.name
  }
}
