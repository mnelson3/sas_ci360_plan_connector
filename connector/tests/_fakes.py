# coding=utf-8
"""Shared helper for stubbing out cloud SDKs the adapter tests don't need.

azure-identity, azure-keyvault-secrets, boto3, google-cloud-secret-manager,
azure-functions, functions-framework, and flask are all real dependencies
of the deployed functions, but nothing about testing this connector's
wiring needs the real SDKs on the network boundary - only that the module
names the adapter code imports resolve to something. Following the same
approach sol-identity's tests use for the private sasci360apicore
dependency: register fake modules directly in sys.modules.
"""

import sys
import types


def install_fake_module(dotted_name):
    """Ensure `dotted_name` (and every parent package it needs) resolves
    via sys.modules, without touching anything already registered there -
    so a real SDK, if ever installed, is never shadowed."""
    if dotted_name in sys.modules:
        return sys.modules[dotted_name]
    module = types.ModuleType(dotted_name)
    sys.modules[dotted_name] = module
    if "." in dotted_name:
        parent_name, attr = dotted_name.rsplit(".", 1)
        parent = install_fake_module(parent_name)
        setattr(parent, attr, module)
    return module
