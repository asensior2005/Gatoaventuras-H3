# 🐱 GatoAventuras H3 - Cine Mágico Interactivo Infantil

> **Proyecto Oficial para el Concurso MiniMax H3 Max** 🏆  
> Generación de vídeo cinematográfico 8K en tiempo real con audio espacial y dirección de voz interactiva estilo *Bandersnatch felino*.

---

## 🌟 Características Principales

- 🎬 **Generación de Vídeo Ultrarrápida con MiniMax H3 Max:** Genera planos cinematográficos de 6 a 10 segundos en menos de 9 segundos con audio espacial inmersivo.
- 🎨 **Estilo Visual 3D Pixar / Claymorphism:** Mundos fantásticos con estética dulce, tierna y colores pastel diseñados para todos los públicos.
- 🎙️ **Dirección por Voz Libre ("Filtro de Creatividad Felino"):** El usuario puede dictar cualquier idea o locura por voz, y el LLM adapta la acción al mundo felino sin romper la coherencia visual.
- 🌈 **5 Universos Temáticos con Gatos Únicos:**
  1. 🧶 **Megaciudad de Rascadores:** Gatito naranja atigrado en rascacielos de soga y nubes de lana.
  2. 🥛 **Nebulosa Láctea y Cereal:** Gatito blanco nieve con escafandra cósmica en gravedad cero.
  3. 🔴 **Dimensión del Puntero Láser:** Gatito negro pantera en templos de cristal y neón.
  4. 🛁 **Valle de Burbujas de Jabón:** Gatito gris con impermeable en ríos de jabón.
  5. 🏺 **El Secreto de Bastet:** Gato sagrado egipcio en Alejandría y el mar Mediterráneo.
- ✨ **Creador de Universos a Medida:** Permite a los usuarios inventar mundos personalizados desde cero.
- 📥 **Exportador de Película Completa (FFmpeg):** Concatena todas las decisiones y escenas generadas en un archivo MP4 descargable de alta calidad.
- 🛡️ **Escudos de Protección de Saldo:** Sistema de caché inteligente ($0.00 en escenas repetidas) + limitador de 5 vidas felinas + modo jurado con clave (`H3CONTEST`).

---

## 🚀 Instalación y Ejecución Local

```bash
# 1. Instalar dependencias
pip install fastapi uvicorn httpx pydantic fal-client

# 2. Configurar la clave de API de fal.ai
export FAL_KEY="tu_fal_key_aqui"

# 3. Iniciar el servidor
python -m uvicorn server:app --host 0.0.0.0 --port 8000
```

---

## 🕹️ Modos de Control
- **Teclas Rápidas:** `[ 1 ]`, `[ 2 ]`, `[ 3 ]` para seleccionar opciones del Bento Grid.
- **Pantalla Completa:** Pulsa `F` o el botón `⛶` para activar el Modo Cine Inmersivo.
- **Voz:** Mantén pulsado el botón central del micrófono para dictar tus órdenes.

---
*Desarrollado con ❤️ para el Concurso MiniMax H3 Max.*
