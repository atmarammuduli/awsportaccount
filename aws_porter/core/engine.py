from typing import List, Type
from aws_porter.handlers.base_handler import BaseHandler
from aws_porter.core.session_manager import SessionManager
from aws_porter.core.registry import MigrationRegistry
from rich.console import Console
from rich.prompt import Confirm, Prompt

console = Console()

class MigrationEngine:
    def __init__(self, session_manager: SessionManager):
        self.session_manager = session_manager
        self.registry = MigrationRegistry()
        self.handlers: List[BaseHandler] = []
        self._discovery_cache = {}

    def register_handler(self, handler_class: Type[BaseHandler]):
        handler = handler_class(self.session_manager, self.registry)
        self.handlers.append(handler)

    def run_interactive(self):
        console.print("[bold cyan]Discovery Phase[/bold cyan]")
        all_resources = []
        for handler in self.handlers:
            resources = self._discover_cached(handler)
            for res in resources:
                all_resources.append((handler, res))

        if not all_resources:
            console.print("No resources found to port.")
            return

        # Simple selection for now, can be improved
        for handler, res in all_resources:
            res_id = handler.get_id(res)
            res_name = handler.get_name(res)

            if Confirm.ask(f"Port {handler.resource_type} [bold]{res_name}[/bold] ({res_id})?"):
                self._port_with_dependencies(handler, res)

    def _discover_cached(self, handler: BaseHandler):
        key = (handler.service_name, handler.resource_type)
        if key not in self._discovery_cache:
            self._discovery_cache[key] = handler.discover()
        return self._discovery_cache[key]

    def _port_with_dependencies(self, handler: BaseHandler, resource: dict):
        res_id = handler.get_id(resource)

        if self.registry.has_resource(handler.service_name, handler.resource_type, res_id):
            return self.registry.get_target_id(handler.service_name, handler.resource_type, res_id)

        # Check dependencies
        deps = handler.get_dependencies(resource)
        for dep_service, dep_type, dep_id in deps:
            if not self.registry.has_resource(dep_service, dep_type, dep_id):
                # Self-reference check: if it's the same resource type and ID, we can't port it before itself
                if dep_service == handler.service_name and dep_type == handler.resource_type and dep_id == res_id:
                    continue

                console.print(f"  [yellow]Dependency found: {dep_type} ({dep_id})[/yellow]")
                dep_handler = next((h for h in self.handlers if h.service_name == dep_service and h.resource_type == dep_type), None)
                if dep_handler:
                    dep_resources = self._discover_cached(dep_handler)
                    dep_res = next((r for r in dep_resources if dep_handler.get_id(r) == dep_id), None)
                    if dep_res:
                        if Confirm.ask(f"  Port dependency {dep_type} [bold]{dep_handler.get_name(dep_res)}[/bold]?"):
                            self._port_with_dependencies(dep_handler, dep_res)
                    else:
                        console.print(f"  [red]Warning: Could not find configuration for dependency {dep_id}[/red]")

        # Port the resource
        try:
            target_id = handler.port(resource)
            if target_id and not target_id.startswith("SKIP:"):
                if handler.verify(target_id):
                    console.print(f"  [green]Successfully ported {handler.resource_type} to {target_id}[/green]")
                    self.registry.add_mapping(handler.service_name, handler.resource_type, res_id, target_id)
                    return target_id
                else:
                    console.print(f"  [red]Verification failed for {target_id}[/red]")
            else:
                console.print(f"  [yellow]Resource skipped or needs manual action: {target_id}[/yellow]")
        except Exception as e:
            console.print(f"  [red]Error porting {res_id}: {str(e)}[/red]")
            if Confirm.ask("  Would you like to retry?"):
                return self._port_with_dependencies(handler, resource)
