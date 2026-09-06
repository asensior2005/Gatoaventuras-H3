import os
import sys
import re
import json
import time
import shutil
import hashlib
import asyncio
import subprocess
from typing import Optional, List, Dict, Any

try:
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
import httpx


try:
    import fal_client
except ImportError:
    fal_client = None

app = FastAPI(title="GatoAventuras H3 - Edicion Protegida para Concurso")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
EXPORTS_DIR = os.path.join(BASE_DIR, "exports")
CACHE_DIR = os.path.join(STATIC_DIR, "cached_videos")
CACHE_FILE = os.path.join(BASE_DIR, "video_cache.json")

os.makedirs(EXPORTS_DIR, exist_ok=True)
os.makedirs(CACHE_DIR, exist_ok=True)

JUROR_PASSCODES = {"H3CONTEST", "GATO2026", "MINIMAX"}

video_cache: Dict[str, Dict[str, Any]] = {}
if os.path.exists(CACHE_FILE):
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            video_cache = json.load(f)
    except Exception:
        video_cache = {}

def save_cache():
    try:
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(video_cache, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print("Error guardando cache:", e)

ip_tokens: Dict[str, Dict[str, Any]] = {}
DEFAULT_TOKENS = 5

class ActionRequest(BaseModel):
    user_input: str
    universe: Optional[str] = "scratchers_city"
    mood: Optional[str] = "golden_hour"
    history: Optional[List[Dict[str, Any]]] = []
    juror_code: Optional[str] = None

class ExportRequest(BaseModel):
    video_urls: List[str]
    title: Optional[str] = "Mi_Pelicula_Gatitos"

class JurorVerifyRequest(BaseModel):
    code: str

class UniverseInitRequest(BaseModel):
    universe_id: Optional[str] = "custom"
    custom_title: Optional[str] = "Mundo Personalizado"
    custom_theme: Optional[str] = "Un mundo divertido para el gatito"

# =========================================================
# 5 UNIVERSES WITH DISTINCT PROTAGONIST CATS & COLORS
# =========================================================
UNIVERSES = {
    "scratchers_city": {
        "id": "scratchers_city",
        "title": "Megaciudad de Rascadores",
        "subtitle": "Gatito Naranja & Rascacielos de Cuerda",
        "icon": "🧶",
        "image_3d": "/static/icon_scratchers_3d.jpg",
        "description": "Rascacielos gigantes envueltos en soga de yute, calles de alfombras mullidas y nubes de ovillos de lana.",
        "character_anchor": "an adorable, super cute ginger orange tabby cat with soft fluffy fur, white paws, and big bright amber eyes",
        "starter": {
            "video_url": "/static/initial_scratchers_city.mp4",
            "narrative": "Un simpático gatito naranja explora una descomunal megaciudad hecha de materiales irresistibles: rascacielos gigantescos forrados en cuerda de rascador, avenidas de alfombra mullida y nubes de ovillos de lana flotando en el cielo.",
            "prompt": "Cinematic shot of an adorable ginger orange tabby cat exploring a giant fantasy city made entirely of scratching-post towers wrapped in sisal rope, fluffy carpet streets, and clouds made of giant floating colorful yarn balls, Pixar 8k, joyful whimsical orchestral audio",
            "choices": [
                {"id": "1", "icon": "🧗", "title": "Escalada vertical", "text": "Trepar a toda velocidad por la fachada de un rascacielos de cuerda de yute."},
                {"id": "2", "icon": "🧶", "title": "El ovillo volador", "text": "Saltar sobre una nube de lana y deshilacharla mientras flota en el aire."},
                {"id": "3", "icon": "🛋️", "title": "Destrucción masiva", "text": "Encontrar un sofá gigante de cuero y afilarse las uñas épicamente."}
            ]
        },
        "style": "giant city of scratching posts and wool, vibrant warm whimsical Pixar 8k, playful orchestral soundtrack"
    },
    "milky_nebula": {
        "id": "milky_nebula",
        "title": "Nebulosa Láctea y Cereal",
        "subtitle": "Gatito Blanco Nieve en Gravedad Cero",
        "icon": "🥛",
        "image_3d": "/static/icon_milky_3d.jpg",
        "description": "Fondo púrpura y rosa de leche cósmica, planetas de anillos de cereal Froot Loops y asteroides de galletas-pez.",
        "character_anchor": "an adorable, pure snow-white fluffy kitten wearing a cute glass astronaut helmet with cat ears and big sapphire blue eyes",
        "starter": {
            "video_url": "/static/initial_milky_nebula.mp4",
            "narrative": "Flotando en gravedad cero en una nebulosa psicodélica de leche cósmica púrpura y rosa, un esponjoso gatito blanco con su casco de astronauta con orejitas observa planetas de cereal de colores y asteroides de galleta-pez.",
            "prompt": "Cinematic zero gravity shot of an adorable pure white kitten wearing a cute astronaut helmet with cat ears floating weightlessly in a pastel pink and purple cosmic milky way galaxy, giant floating colorful cereal ring planets, fish-shaped cookie asteroids, 8k, celestial ambient audio",
            "choices": [
                {"id": "1", "icon": "🌌", "title": "Flotar sin gravedad", "text": "Dar volteretas lentas en el espacio persiguiendo una crujiente galleta-pez flotante."},
                {"id": "2", "icon": "🥛", "title": "Lamer la nebulosa", "text": "Acercarse a un remolino de leche cósmica flotante y beber de él con deleite."},
                {"id": "3", "icon": "🪐", "title": "Salto interplanetario", "text": "Usar un cereal gigante de colores como trampolín para impulsarse hacia otro planeta."}
            ]
        },
        "style": "psychedelic cosmic milk space, pastel pink and purple nebula, floating cereal rings, whimsical sci-fi 8k, celestial synth audio"
    },
    "laser_dimension": {
        "id": "laser_dimension",
        "title": "Dimensión del Puntero Láser",
        "subtitle": "Gatito Negro Pantera & Neón",
        "icon": "🔴",
        "image_3d": "/static/icon_laser_3d.jpg",
        "description": "Un antiguo templo subterráneo de cristal a oscuras iluminado por patrones de puntos láser de neón rojo.",
        "character_anchor": "an adorable, sleek jet-black kitten with shiny silky black fur and luminous glowing emerald-green eyes",
        "starter": {
            "video_url": "/static/initial_laser_dimension.mp4",
            "narrative": "En un templo oscuro de cristal, un ágil gatito negro como una pantera observa cómo infinidad de puntos láser de neón rojo empiezan a rebotar por suelos y columnas.",
            "prompt": "Cinematic shot of an adorable sleek black cat with glowing green eyes inside a mysterious dark crystal temple illuminated by glowing red laser dots and neon light patterns bouncing on the floor and glass pillars, 8k, mystical synth audio",
            "choices": [
                {"id": "1", "icon": "🔴", "title": "Cazar el punto", "text": "Lanzarse en una carrera hiperactiva contra el suelo para atrapar la escurridiza luz roja."},
                {"id": "2", "icon": "👥", "title": "Pelea de sombras", "text": "Interactuar y dar zarpazos juguetones a su propia sombra proyectada en la pared de neón."},
                {"id": "3", "icon": "🔮", "title": "Activar el portal", "text": "Pisar con la patita un botón láser gigante en el suelo para que la sala entera cambie de color."}
            ]
        },
        "style": "dark crystal temple with glowing crimson laser beams and neon floor reflections, atmospheric mystery, cinematic synth audio, 8k"
    },
    "soap_bubbles_valley": {
        "id": "soap_bubbles_valley",
        "title": "Valle de Burbujas de Jabón",
        "subtitle": "Gatito Gris Peluche con Chubasquero",
        "icon": "🛁",
        "image_3d": "/static/icon_soap_3d.jpg",
        "description": "Ríos de agua jabonosa cristalina y millones de burbujas gigantes iridiscentes.",
        "character_anchor": "an adorable, cute fluffy silver-grey British Shorthair kitten wearing a cute translucent waterproof yellow raincoat with hood",
        "starter": {
            "video_url": "/static/initial_soap_bubbles.mp4",
            "narrative": "Un valle verde bañado por ríos de agua jabonosa cristalina, donde flotan millones de burbujas gigantes. Un tierno gatito gris con un pequeño impermeable translúcido camina fascinado sin mojarse.",
            "prompt": "Cinematic shot of a cute silver-grey kitten wearing a cute translucent waterproof raincoat exploring a vibrant green valley with rivers of sparkling soap water and giant colorful iridescent soap bubbles floating everywhere, 8k, playful joyful audio",
            "choices": [
                {"id": "1", "icon": "🧼", "title": "Viajar en burbuja", "text": "Meterse dentro de una burbuja gigante y flotar suavemente sobre el valle."},
                {"id": "2", "icon": "💥", "title": "Ataque de garras", "text": "Explotar una ráfaga de mini burbujas en el aire a toda velocidad con zarpazos."},
                {"id": "3", "icon": "🏄", "title": "Tobogán de espuma", "text": "Deslizarse velozmente por una colina cubierta de espuma de jabón esponjosa."}
            ]
        },
        "style": "vibrant green valley with giant iridescent soap bubbles and fluffy foam slides, bright sunshine, playful joyful audio, 8k photorealistic"
    },
    "bastet_egypt": {
        "id": "bastet_egypt",
        "title": "El Secreto de Bastet",
        "subtitle": "Gato Sagrado Egipcio Mau",
        "icon": "🏺",
        "image_3d": "/static/icon_bastet_3d.jpg",
        "description": "Un gato sagrado en templos del Antiguo Egipto, puertos del Nilo y arrecifes del Mediterráneo.",
        "character_anchor": "a sleek, majestic Egyptian Mau cat with silver-grey spotted fur, luminous golden-amber eyes, and wearing an ornate ancient Egyptian gold collar inlaid with turquoise and lapis lazuli jewels",
        "starter": {
            "video_url": "/static/initial_bastet.mp4",
            "narrative": "Bajo la dorada luz del atardecer en el puerto de Alejandría, un majestuoso gato egipcio con collar de oro y lapislázuli observa el mar Mediterráneo sobre antiguas ruinas de piedra.",
            "prompt": "Cinematic shot of a majestic Egyptian cat with golden collar sitting on ancient stone ruins overlooking the turquoise Mediterranean sea, sunset lighting, 8k, spatial audio with waves and ancient score",
            "choices": [
                {"id": "1", "icon": "⛵", "title": "Subir al barco", "text": "Bajar hacia el muelle para subir a un barco de vela de madera sobre las olas."},
                {"id": "2", "icon": "🏛️", "title": "Entrar al templo", "text": "Girar hacia el interior del templo sagrado siguiendo una misteriosa luz dorada."},
                {"id": "3", "icon": "🐬", "title": "Mirar delfines", "text": "Acercarse al acantilado donde unos delfines saltan entre las olas turquesas."}
            ]
        },
        "style": "ancient Egypt coastal ruins, photorealistic 8k, warm golden hour lighting, Mediterranean sea, cinematic audio with ocean waves and ancient score"
    }
}

MOODS = {
    "golden_hour": "warm cinematic golden hour sunset lighting, soft golden sunbeams",
    "mystic_night": "atmospheric night with gentle moonlight and mystical glowing lanterns",
    "epic_storm": "dramatic cinematic weather with dynamic playful breeze and lighting",
    "peaceful_dawn": "serene fresh morning sunrise light, gentle mist and crystal clear air"
}

def get_cache_key(universe: str, action: str) -> str:
    norm = re.sub(r'[^a-zA-Z0-9áéíóúÁÉÍÓÚñÑ]', '', action.lower().strip())
    return f"{universe}_{norm}"

# =========================================================
# DYNAMIC COLOR & TRANSFORMATION OVERRIDE ENGINE
# =========================================================
def extract_custom_cat_appearance(raw_action_lower: str) -> Optional[str]:
    # Check if user asks to change the cat's color or breed
    if "blanco" in raw_action_lower or "blanca" in raw_action_lower:
        return "an adorable, pure snow-white fluffy cat with bright blue eyes"
    elif "negro" in raw_action_lower or "negra" in raw_action_lower:
        return "an adorable, sleek jet-black kitten with shiny silky black fur and luminous eyes"
    elif "rosa" in raw_action_lower or "rosado" in raw_action_lower:
        return "an adorable magical pastel-pink fluffy fantasy kitten with sparkling fur"
    elif "arcoiris" in raw_action_lower or "arco iris" in raw_action_lower or "colores" in raw_action_lower:
        return "a magical rainbow-colored pastel fantasy kitten with shimmering colorful fur"
    elif "naranja" in raw_action_lower or "rubio" in raw_action_lower:
        return "an adorable ginger orange tabby cat with soft fluffy fur and bright amber eyes"
    elif "azul" in raw_action_lower:
        return "a magical soft pastel sky-blue fluffy fantasy kitten"
    elif "dorado" in raw_action_lower or "oro" in raw_action_lower:
        return "a magical glowing golden celestial kitten with shining luminous fur"
    elif "siames" in raw_action_lower or "siamés" in raw_action_lower:
        return "an adorable Siamese kitten with dark brown points, cream coat, and deep blue eyes"
    elif "calico" in raw_action_lower or "carey" in raw_action_lower:
        return "an adorable tricolor calico kitten with white, orange and brown patches"
    return None

def adapt_user_action_creatively(raw_action: str, universe_key: str) -> tuple[str, str, Optional[str]]:
    raw_lower = raw_action.lower().strip()
    override_cat = extract_custom_cat_appearance(raw_lower)
    
    # Specific color transformation requests
    if override_cat and ("cambie" in raw_lower or "sea" in raw_lower or "vuelva" in raw_lower or "pinte" in raw_lower or "transforme" in raw_lower or "color" in raw_lower):
        narrative = f"¡Magia potagia! El gatito se transforma y ahora tiene un precioso pelaje de nuevo color mientras se mira contento las patitas."
        prompt_en = f"the cat magically and joyfully transforming its fur color in a burst of sparkling magical dust, happily admiring its new coat"
        return narrative, prompt_en, override_cat

    if "demolicion" in raw_lower or ("ovillo" in raw_lower and "derriba" in raw_lower) or "torre" in raw_lower:
        narrative = "¡El gato se balancea sobre un colosal ovillo de lana como si fuera una bola de demolición, derribando una torre de rascadores que cae como fichas de dominó!"
        prompt_en = "the cat thrillingly swinging on a giant wool yarn ball like a wrecking ball, playfully toppling a scratching-post tower in slow motion domino effect"
        return narrative, prompt_en, override_cat

    elif "skate" in raw_lower or ("galleta" in raw_lower and ("tabla" in raw_lower or "mont" in raw_lower or "surf" in raw_lower)):
        narrative = "¡El gato se sube sobre una galleta flotante con forma de pez y la usa como tabla de skate espacial, surfeando a través de los anillos de cereal cósmicos!"
        prompt_en = "the cat coolly riding on top of a floating fish-shaped cookie like a space skateboard, surfing gracefully through giant colorful cereal rings in zero gravity"
        return narrative, prompt_en, override_cat

    elif "mil" in raw_lower or ("laser" in raw_lower and "multipli" in raw_lower) or "loco" in raw_lower or "circulo" in raw_lower:
        narrative = "¡El punto láser se multiplica mágicamente en cientos de destellos rojos por toda la sala y el gato empieza a correr en círculos a toda velocidad con alegría desbordante!"
        prompt_en = "the red laser light splitting into hundreds of sparkling red dots across the crystal floor, with the cat joyfully sprinting in hyperactive circles chasing the sparkles"
        return narrative, prompt_en, override_cat

    elif "rugido" in raw_lower or "ruge" in raw_lower or ("burbuja" in raw_lower and "protec" in raw_lower) or "escudo" in raw_lower:
        narrative = "¡El gato suelta un adorable y poderoso rugido felino que infla una gigantesca mega burbuja protectora iridiscente a su alrededor, rebotando por el valle!"
        prompt_en = "the cat letting out a cute fierce roar that inflates a giant glowing iridescent bubble shield around itself, bouncing playfully across the green valley"
        return narrative, prompt_en, override_cat

    elif "tanque" in raw_lower or "guerra" in raw_lower or "metralleta" in raw_lower:
        narrative = "El gato se sube con valentía dentro de una caja de cartón blindada decorada como un tanque de juguete con ruedas de carretes de hilo, rodando triunfalmente por el escenario."
        prompt_en = "the cat hilariously and proudly riding inside a cute toy cardboard tank with yarn-spool wheels rolling smoothly through the scene"
        return narrative, prompt_en, override_cat

    elif "rayo" in raw_lower or "disparar" in raw_lower or "destru" in raw_lower or "bomba" in raw_lower or "misil" in raw_lower:
        narrative = "El gato estornuda graciosamente y, por accidente, activa un artefacto mágico que dispara un destello cósmico de luz haciendo levitar una roca."
        prompt_en = "the cat sneezes adorably, accidentally activating a magical glowing star relic that emits a bright glowing beam of pastel light making a floating object levitate"
        return narrative, prompt_en, override_cat

    elif "mortal" in raw_lower or "salto" in raw_lower or "acrobacia" in raw_lower or "voltereta" in raw_lower:
        narrative = "¡El gato realiza un impresionante mortal hacia atrás en el aire con gracia felina, aterrizando en perfecto equilibrio sobre una superficie flotante!"
        prompt_en = "the cat performing a graceful slow-motion backflip in mid-air and landing perfectly on its four paws on a floating surface with cinematic flair"
        return narrative, prompt_en, override_cat

    clean_action = re.sub(r'[𐀀-􏿿]', '', raw_action).strip()
    narrative = f"El gato decide: {clean_action}"
    prompt_en = f"the cat dynamically performing the action: {clean_action}"
    return narrative, prompt_en, override_cat

def build_locked_prompt(adapted_action_en: str, universe_key: str, mood_key: str = "golden_hour", override_cat: Optional[str] = None) -> str:
    u = UNIVERSES.get(universe_key, UNIVERSES["scratchers_city"])
    fixed_style = "Cinematic 3D Pixar meets photorealistic 8k, highly detailed realistic fur, vibrant rich colors, raytraced lighting, realistic natural spatial stereo audio"
    
    # Use overridden appearance if user requested color change, otherwise use universe default
    char_anchor = override_cat if override_cat else u.get("character_anchor", "an adorable cute fluffy kitten")
    mood_desc = MOODS.get(mood_key, MOODS["golden_hour"])
    world_env = u["style"]
    
    return f"[STYLE: {fixed_style}] [PROTAGONIST: {char_anchor}] [ACTION: {adapted_action_en}] [ENVIRONMENT & ATMOSPHERE: in {world_env}, {mood_desc}]. Photorealistic masterpiece, 8k resolution, crisp spatial sound."

def generate_bento_choices(action_narrative: str, universe_key: str) -> List[Dict[str, str]]:
    if universe_key == "scratchers_city":
        return [
            {"id": "1", "icon": "🧗", "title": "Escalada vertical", "text": "Trepar a toda velocidad por la fachada de un rascacielos de cuerda de yute."},
            {"id": "2", "icon": "🧶", "title": "El ovillo volador", "text": "Saltar sobre una nube de lana y deshilacharla mientras flota en el aire."},
            {"id": "3", "icon": "🛋️", "title": "Destrucción masiva", "text": "Encontrar un sofá gigante de cuero y afilarse las uñas épicamente."}
        ]
    elif universe_key == "milky_nebula":
        return [
            {"id": "1", "icon": "🌌", "title": "Flotar sin gravedad", "text": "Dar volteretas lentas en el espacio persiguiendo una crujiente galleta-pez flotante."},
            {"id": "2", "icon": "🥛", "title": "Lamer la nebulosa", "text": "Acercarse a un remolino de leche cósmica flotante y beber de él con deleite."},
            {"id": "3", "icon": "🪐", "title": "Salto interplanetario", "text": "Usar un cereal gigante de colores como trampolín para impulsarse hacia otro planeta."}
        ]
    elif universe_key == "laser_dimension":
        return [
            {"id": "1", "icon": "🔴", "title": "Cazar el punto", "text": "Lanzarse en una carrera hiperactiva contra el suelo para atrapar la escurridiza luz roja."},
            {"id": "2", "icon": "👥", "title": "Pelea de sombras", "text": "Interactuar y dar zarpazos juguetones a su propia sombra proyectada en la pared de neón."},
            {"id": "3", "icon": "🔮", "title": "Activar el portal", "text": "Pisar con la patita un botón láser gigante en el suelo para que la sala entera cambie de color."}
        ]
    elif universe_key == "soap_bubbles_valley":
        return [
            {"id": "1", "icon": "🧼", "title": "Viajar en burbuja", "text": "Meterse dentro de una burbuja gigante y flotar suavemente sobre el valle."},
            {"id": "2", "icon": "💥", "title": "Ataque de garras", "text": "Explotar una ráfaga de mini burbujas en el aire a toda velocidad con zarpazos."},
            {"id": "3", "icon": "🏄", "title": "Tobogán de espuma", "text": "Deslizarse velozmente por una colina cubierta de espuma de jabón esponjosa."}
        ]
    elif universe_key == "bastet_egypt":
        return [
            {"id": "1", "icon": "⛵", "title": "Subir al barco", "text": "Bajar hacia el muelle para subir a un barco de vela de madera sobre las olas."},
            {"id": "2", "icon": "🏛️", "title": "Entrar al templo", "text": "Girar hacia el interior del templo sagrado siguiendo una misteriosa luz dorada."},
            {"id": "3", "icon": "🐬", "title": "Mirar delfines", "text": "Acercarse al acantilado donde unos delfines saltan entre las olas turquesas."}
        ]
    else:
        return [
            {"id": "1", "icon": "🐾", "title": "Avanzar", "text": "Explorar con cautela el siguiente rincón del escenario."},
            {"id": "2", "icon": "🔍", "title": "Investigar", "text": "Examinar de cerca un objeto misterioso que brilla en el suelo."},
            {"id": "3", "icon": "✨", "title": "Sorpresa", "text": "Hacer un movimiento juguetón para ver qué ocurre en el entorno."}
        ]

@app.get("/")
def get_index():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))

