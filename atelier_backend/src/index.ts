import { Container, getContainer } from "@cloudflare/containers";

export class AtelierApi extends Container {
  defaultPort = 8000;
  requiredPorts = [8000];
  sleepAfter = "15m";
  enableInternet = true;
  pingEndpoint = "/health";
}

interface Env {
  ATELIER_API: DurableObjectNamespace;
  DATABASE_URL: string;
  JWT_SECRET: string;
  GROQ_API_KEY: string;
  GROQ_MODEL: string;
  GEMINI_API_KEY: string;
  GEMINI_MODEL: string;
  LANGFUSE_PUBLIC_KEY: string;
  LANGFUSE_SECRET_KEY: string;
  LANGFUSE_HOST: string;
  CORS_ORIGINS: string;
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const container = getContainer(env.ATELIER_API, "main");
    await container.startAndWaitForPorts({
      ports: [8000],
      startOptions: {
        envVars: {
          ENVIRONMENT: "production",
          LLM_PROVIDER: "live",
          SEED_DEMO_USERS: "true",
          ALLOW_SELF_ASSIGN_ROLE: "true",
          DATABASE_URL: env.DATABASE_URL,
          JWT_SECRET: env.JWT_SECRET,
          GROQ_API_KEY: env.GROQ_API_KEY,
          GROQ_MODEL: env.GROQ_MODEL || "qwen/qwen3.6-27b",
          GEMINI_API_KEY: env.GEMINI_API_KEY,
          GEMINI_MODEL: env.GEMINI_MODEL || "gemini-3.6-flash",
          LANGFUSE_PUBLIC_KEY: env.LANGFUSE_PUBLIC_KEY,
          LANGFUSE_SECRET_KEY: env.LANGFUSE_SECRET_KEY,
          LANGFUSE_HOST: env.LANGFUSE_HOST || "https://cloud.langfuse.com",
          CORS_ORIGINS: env.CORS_ORIGINS || "",
        },
      },
      cancellationOptions: {
        instanceGetTimeoutMS: 30_000,
        portReadyTimeoutMS: 90_000,
      },
    });
    return container.fetch(request);
  },
};
