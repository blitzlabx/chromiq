# Chromiq

> **Public Color Utility Platform** for designers and developers. Created by **Blitz** · GitHub/social: **blitzlabx**.

Chromiq is a no-authentication, no-database color workspace with a production-ready REST API. It converts color formats, builds harmony palettes and gradients, evaluates WCAG contrast, mixes and transforms colors, extracts dominant colors from images, and exposes machine-readable results for apps, design systems and automation.

## Highlights

- HEX, RGB/RGBA, HSL/HSLA, HSV/HSB and CMYK representations
- Conversion API with consistent JSON responses
- Complementary, analogous, triadic, tetradic, split-complementary and monochromatic palettes
- Configurable gradients and CSS output
- WCAG contrast ratios with AA/AAA checks
- RGB/HSL color mixing
- Tint, shade, tone, hue, saturation and brightness adjustments
- Secure random color generation
- Dominant color extraction from uploaded images
- Live browser workspace with copyable values and previews
- CSS/Tailwind-friendly values and JSON objects through the API
- `/ping` and `/health` endpoints for monitoring
- Request-size limits and simple in-process rate limiting
- Docker + Render configuration
- Automated tests, Ruff and mypy configuration

## Architecture

```text
Browser UI (static HTML/CSS/JS)
          |
          v
       FastAPI
          |
   +------+------+
   |             |
Color engine   Pillow
   |             |
   +-------> JSON REST API
```

The core color engine is independent from FastAPI, so the conversion, contrast, palette and transformation logic can be reused without the web layer. There is intentionally no database and no authentication system.

## Project structure

```text
chromiq/
├── app/
│   ├── __init__.py
│   ├── __main__.py
│   ├── color.py
│   └── main.py
├── static/
│   ├── index.html
│   ├── style.css
│   └── app.js
├── tests/
│   ├── test_color.py
│   └── test_api.py
├── Dockerfile
├── render.yaml
├── requirements.txt
├── requirements-dev.txt
├── pyproject.toml
├── .dockerignore
├── .gitignore
└── README.md
```

## Quick start

Python 3.11+ is recommended.

```bash
git clone <your-repository-url>
cd chromiq
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000`.

Interactive API documentation is available at `/docs` and `/redoc`.

## API

All API endpoints are public and require no account.

### Health

```bash
curl http://localhost:8000/ping
curl http://localhost:8000/health
```

### Convert

```bash
curl -X POST http://localhost:8000/api/v1/convert \
  -H 'Content-Type: application/json' \
  -d '{"color":{"value":"#6C5CE7"}}'
```

Python:

```python
import requests

response = requests.post(
    "https://your-render-service.onrender.com/api/v1/convert",
    json={"color": {"value": "#6C5CE7"}},
    timeout=10,
)
print(response.json())
```

### Palette

```bash
curl -X POST http://localhost:8000/api/v1/palette \
  -H 'Content-Type: application/json' \
  -d '{"color":{"value":"#6C5CE7"},"type":"triadic"}'
```

Supported palette types: `complementary`, `analogous`, `triadic`, `tetradic`, `split-complementary`, `monochromatic`.

### Gradient

```bash
curl -X POST http://localhost:8000/api/v1/gradient \
  -H 'Content-Type: application/json' \
  -d '{"colors":["#6C5CE7","#12C2E9"],"stops":8,"direction":"to right"}'
```

### Contrast

```bash
curl -X POST http://localhost:8000/api/v1/contrast \
  -H 'Content-Type: application/json' \
  -d '{"foreground":{"value":"#FFFFFF"},"background":{"value":"#6C5CE7"}}'
```

The response includes the numerical ratio plus `AA_normal`, `AA_large`, `AAA_normal`, and `AAA_large` booleans.

### Mix

```bash
curl -X POST http://localhost:8000/api/v1/mix \
  -H 'Content-Type: application/json' \
  -d '{"first":{"value":"#FF0000"},"second":{"value":"#0000FF"},"amount":0.5,"space":"rgb"}'
```

