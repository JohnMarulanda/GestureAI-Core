from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import controller_routes, config_routes

# Create FastAPI app instance with metadata
app = FastAPI(
    title="GestureAI API",
    description="API to control GestureAI modules and manage configurations",
    version="1.0.0"
)

# Configure CORS to allow cross-origin requests from any origin
origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,          # Allow requests from all origins
    allow_credentials=True,
    allow_methods=["*"],            # Allow all HTTP methods
    allow_headers=["*"],            # Allow all headers
)

# Include route modules for controllers and configuration management
app.include_router(controller_routes.router)
app.include_router(config_routes.router)

# Root endpoint providing basic API information
@app.get("/")
async def root():
    """
    Root endpoint with general information about the GestureAI API.

    Returns:
        A JSON object containing API name, version, description, and available endpoints.
    """
    return {
        "name": "GestureAI API",
        "version": "1.0.0",
        "description": "API for gesture control and system configuration in GestureAI",
        "endpoints": [
            "/controller - Manage gesture controllers",
            "/config - Manage system and gesture configurations"
        ]
    }