@app.get("/api/universes")
def get_all_universes():
    return JSONResponse(list(UNIVERSES.values()))

@app.get("/api/user_tokens")
def get_tokens(request: Request):
    client_ip = request.client.host if request.client else "127.0.0.1"
    if client_ip not in ip_tokens:
        ip_tokens[client_ip] = {"tokens": DEFAULT_TOKENS, "is_juror": False}
    return JSONResponse(ip_tokens[client_ip])

@app.post("/api/universe/custom")
async def create_custom_universe(req: UniverseInitRequest, request: Request):
    title = req.custom_title.strip() if req.custom_title else "Mundo Mágico"
    theme = req.custom_theme.strip() if req.custom_theme else "Un reino de chuches y diversión felina"
    uid = f"custom_{int(time.time())}"
    
    client_ip = request.client.host if request.client else "127.0.0.1"
    if client_ip not in ip_tokens:
        ip_tokens[client_ip] = {"tokens": DEFAULT_TOKENS, "is_juror": False}
    
    user_data = ip_tokens[client_ip]
    is_juror = user_data.get("is_juror", False)
    if not is_juror and user_data["tokens"] <= 0:
        raise HTTPException(
            status_code=429,
            detail="Has agotado tus 5 Pescaditos Mágicos gratuitos. Introduce la clave de jurado para crear mundos infinitos."
        )
    
    if not is_juror:
        user_data["tokens"] = max(0, user_data["tokens"] - 1)

    # Clean cat with no Egyptian costumes for custom worlds
    char_desc = "an adorable, super cute and fluffy ginger tabby kitten with big bright curious eyes"
    final_prompt = (
        f"[STYLE: Cinematic 3D Pixar meets photorealistic 8k, highly detailed realistic fur, vibrant rich colors, raytraced lighting, realistic natural spatial stereo audio] "
        f"[PROTAGONIST: {char_desc}] "
        f"[ACTION: enthusiastically exploring {theme} with curiosity and joyful animation] "
        f"[ENVIRONMENT & ATMOSPHERE: in {theme}, warm cinematic golden hour lighting]. Photorealistic masterpiece, 8k resolution, crisp spatial sound."
    )
    
    video_url = None
    try:
        result = await asyncio.to_thread(
            fal_client.subscribe,
            "minimax/h3-max/text-to-video",
            arguments={
                "prompt": final_prompt,
                "aspect_ratio": "16:9"
            },
            with_logs=False
        )
        if isinstance(result, dict):
            if "video" in result and isinstance(result["video"], dict):
                video_url = result["video"].get("url")
            elif "videos" in result and len(result["videos"]) > 0:
                video_url = result["videos"][0].get("url") if isinstance(result["videos"][0], dict) else result["videos"][0]
            elif "url" in result:
                video_url = result["url"]
    except Exception as e:
        print("Error generando vídeo para mundo personalizado:", e)

    if not video_url:
        video_url = "/static/initial_scratchers_city.mp4"

    narrative = f"¡El gatito explorador aterriza en {title}! El aire huele a pura magia mientras contempla {theme}."

    new_u = {
        "id": uid,
        "title": title,
        "subtitle": "Universo Creado por Ti",
        "icon": "✨",
        "image_3d": "/static/icon_scratchers_3d.jpg",
        "description": theme,
        "character_anchor": char_desc,
        "starter": {
            "video_url": video_url,
            "narrative": narrative,
            "prompt": final_prompt,
            "choices": [
                {"id": "1", "icon": "🐾", "title": "Explorar a fondo", "text": f"Caminar con curiosidad para descubrir los secretos de {theme}."},
                {"id": "2", "icon": "✨", "title": "Probar algo divertido", "text": f"Hacer una acrobacia y jugar con los objetos mágicos de {title}."},
                {"id": "3", "icon": "🔍", "title": "Buscar tesoros", "text": f"Inspeccionar un rincón brillante que resalta en {title}."}
            ]
        },
        "style": f"{theme}, vibrant warm whimsical Pixar 8k, playful orchestral soundtrack"
    }

    UNIVERSES[uid] = new_u
    return JSONResponse(new_u)

