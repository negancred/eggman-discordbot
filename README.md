# Eggman (Discord bot) — Dockerized

Quick steps to build and run the bot in Docker.

**Build image**

```bash
docker build -t eggman:latest .
```

**Run (recommended)** — use an env file for the token and persist `data/`:

```bash
# create a .env with DISCORD_TOKEN
docker run -d \
  --name eggman \
  --restart unless-stopped \
  --env-file .env \
  -v "$PWD/data":/app/data \
  eggman:latest
```

On Windows PowerShell replace `"$PWD/data"` with `${PWD}/data`.

Or with docker-compose:

```bash
docker-compose up -d --build
```

**Notes**
- `ffmpeg` and `yt-dlp` are installed in the image (yt-dlp is listed in `requirements.txt`).
- Keep your `DISCORD_TOKEN` out of version control; use `.env` or secret management on your host.

**Hosting**
- Push the image to Docker Hub or GitHub Container Registry and run it on any VPS or cloud instance with Docker.
- For automated builds, add a CI workflow to build and push the image when you tag or push to `main`.
