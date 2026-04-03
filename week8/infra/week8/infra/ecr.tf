resource "aws_ecr_repository" "my_repo" {
    for_each = local.ecs_services_map
    name = each.value.ecr_repository
}