@app.post("/api/verify_juror")
def verify_juror(req: JurorVerifyRequest, request: Request):
    client_ip = request.client.host if request.client else "127.0.0.1"
    if req.code.strip().upper() in JUROR_PASSCODES:
        if client_ip not in ip_tokens:
            ip_tokens[client_ip] = {"tokens": 9999, "is_juror": True}
        else:
            ip_tokens[client_ip]["tokens"] = 9999
            ip_tokens[client_ip]["is_juror"] = True
        return JSONResponse({"status": "success", "is_juror": True, "tokens": 9999})
    else:
        raise HTTPException(status_code=403, detail="Código de jurado incorrecto.")

@app.post("/api/generate")
async def generate_scene(req: ActionRequest, request: Request):
    user_action = req.user_input.strip()
    if not user_action:
        raise HTTPException(status_code=400, detail="La acción no puede estar vacía.")
    
    universe_key = req.universe or "scratchers_city"
    mood_key = req.mood or "golden_hour"
    client_ip = request.client.host if request.client else "127.0.0.1"

    if client_ip not in ip_tokens:
        ip_tokens[client_ip] = {"tokens": DEFAULT_TOKENS, "is_juror": False}
    
    user_data = ip_tokens[client_ip]
    is_juror = user_data.get("is_juror", False) or (req.juror_code and req.juror_code.strip().upper() in JUROR_PASSCODES)
    if is_juror:
        user_data["is_juror"] = True
        user_data["tokens"] = 9999

    narrative_es, prompt_action_en, override_cat = adapt_user_action_creatively(user_action, universe_key)
    cache_key = get_cache_key(universe_key, user_action)

    if cache_key in video_cache and not override_cat:
        cached_entry = video_cache[cache_key]
        cached_file = os.path.join(STATIC_DIR, cached_entry["local_rel_path"])
        if os.path.exists(cached_file):
            choices = generate_bento_choices(narrative_es, universe_key)
            return JSONResponse({
                "status": "success",
                "video_url": f"/static/{cached_entry['local_rel_path']}",
                "narrative": cached_entry.get("narrative", narrative_es),
                "raw_action": user_action,
                "prompt_used": cached_entry.get("prompt_used", "Cache hit"),
                "choices": choices,
                "generation_time": "0.1s (Caché Instantánea)",
                "model": "MiniMax H3 Max (Caché $0.00)",
                "tokens_left": user_data["tokens"],
                "is_juror": is_juror,
                "cache_hit": True
            })

    if not is_juror and user_data["tokens"] <= 0:
        raise HTTPException(
            status_code=429,
            detail="Has agotado tus 5 Pescaditos Mágicos gratuitos. Puedes seguir disfrutando de todas las opciones en caché o introducir la clave de jurado."
        )

    if not is_juror:
        user_data["tokens"] = max(0, user_data["tokens"] - 1)

    final_prompt = build_locked_prompt(prompt_action_en, universe_key, mood_key, override_cat)
    
    t0 = time.time()
    try:
        def on_queue_update(update):
            if isinstance(update, fal_client.InProgress):
                for log in update.logs:
                    pass

        result = await asyncio.to_thread(
            fal_client.subscribe,
            "minimax/h3-max/text-to-video",
            arguments={
                "prompt": final_prompt,
                "aspect_ratio": "16:9"
            },
            with_logs=True,
            on_queue_update=on_queue_update
        )
        
        t1 = time.time()
        video_url = None
        if isinstance(result, dict):
            if "video" in result and isinstance(result["video"], dict):
                video_url = result["video"].get("url")
            elif "videos" in result and len(result["videos"]) > 0:
                video_url = result["videos"][0].get("url") if isinstance(result["videos"][0], dict) else result["videos"][0]
            elif "url" in result:
                video_url = result["url"]
                
        if not video_url:
            raise Exception("No se pudo obtener la URL del vídeo generado.")

        filename_hash = hashlib.md5(cache_key.encode()).hexdigest()[:12]
        cache_filename = f"cached_{filename_hash}.mp4"
        cache_rel_path = f"cached_videos/{cache_filename}"
        cache_full_path = os.path.join(STATIC_DIR, cache_rel_path)

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.get(video_url)
                if resp.status_code == 200:
                    with open(cache_full_path, "wb") as f:
                        f.write(resp.content)
                    video_cache[cache_key] = {
                        "local_rel_path": cache_rel_path,
                        "narrative": narrative_es,
                        "prompt_used": final_prompt,
                        "created_at": time.time()
                    }
                    save_cache()
                    video_url = f"/static/{cache_rel_path}"
        except Exception as e:
            print("No se pudo guardar copia local de caché:", e)

        choices = generate_bento_choices(narrative_es, universe_key)
        
        return JSONResponse({
            "status": "success",
            "video_url": video_url,
            "narrative": narrative_es,
            "raw_action": user_action,
            "prompt_used": final_prompt,
            "choices": choices,
            "generation_time": f"{round(t1 - t0, 1)}s",
            "model": "MiniMax H3 Max (@fal.ai)",
            "tokens_left": user_data["tokens"],
            "is_juror": is_juror,
            "cache_hit": False
        })
    except Exception as e:
        err_msg = str(e)
        if "Exhausted balance" in err_msg:
            raise HTTPException(status_code=402, detail="Saldo de fal.ai agotado. Recarga en fal.ai/dashboard/billing.")
        raise HTTPException(status_code=500, detail=f"Error en fal.ai: {err_msg}")

