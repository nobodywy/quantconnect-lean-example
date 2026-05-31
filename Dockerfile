# ── LEAN Engine Runtime ───────────────────────────────────────────────
# Official QuantConnect LEAN Docker image.
# For custom environments, extend this base.

FROM quantconnect/lean:latest

# (Optional) install additional Python packages
# RUN pip install --no-cache-dir your-package

# Copy local algorithms into the container
COPY --chown=lean:lean algorithms/ /Lean/Launcher/bin/Debug/algorithms/
COPY --chown=lean:lean notebooks/ /Lean/Launcher/bin/Debug/notebooks/
COPY --chown=lean:lean lean.json    /Lean/Launcher/bin/Debug/
COPY --chown=lean:lean data/        /Lean/Data/

WORKDIR /Lean/Launcher/bin/Debug
