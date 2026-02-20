# clawDeploy Security & Zero-Knowledge Architecture

When deploying NullClaw bots using `clawDeploy` on your infrastructure, the following architectural decisions allow you to offer maximum privacy to your clients.

## 1. Zero-Knowledge Deployment Model (SaaS)

If you are running a deployment service where clients launch their own bots, `clawDeploy` architecture can ensure that even you (as the infrastructure provider) cannot access their chats or secrets.

### Isolation by Default
- Each bot is deployed in a dynamically generated context (e.g., `deploy_bot1/`).
- **Dedicated Environment Files:** Each bot gets a unique `.env` file instead of relying on global secrets.
- **Dedicated Volumes:** The database is isolated to a specific Docker volume (`${APP_NAME}_data`), preventing accidental data leakage across clients.

### End-to-End Database Encryption
By default, NullClaw's memory database is an unencrypted SQLite file. To provide mathematical Zero-Knowledge guarantees:
1.  Clients generate a secure passphrase in their local browser.
2.  The passphrase is never stored in your central SaaS database.
3.  Instead, pass it as an ephemeral argument to the container via `deployer.py`.
4.  Replace the standard `sqlite3.h` binding in the bot's image with **SQLCipher** to AES-256 encrypt the database on disk.
5.  If the server is compromised or the volume is copied, the raw data cannot be read without the client's injected passphrase.

### Local LLM Inference
If privacy requirements extend to third-party endpoints, configure `NULLCLAW_MODEL` to point to a local model endpoint (such as an internally hosted Ollama or vLLM server).
- This guarantees prompt inputs and memory retrieval never exit the boundaries of your physical datacenter.

## 2. In-Container Security (NullClaw specifics)

Our deployments inherit NullClaw's native secure-by-default features:

- **ChaCha20-Poly1305 AEAD:** API keys injected via `TELEGRAM_BOT_TOKEN` or `NULLCLAW_API_KEY` are aggressively encrypted using an auto-generated (or explicitly mounted) `/.secret_key`.
- **Sandboxed Execution:** NullClaw automatically bounds execution limits using kernel-level isolations (Landlock, Firejail, Bubblewrap), neutralizing any client-initiated malicious code within the container boundary.
- **Audit Logging:** Immutably records executed policies, system calls, and access requests inside the container, facilitating easy forensic trails without exposing message contents.
