"""Modal deployment configuration for AutoCI."""
import os
from modal import App, Image, Secret, asgi_app

image = Image.debian_slim(python_version="3.11").pip_install_from_requirements("requirements.txt")

app = App("autoci-backend", image=image)

secrets = [
    Secret.from_name("autoci-supabase"),
    Secret.from_name("autoci-anthropic"),
    Secret.from_name("autoci-deepseek"),
    Secret.from_name("autoci-adzuna"),
    Secret.from_name("autoci-tavily"),
    Secret.from_name("autoci-newsapi"),
    Secret.from_name("autoci-google-oauth"),
]

@app.function(
    secrets=secrets,
    allow_concurrent_inputs=10,
    container_idle_timeout=300,
    timeout=600,
)
@asgi_app()
def fastapi_app():
    from main import app
    return app
