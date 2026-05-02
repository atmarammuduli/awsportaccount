import typer
from typing import Optional
from rich.console import Console

app = typer.Typer(help="AWS Porter: Clone AWS resources between accounts.")
console = Console()

@app.command()
def port(
    source_profile: Optional[str] = typer.Option(None, "--source-profile", help="AWS profile for the source account"),
    target_profile: Optional[str] = typer.Option(None, "--target-profile", help="AWS profile for the target account"),
    source_region: str = typer.Option("us-east-1", "--source-region", help="Source AWS region"),
    target_region: str = typer.Option(None, "--target-region", help="Target AWS region (defaults to source region)"),
    source_access_key: Optional[str] = typer.Option(None, envvar="SOURCE_AWS_ACCESS_KEY_ID"),
    source_secret_key: Optional[str] = typer.Option(None, envvar="SOURCE_AWS_SECRET_ACCESS_KEY"),
    target_access_key: Optional[str] = typer.Option(None, envvar="TARGET_AWS_ACCESS_KEY_ID"),
    target_secret_key: Optional[str] = typer.Option(None, envvar="TARGET_AWS_SECRET_ACCESS_KEY"),
):
    """
    Interactively port AWS resources from source to target account.
    """
    if target_region is None:
        target_region = source_region

    console.print(f"[bold green]Starting AWS Porter[/bold green]")
    from aws_porter.core.logger import setup_logging
    logger = setup_logging()
    logger.info("Starting AWS Porter")

    from aws_porter.core.session_manager import SessionManager
    from aws_porter.core.engine import MigrationEngine
    from aws_porter.handlers.vpc_handler import VPCHandler
    from aws_porter.handlers.subnet_handler import SubnetHandler
    from aws_porter.handlers.security_group_handler import SecurityGroupHandler
    from aws_porter.handlers.iam_handler import IAMRoleHandler
    from aws_porter.handlers.s3_handler import S3Handler
    from aws_porter.handlers.lambda_handler import LambdaHandler
    from aws_porter.handlers.dynamodb_handler import DynamoDBHandler
    from aws_porter.handlers.apigateway_handler import APIGatewayHandler
    from aws_porter.handlers.sqs_handler import SQSHandler
    from aws_porter.handlers.sns_handler import SNSHandler
    from aws_porter.handlers.eventbridge_handler import EventBridgeHandler
    from aws_porter.handlers.nat_gateway_handler import NATGatewayHandler
    from aws_porter.handlers.efs_handler import EFSHandler
    from aws_porter.handlers.rds_handler import RDSHandler
    from aws_porter.handlers.launch_template_handler import LaunchTemplateHandler
    from aws_porter.handlers.db_subnet_group_handler import DBSubnetGroupHandler

    session_mgr = SessionManager(
        source_profile=source_profile,
        target_profile=target_profile,
        source_region=source_region,
        target_region=target_region,
        source_access_key=source_access_key,
        source_secret_key=source_secret_key,
        target_access_key=target_access_key,
        target_secret_key=target_secret_key
    )
    engine = MigrationEngine(session_mgr)

    # Register handlers in dependency order (mostly)
    engine.register_handler(VPCHandler)
    engine.register_handler(SubnetHandler)
    engine.register_handler(SecurityGroupHandler)
    engine.register_handler(IAMRoleHandler)
    engine.register_handler(S3Handler)
    engine.register_handler(SQSHandler)
    engine.register_handler(SNSHandler)
    engine.register_handler(DynamoDBHandler)
    engine.register_handler(LambdaHandler)
    engine.register_handler(APIGatewayHandler)
    engine.register_handler(EventBridgeHandler)
    engine.register_handler(NATGatewayHandler)
    engine.register_handler(EFSHandler)
    engine.register_handler(DBSubnetGroupHandler)
    engine.register_handler(RDSHandler)
    engine.register_handler(LaunchTemplateHandler)

    try:
        engine.run_interactive()
    except Exception as e:
        console.print(f"[bold red]Migration Error:[/bold red] {str(e)}")

if __name__ == "__main__":
    app()
