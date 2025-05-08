from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from core.controllers.volume_controller import VolumeController
from core.controllers.brightness_controller import BrightnessController
from core.controllers.app_controller import AppController
from core.controllers.shortcuts_controller import ShortcutsController
from core.controllers.keyboard_controller import KeyboardController
from core.controllers.navigation_controller import NavigationController
from core.controllers.system_controller import SystemController
from core.controllers.multimedia_controller import MultimediaController
from core.controllers.zoom_controller import ZoomController
from core.controllers.paint_controller import PaintController
from core.controllers.mouse_controller import MouseController

app = FastAPI(title="GestureAI API", description="API para controlar los módulos de GestureAI", version="1.0.0")

origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

router = APIRouter()

controllers = {
    "volume": VolumeController,
    "brightness": BrightnessController,
    "app": AppController,
    "shortcuts": ShortcutsController,
    "keyboard": KeyboardController,
    "navigation": NavigationController,
    "system": SystemController,
    "multimedia": MultimediaController,
    "zoom": ZoomController,
    "paint": PaintController,
    "mouse": MouseController
}

@router.get("/controllers")
def list_controllers():
    return {"controllers": list(controllers.keys())}

@router.post("/controller/{name}/start")
def start_controller(name: str):
    if name not in controllers:
        return {"error": "Controlador no encontrado"}
    try:
        controller = controllers[name]()
        # Aquí podrías lanzar el controlador en un hilo o proceso separado
        # Por simplicidad, solo devolvemos un mensaje
        return {"status": f"{name} iniciado"}
    except Exception as e:
        return {"error": str(e)}

@router.post("/controller/{name}/stop")
def stop_controller(name: str):
    # Implementar lógica para detener el controlador si es necesario
    return {"status": f"{name} detenido (implementación pendiente)"}

@router.get("/controller/{name}/status")
def controller_status(name: str):
    # Implementar lógica para consultar el estado real del controlador
    return {"status": f"Estado de {name} no implementado aún"}

app.include_router(router)