@app.post("/api/export_movie")
async def export_movie(req: ExportRequest):
    if not req.video_urls:
        raise HTTPException(status_code=400, detail="No hay vídeos para unir.")
    
    session_id = f"movie_{int(time.time())}"
    temp_dir = os.path.join(EXPORTS_DIR, session_id)
    os.makedirs(temp_dir, exist_ok=True)
    
    try:
        downloaded_files = []
        async with httpx.AsyncClient(timeout=60.0) as client:
            for idx, url in enumerate(req.video_urls):
                clip_path = os.path.join(temp_dir, f"clip_{idx:03d}.mp4")
                if url.startswith("/static/"):
                    local_p = os.path.join(STATIC_DIR, url.replace("/static/", ""))
                    if os.path.exists(local_p):
                        shutil.copy(local_p, clip_path)
                        downloaded_files.append(clip_path)
                        continue
                        
                res = await client.get(url)
                if res.status_code == 200:
                    with open(clip_path, "wb") as f:
                        f.write(res.content)
                    downloaded_files.append(clip_path)
                else:
                    print(f"Error descargando {url}: status {res.status_code}")
                    
        if not downloaded_files:
            raise Exception("No se pudo descargar ningún clip.")
            
        out_filename = f"{req.title or 'Pelicula_Gatitos'}_{session_id}.mp4"
        final_output_path = os.path.join(EXPORTS_DIR, out_filename)
        
        if len(downloaded_files) == 1:
            shutil.copy(downloaded_files[0], final_output_path)
        else:
            concat_list_path = os.path.join(temp_dir, "concat.txt")
            with open(concat_list_path, "w", encoding="utf-8") as f:
                for fpath in downloaded_files:
                    clean_p = fpath.replace(chr(92), "/")
                    f.write("file '" + clean_p + "'\n")
            
            cmd = f'ffmpeg -y -f concat -safe 0 -i "{concat_list_path}" -c copy "{final_output_path}"'
            proc = subprocess.run(cmd, shell=True, capture_output=True)
            if proc.returncode != 0:
                cmd_reencode = f'ffmpeg -y -f concat -safe 0 -i "{concat_list_path}" -c:v libx264 -c:a aac "{final_output_path}"'
                subprocess.run(cmd_reencode, shell=True, capture_output=True)
                
        return JSONResponse({
            "status": "success",
            "download_url": f"/exports/{out_filename}",
            "filename": out_filename,
            "clips_count": len(downloaded_files)
        })
    finally:
        try:
            shutil.rmtree(temp_dir, ignore_errors=True)
        except Exception:
            pass

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
app.mount("/exports", StaticFiles(directory=EXPORTS_DIR), name="exports")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