### Adjust

```bash
curl -X POST http://localhost:8000/api/v1/adjust \
  -H 'Content-Type: application/json' \
  -d '{"color":{"value":"#6C5CE7"},"operation":"tint","amount":0.2}'
```

Operations: `hue`, `saturation`, `brightness`, `tint`, `shade`, `tone`.

### Random

```bash
curl -X POST http://localhost:8000/api/v1/random
```

### Image extraction

```bash
curl -X POST http://localhost:8000/api/v1/extract \
  -F 'file=@photo.png' \
  -F 'count=8'
```

Images are capped at 5 MB and reduced before quantization. Supported formats depend on Pillow's installed decoders.

## Color model notes

Chromiq normalizes colors internally to floating-point RGBA values. Output representations are derived from that canonical value. HEX supports `#RGB`, `#RGBA`, `#RRGGBB` and `#RRGGBBAA`.

CMYK is emitted as a practical RGB-to-CMYK conversion. It is intended for utility/design workflows rather than printer-specific ICC color management.

## Validation and errors

Malformed or out-of-range values return HTTP `422` with a descriptive `detail`. Oversized request bodies and images return `413`. Excessive requests return `429`.

Example:

```json
{"detail":"Invalid HEX color. Use #RGB, #RGBA, #RRGGBB, or #RRGGBBAA."}
```

## Rate limiting

The service applies a lightweight per-IP in-process limit. The default is 120 requests per 60 seconds and can be changed with `RATE_LIMIT`.

Because the limiter is intentionally simple and memory-backed, it is appropriate for a small public utility deployment. For a high-volume multi-instance deployment, place a managed gateway/WAF or distributed rate limiter in front of Chromiq.

## Security

- No passwords or authentication data are collected.
- No database is used.
- Uploads are processed in memory and are not persisted by Chromiq.
- Request bodies are capped at 5 MB by middleware.
- Image uploads are independently capped at 5 MB.
- Pydantic validation constrains API payloads.
- The API should still be deployed behind TLS in production.

## Docker

Build and run locally:

```bash
docker build -t chromiq .
docker run --rm -p 10000:10000 -e PORT=10000 chromiq
```

The container reads Render's `PORT` environment variable and falls back to `10000` locally.

## Render deployment

This repository includes `render.yaml` and a production Dockerfile.

1. Push the repository to GitHub.
2. Create a new Render Blueprint or Web Service.
3. Select the repository.
4. Render detects `render.yaml` and the Dockerfile.
5. The service uses `/health` as its health check.
6. Render supplies `PORT`; the container passes it to Uvicorn.

For UptimeRobot, use:

```text
https://YOUR-SERVICE.onrender.com/ping
```

or:

```text
https://YOUR-SERVICE.onrender.com/health
```

## Quality checks

Install development dependencies:

```bash
pip install -r requirements-dev.txt
```

Run tests:

```bash
pytest -q
```

Run linting:

```bash
ruff check .
```

Run type checking:

```bash
mypy app
```

## Design principles

Chromiq intentionally avoids generic AI-dashboard styling. The interface is built around strong color surfaces, compact developer tooling, direct controls, live previews and responsive behavior. No authentication gate is inserted between users and the utilities.

## Limitations

- CMYK does not model printer-specific profiles.
- In-process rate limiting resets when a process restarts and is not shared across multiple instances.
- Image extraction is optimized for practical dominant-color discovery, not scientific colorimetry.
- Tailwind output is represented through standard color values suitable for token generation; Chromiq does not attempt to mutate a Tailwind configuration file remotely.

## Contributing

Fork the project, create a focused branch, add or update tests, run `pytest`, `ruff check .`, and `mypy app`, then open a pull request with a clear description.

## Credits

**Chromiq was created by Blitz.**

GitHub/social username: **blitzlabx**

All project branding and creator credit belong to **Blitz**.

## License

No license file is included by default. Add the license that matches how you intend to publish Chromiq before distributing it under an open-source license.
