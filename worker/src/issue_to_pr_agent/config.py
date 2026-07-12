"""Worker configuration, loaded from the environment the dispatcher injects."""

from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class WorkerConfig(BaseSettings):
    """Environment-driven config. Names match the dispatcher's worker-env keys."""

    model_config = SettingsConfigDict(env_prefix="", extra="ignore")

    github_installation_token: str = Field(default="", alias="GITHUB_INSTALLATION_TOKEN")
    job_id: str = Field(default="", alias="ITPR_JOB_ID")

    aws_endpoint_url: str = Field(default="http://localhost:4566", alias="AWS_ENDPOINT_URL")
    aws_region: str = Field(default="us-east-1", alias="AWS_REGION")
    s3_artifacts_bucket: str = Field(default="itpr-artifacts", alias="S3_ARTIFACTS_BUCKET")

    langfuse_host: str = Field(default="http://localhost:3000", alias="LANGFUSE_HOST")
    ollama_host: str = Field(default="http://localhost:11434", alias="OLLAMA_HOST")

    llm_provider_order: str = Field(default="mock", alias="LLM_PROVIDER_ORDER")

    openrouter_api_key: str | None = Field(default=None, alias="OPENROUTER_API_KEY")
    openrouter_model: str = Field(default="tencent/hy3:free", alias="OPENROUTER_MODEL")
    nvidia_nim_api_key: str | None = Field(default=None, alias="NVIDIA_NIM_API_KEY")
    nvidia_nim_model: str = Field(default="qwen/qwen3.5-122b-a10b", alias="NVIDIA_NIM_MODEL")
    gemini_api_key: str | None = Field(default=None, alias="GEMINI_API_KEY")
    groq_api_key: str | None = Field(default=None, alias="GROQ_API_KEY")

    @property
    def provider_order(self) -> list[str]:
        return [p.strip() for p in self.llm_provider_order.split(",") if p.strip()]
