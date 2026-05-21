// Variables for the AWS AMI build.
// Change these without touching the main template.

variable "region" {
  type        = string
  default     = "us-east-1"
  description = "AWS region to build in."
}

variable "instance_type" {
  type        = string
  default     = "t3.micro"
  description = "EC2 instance type used for the temporary build instance."
}

variable "ami_prefix" {
  type        = string
  default     = "nginx-baked"
  description = "Prefix used in the resulting AMI name. A timestamp is appended automatically."
}
