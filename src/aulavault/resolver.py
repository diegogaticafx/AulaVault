from .models import Module, ResolvedModule
from .session import MoodleSession
from .resolvers import resource, url_module, assign, label

RESOLVERS = {
    "resource": resource.resolve,
    "url": url_module.resolve,
    "assign": assign.resolve,
    "label": label.resolve,
}


def resolve_module(session: MoodleSession, module: Module) -> ResolvedModule:
    resolver = RESOLVERS.get(module.type)
    if resolver:
        return resolver(session, module)
    return ResolvedModule(module=module)
