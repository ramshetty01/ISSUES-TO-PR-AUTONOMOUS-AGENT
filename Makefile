# ---------------------------------------------------------------------------
# issue-to-pr-agent — local dev orchestration.
# One command to boot the $0 stack (LocalStack + Langfuse + app services),
# seed the queues, run the smoke eval, and build the worker image.
# ---------------------------------------------------------------------------

COMPOSE ?= docker compose
LOCALSTACK_SVC ?= localstack

.PHONY: up down seed eval worker-image logs ps help

help: ## Show available targets
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  %-14s %s\n", $$1, $$2}'

up: ## Boot the full local stack (detached)
	$(COMPOSE) up -d

down: ## Tear down the full local stack (keep volumes)
	$(COMPOSE) down

seed: ## (Re)provision LocalStack resources and enqueue a sample job
	$(COMPOSE) exec -T $(LOCALSTACK_SVC) sh < infra/local/localstack-init.sh
	$(COMPOSE) exec -T $(LOCALSTACK_SVC) sh < infra/local/seed-local-queues.sh

eval: ## Run the internal smoke eval against the mock provider
	python3 eval/runners/run_internal_eval.py --provider mock --subset smoke

worker-image: ## Build the sandboxed worker container image
	scripts/build-worker-image.sh

logs: ## Tail logs from all services
	$(COMPOSE) logs -f

ps: ## Show status of all services
	$(COMPOSE) ps
