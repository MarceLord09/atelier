# Atelier — Content Suite

Plataforma de consistencia de marca para el **reto técnico Alicorp IAGen**.

Un brief se convierte en DNA indexado. El motor creativo consulta ese manual antes de escribir. Dos aprobadores cierran el expediente: texto en Mesa, imagen en Visión. Langfuse deja rastro de retrieval, prompt y latencia.

Repo: [github.com/MarceLord09/atelier](https://github.com/MarceLord09/atelier)

## Mapa del reto

| Módulo del PDF | En Atelier | Quién |
|---|---|---|
| I · Brand DNA + RAG | `/dna` · chunks en pgvector | Creador |
| II · Creative Engine | `/prensa` · ficha, guion, prompt de imagen | Creador |
| III · Gobernanza | `/mesa` Pendiente → Aprobado / Rechazado | Aprobador A |
| III · Auditoría multimodal | `/vision` · Gemini contra el mismo DNA | Aprobador B |
| IV · Observabilidad | Langfuse: `brand.compose`, `creative.generate`, `governance.audit` | — |

Stack pedido: FastAPI + Next.js + GitHub + Supabase + Groq (texto) + Gemini (visión) + Langfuse.

## Demo en 4 minutos

Contraseña de las tres cuentas: **`Atelier2026!`**

| Rol | Correo | Ruta |
|---|---|---|
| Creador | `lucia@atelier.app` | `/dna` → `/prensa` |
| Aprobador A | `mateo@atelier.app` | `/mesa` |
| Aprobador B | `ines@atelier.app` | `/vision` |

1. **Lucía** compone el DNA (nombre, producto, tono, palabras prohibidas). El masthead pasa a MANUAL ACTIVO / RAG.
2. En **Prensa** genera ficha, guion y prompt de imagen. Cada pieza cita fragmentos del manual y queda `PENDING`.
3. **Mateo** abre Mesa, ve solo la marca activa, aprueba o rechaza.
4. **Inés** arrastra un packshot. Gemini contrasta nombre, paleta, voz y área de respeto contra el DNA. PASA / NO PASA con desglose.
5. En [Langfuse](https://cloud.langfuse.com) aparecen las tres trazas.

Varias marcas: si el nombre del DNA cambia, se crea otra marca. El chip del masthead cambia de marca y Mesa no mezcla colas. El kit (ficha + guion + prompt) aprobado queda con su DNA.

## Cómo correr en local

Hace falta Python 3.12+ (3.14 también, con `sqlmodel>=0.0.32`), Node 20+, pnpm y un Postgres (Supabase sirve).

**Backend**

```bash
cd atelier_backend
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

**Frontend**

```bash
cd atelier_front
cp .env.example .env
pnpm i
pnpm dev
```

- App: http://localhost:3000
- API / health: http://127.0.0.1:8000/health (`llm`, `vision`, `langfuse`)
- Docs: http://127.0.0.1:8000/docs

`SEED_DEMO_USERS=true` crea las tres cuentas al arrancar.

Tests: `cd atelier_backend && pytest -q`

## Variables

`atelier_backend/.env` — no commitear claves.

| Variable | Para qué |
|---|---|
| `DATABASE_URL` | Postgres de Supabase (`postgresql://…` o `postgresql+asyncpg://…`) |
| `JWT_SECRET` | Firma de access / refresh |
| `LLM_PROVIDER` | `live` (Groq + Gemini) o `template` (sin red) |
| `GROQ_API_KEY` / `GROQ_MODEL` | DNA y copy. Default: `qwen/qwen3.6-27b` |
| `GEMINI_API_KEY` / `GEMINI_MODEL` | Visión. Default: `gemini-3.6-flash` (cuentas nuevas ya no usan 2.5) |
| `LANGFUSE_PUBLIC_KEY` / `LANGFUSE_SECRET_KEY` | Observabilidad. Host: `https://cloud.langfuse.com` |
| `CORS_ORIGINS` | URL del front |
| `SEED_DEMO_USERS` | `true` en demo |

Front: `NEXT_PUBLIC_API_URL=http://127.0.0.1:8000`

## Arquitectura

Front y backend viven en carpetas distintas. Cada uno es modular (capas hexagonales). El único contrato entre ambos es HTTP + JWT.

### Backend — `atelier_backend/`

```
app/
  domain/           entidades, enums, ports  (sin FastAPI, sin SQL, sin Groq)
  application/      casos de uso: compose, generate, audit, auth, seed
  infrastructure/   SQLModel, pgvector, Groq, Gemini, embeddings, container
  api/v1/           routers: auth, brands, creative, governance
  core/             config, JWT, errores, Langfuse
```

El servicio habla con `BrandRepository`, `Embedder`, `LlmClient`, `VisionClient` (ports). Groq o el modo `template` se enchufan en `infrastructure/` sin tocar el dominio.

### Frontend — `atelier_front/`

```
features/           un módulo por mesa: dna, prensa, mesa, visión, auth
lib/domain/         Brand, Asset, Audit, Role  (tipos, sin fetch)
lib/application/    AuthProvider, BrandProvider
lib/infrastructure/ clientes HTTP por bounded context (auth, brands, creative, governance)
app/(workspace)/    rutas Next.js; páginas delgadas que montan un feature
components/         layout, UI, proof-sheet (compartido)
```

Una pantalla no llama a `fetch` directo: pasa por `lib/infrastructure/api/*`. El dominio no sabe de Next ni de FastAPI.

### Flujo de datos

- Nada se genera sin DNA indexado.
- Retrieval: embeddings locales 1536-d + `pgvector` en `brand_chunks`.
- Copy: Groq con JSON; palabras prohibidas se ocultan en el prompt y se reintenta si el modelo las copia.
- Visión: Gemini lee la imagen y el manual. ATELIER es la plataforma, no la marca a contrastar.
- Estados de pieza: `PENDING` → `APPROVED` | `REJECTED`.

## pgvector

Al arrancar, el API intenta:

```sql
create extension if not exists vector;
alter table brand_chunks add column if not exists embedding vector(1536);
```

Si Supabase lo bloquea, corre eso en SQL Editor.

## Deploy

- **App:** [https://atelier.marceloperu-09.workers.dev](https://atelier.marceloperu-09.workers.dev)
- **API / health:** [https://atelier-alicorp-api.onrender.com/health](https://atelier-alicorp-api.onrender.com/health)

El plan free de Render se duerme a los 15 min: **abre `/health` 1–2 min antes de la expo**.

## Presentación (6 slides)

Abre [`docs/presentacion.html`](docs/presentacion.html) en el navegador. `←` `→` o clic para pasar.

## Límites honestos

- Embeddings de retrieval son un hash local, no un modelo de embedding de red. pgvector sí persiste el vector.
- El crédito de Vertex no paga Google AI Studio; Visión usa API key de AI Studio.
- Piezas generadas *antes* del selector de marcas pueden quedar en el DNA que se sobrescribió. Marcas nuevas ya no se mezclan.
