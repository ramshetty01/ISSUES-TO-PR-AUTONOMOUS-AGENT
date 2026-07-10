/** Liveness endpoint. */
import { Router } from "express";

export function healthRouter(): Router {
  const router = Router();
  router.get("/health", (_req, res) => {
    res.status(200).json({ status: "ok", uptime: process.uptime() });
  });
  return router;
}
