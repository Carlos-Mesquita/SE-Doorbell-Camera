import os

import click
import uvicorn
from dotenv import load_dotenv

load_dotenv()


@click.command()
@click.option(
    "--env",
    type=click.Choice(["local", "staging", "production"], case_sensitive=False),
    default="local",
)
def main(env: str):
    os.environ["ENV"] = env.upper()
    uvicorn.run(
        app=f"doorbell_api:app",
        host="0.0.0.0",
        port=8000,
        reload=True if env != "prod" else False,
        workers=1,
    )


if __name__ == "__main__":
    main()