# 1. THE PROVIDER: Tells Terraform we are using AWS and the Paris region
provider "aws" {
  region = "eu-west-3"
}

# 2. THE DATA BLOCK: A Pro-SRE move. Instead of hardcoding an OS version,
# we tell Terraform to dynamically search AWS for the absolute latest Ubuntu 22.04 image.
data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"] # Canonical's official AWS account ID

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
  }
}

# 3. THE SECURITY GROUP: This is our Firewall. 
# We start with a "Deny All" approach and only open what we explicitly need.
resource "aws_security_group" "amadeus_sg" {
  name        = "amadeus_flight_sg"
  description = "Allow inbound traffic for Amadeus POC"

  # Open Port 22 so we can SSH into the server later
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Open Port 5000 for our Flight App
  ingress {
    from_port   = 5000
    to_port     = 5000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Open Port 8000 for our Prometheus Metrics
  ingress {
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Allow the server to access the internet (to download Docker later)
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1" # "-1" means all protocols
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# THE SSH KEY: Uploads our public key to AWS so we can log in
resource "aws_key_pair" "amadeus_auth" {
  key_name   = "amadeus-key"
  public_key = file("~/.ssh/amadeus_key.pub")
}

# 4. THE EC2 INSTANCE: The actual Virtual Server
resource "aws_instance" "amadeus_server" {
  ami                    = data.aws_ami.ubuntu.id
  instance_type          = "t3.micro" # 100% Free Tier Eligible!
  vpc_security_group_ids = [aws_security_group.amadeus_sg.id]
  
  key_name               = aws_key_pair.amadeus_auth.key_name

  tags = {
    Name = "Amadeus-POC-Server"
  }
}

# 5. THE OUTPUT: Tells Terraform to print the public IP address 
# to our terminal when it finishes, so we know where to connect!
output "server_public_ip" {
  value = aws_instance.amadeus_server.public_ip
}