"""Resource + isolation limits for sandbox containers."""

from __future__ import annotations

from dataclasses import dataclass, field

from .network_policy import NetworkPolicy, to_network_args


@dataclass(slots=True)
class SandboxLimits:
    memory: str = "2g"
    cpus: str = "2"
    pids_limit: int = 512
    network: NetworkPolicy = NetworkPolicy.NONE
    readonly_rootfs: bool = True
    cap_drop: list[str] = field(default_factory=lambda: ["ALL"])
    security_opt: list[str] = field(default_factory=lambda: ["no-new-privileges"])
    tmpfs: list[str] = field(default_factory=lambda: ["/tmp"])

    def to_docker_args(self) -> list[str]:
        args = [
            "--memory", self.memory,
            "--cpus", self.cpus,
            "--pids-limit", str(self.pids_limit),
            *to_network_args(self.network),
        ]
        if self.readonly_rootfs:
            args.append("--read-only")
        for c in self.cap_drop:
            args += ["--cap-drop", c]
        for s in self.security_opt:
            args += ["--security-opt", s]
        for t in self.tmpfs:
            args += ["--tmpfs", t]
        return args
