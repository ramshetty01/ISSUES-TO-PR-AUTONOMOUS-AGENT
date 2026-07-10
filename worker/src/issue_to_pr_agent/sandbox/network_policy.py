"""Egress policy for sandbox containers."""

from __future__ import annotations

from enum import Enum


class NetworkPolicy(str, Enum):
    NONE = "none"          # no network at all (default for untrusted execution)
    ALLOWLIST = "allowlist"  # a pre-created docker network with restricted egress
    BRIDGE = "bridge"      # full egress (build steps that fetch deps)


def to_network_args(policy: NetworkPolicy, allowlist_network: str = "itpr-egress") -> list[str]:
    """Translate a policy into `docker run --network` args."""
    if policy is NetworkPolicy.NONE:
        return ["--network", "none"]
    if policy is NetworkPolicy.ALLOWLIST:
        return ["--network", allowlist_network]
    return ["--network", "bridge"]


def blocks_egress(policy: NetworkPolicy) -> bool:
    return policy is NetworkPolicy.NONE
