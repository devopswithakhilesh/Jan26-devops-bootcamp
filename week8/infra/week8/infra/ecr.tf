resource "aws_ecr_repository" "my_repo" {
  for_each = local.ecs_services_map
  name     = each.value.ecr_repository
}


# 879381241087.dkr.ecr.ap-south-1.amazonaws.com/devopsdozo-backend
# 879381241087.dkr.ecr.ap-south-1.amazonaws.com/devopsdozo-frontend

# docker build  -t 879381241087.dkr.ecr.ap-south-1.amazonaws.com/devopsdozo-backend:latest  --platform linux/amd64  .
# docker build -t 879381241087.dkr.ecr.ap-south-1.amazonaws.com/devopsdozo-frontend:latest  --platform linux/amd64 .


# ecr login
# aws ecr get-login-password --region ap-south-1 | docker login --username AWS --password-stdin 879381241087.dkr.ecr.ap-south-1.amazonaws.com 