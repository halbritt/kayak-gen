FROM python:3.12-slim

# VTK pulls in OpenGL + Mesa for off-screen rendering.
RUN apt-get update && apt-get install -y --no-install-recommends \
        libgl1 \
        libglib2.0-0 \
        libxrender1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY pyproject.toml ./
COPY kayakgen ./kayakgen
COPY generator.py gui.py pyvista_view.py ./

RUN pip install --no-cache-dir -e ".[web]"

ENV TRAME_HOST=0.0.0.0
ENV TRAME_PORT=8080
EXPOSE 8080

CMD ["kayakgen", "serve", "--host", "0.0.0.0", "--port", "8080"]
