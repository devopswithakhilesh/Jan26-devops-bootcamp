resource "aws_ecs_cluster" "main" {
    name = "${var.prefix}-${var.app_name}-cluster"
}

resource "aws_ecs_task_definition" "service" {
  for_each = local.ecs_services_map
  family                   = "${var.prefix}-${var.app_name}-${each.key}-task"
  execution_role_arn       = aws_iam_role.ecs_task_execution.arn
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = each.value.cpu
  memory                   = each.value.memory
  container_definitions = jsonencode([
    {
      name      = var.app_name
      image     = ""
      cpu       = each.value.cpu
      memory    = each.value.memory
      essential = true
      portMappings = [
        {
          containerPort = each.value.port
          hostPort      = each.value.port
        }
      ]
      environment = [
        { "name" : "Owner", "value" : "Akhilesh" },
        { "name" : "DB_LINK", "value" : "postgresql://${aws_db_instance.postgres.username}:${random_password.password.result}@${aws_db_instance.postgres.address}:5432/${aws_db_instance.postgres.db_name}" }
      ]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-create-group  = "false"
          awslogs-group         = aws_cloudwatch_log_group.ecs_logs[each.key].name
          awslogs-region        = "ap-south-1"
          awslogs-stream-prefix = "ecs"
        }
      }
    }
  ])
}