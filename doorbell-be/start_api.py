import click
import uvicorn


@click.command()
@click.option(
    "--env",
    type=click.Choice(["local", "dev", "prod"], case_sensitive=False),
    default="local",
)
def main(env: str):
    uvicorn.run(
        app=f"doorbell_api:app",
        host="localhost",
        port=8000,
        reload=True if env != "prod" else False,
        workers=1,
    )


if __name__ == "__main__":
    main()