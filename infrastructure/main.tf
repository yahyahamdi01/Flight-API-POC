terraform {
  backend "s3" {
    bucket = "flight-ops-terraform-state-242"
    key    = "state/terraform.tfstate"
    region = "eu-west-3"
  }
}

provider "aws" {
  region = "eu-west-3"
}

variable "public_key" {
  type        = string
  description = "Public key for the EC2 instance"
}

# latest Ubuntu
data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"]

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
  }
}

#  SECURITY GROUP
resource "aws_security_group" "ops_sg" {
  name        = "flight_ops_sg"
  description = "Inbound traffic for Flight Ops POC"

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 5000
    to_port     = 5000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 9090
    to_port     = 9090
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 3000
    to_port     = 3000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# SSH 
resource "aws_key_pair" "ops_auth" {
  key_name   = "ops-key"
  public_key = var.public_key
}

# EC2
resource "aws_instance" "ops_server" {
  ami                    = data.aws_ami.ubuntu.id
  instance_type          = "t3.micro"
  vpc_security_group_ids = [aws_security_group.ops_sg.id]
  key_name               = aws_key_pair.ops_auth.key_name

  tags = {
    Name = "Flight-Ops-Server"
  }
}


output "server_public_ip" {
  value = aws_instance.ops_server.public_ip
}