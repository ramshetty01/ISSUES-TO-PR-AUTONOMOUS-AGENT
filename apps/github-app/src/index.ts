/** github-app entrypoint: load config, start the server, wire smee forwarding. */
import { loadAppConfig } from "./config.js";
import { createServer } from "./server.js";
import { startSmee } from "./smee-client.js";
import { logger } from "./logging/logger.js";

function main(): void {
  const config = loadAppConfig();
  const app = createServer();

  const server = app.listen(config.port, () => {
    logger.info("github-app listening", { port: config.port });
    startSmee(config.smeeUrl, `http://localhost:${config.port}/webhook`);
  });

  const shutdown = (signal: string) => {
    logger.info("shutting down", { signal });
    server.close(() => process.exit(0));
  };
  process.on("SIGINT", () => shutdown("SIGINT"));
  process.on("SIGTERM", () => shutdown("SIGTERM"));
}

main();
