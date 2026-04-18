"""Service startup entry point"""
import uvicorn
from app.config.settings import get_settings


def main():
    settings = get_settings()
    uvicorn.run(
        "app.api.main:app",
        host=settings.api.host,
        port=settings.api.port,
        workers=settings.api.workers,
        reload=settings.api.reload,
        log_level=settings.monitoring.log_level.lower(),
    )


if __name__ == "__main__":
    main()
