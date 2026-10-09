import uvicorn
from app.config import settings

if __name__ == "__main__":
    print("=" * 70)
    print(f"🚀 Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    print(f"🌐 Web UI: http://{settings.HOST}:{settings.PORT}")
    print(f"📖 Swagger API Docs: http://{settings.HOST}:{settings.PORT}/docs")
    print(f"🗄️ Database: {settings.DATABASE_URL}")
    print("=" * 70)
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
