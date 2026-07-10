/** @itpr/config — typed, validated environment loading for all TS services. */
export { loadConfig, ConfigError, type EnvSource } from "./env.js";
export { configSchema, type Config } from "./schema.js";
export { DEV_DEFAULTS } from "./defaults.js";
