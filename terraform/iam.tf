# IAM / Access Management

# IAM Users
resource "aws_iam_user" "users" {
  for_each = { for user in var.iam_users : user.username => user }

  name = each.value.username

  tags = each.value.tags
}

resource "aws_iam_user_login_profile" "login_profiles" {
  for_each = {
    for user in var.iam_users : user.username => user
    if user.console_access
  }

  user                    = aws_iam_user.users[each.key].name
  password_reset_required = each.value.force_password_reset
}


# IAM Groups
resource "aws_iam_group" "groups" {
  for_each = { for group in var.iam_groups : group.name => group }

  name = each.value.name
}

locals {
  group_policy_attachments = flatten([
    for group in var.iam_groups : [
      for policy_arn in group.attached_policies : {
        group_name = group.name
        policy_arn = policy_arn
      }
    ]
  ])
}

resource "aws_iam_group_policy_attachment" "group_policy_attachments" {
  for_each = {
    for attachment in local.group_policy_attachments : "${attachment.group_name}-${attachment.policy_arn}" => attachment
  }

  group      = aws_iam_group.groups[each.value.group_name].name
  policy_arn = each.value.policy_arn
}

resource "aws_iam_user_group_membership" "memberships" {
  for_each = {
    for user in var.iam_users : user.username => user
    if length(user.groups) > 0
  }

  user   = aws_iam_user.users[each.key].name
  groups = each.value.groups
}

