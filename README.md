# AWS Porter

AWS Porter is a CLI tool designed to port (clone) AWS resources from one account to another interactively. It handles resource discovery, dependency resolution, and basic verification.

## Features

- **Interactive Selection**: Choose exactly which resources to port.
- **Multiple Auth Methods**: Use AWS Profiles (from your `~/.aws/credentials`) or enter Access/Secret Keys interactively.
- **Dependency Tracking**: Automatically detects and offers to port dependent resources (e.g., ports a VPC when you select a Subnet).
- **Idempotency**: Detects existing resources by name/tags and offers to skip or overwrite.
- **Cross-Account/Cross-Region**: Supports porting between different AWS profiles and regions.
- **Account ID Mapping**: Automatically replaces source account IDs with target account IDs in IAM policies and Security Group rules.

## Supported Services

- **Networking**: VPC, Subnets, Security Groups, Route Tables, Internet Gateways.
- **Compute**: Lambda Functions (code + config + VpcConfig).
- **Storage**: S3 Buckets (configuration, tagging, versioning).
- **Identity**: IAM Roles and Policies.
- **Database**: DynamoDB (table schemas).
- **Messaging**: SQS Queues, SNS Topics.
- **API**: API Gateway (REST APIs via OpenAPI export/import).

## Quick Start

The easiest way to run AWS Porter is using the `run_porter.sh` script, which handles environment setup and dependencies.

```bash
chmod +x run_porter.sh
./run_porter.sh
```

### Authentication Methods

#### 1. AWS Profiles (Recommended)
An AWS Profile is a named set of credentials stored locally. If you have the AWS CLI installed, you can create one by running `aws configure --profile my-profile-name`.
Your profiles are stored in:
- Windows: `%USERPROFILE%\.aws\credentials`
- Linux/Mac: `~/.aws/credentials`

#### 2. Access Key / Secret Key
If you don't want to set up profiles, you can select option **2** in the script to paste your `Access Key ID` and `Secret Access Key` directly when prompted.

### Execution Steps
1. Run `./run_porter.sh`.
2. Choose your authentication method.
3. Provide the source and target account details.
4. The tool will "Discover" resources in the source account.
5. For each resource, you will be asked whether to port it.
6. If a resource depends on another (e.g., a Subnet needs a VPC), the tool will offer to port the dependency first.

### Manual Setup

If you prefer to run it manually:

1. Create a virtual environment: `python3 -m venv .venv && source .venv/bin/activate`
2. Install dependencies: `pip install -r requirements.txt`
3. Run the tool:
   ```bash
   python -m aws_porter.main port \
     --source-profile old-acc \
     --target-profile new-acc \
     --source-region us-east-1 \
     --target-region us-west-2
   ```

## Development

- **Handlers**: Each service is implemented as a handler in `aws_porter/handlers/`.
- **Engine**: The core logic for discovery and dependency resolution is in `aws_porter/core/engine.py`.
- **Tests**: Run tests using `pytest`.
