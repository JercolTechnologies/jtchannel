# IDENTIDAD_CANAL.md — ADN y Estrategia Editorial del Canal

Este documento define la identidad, el posicionamiento, la filosofía editorial y la estrategia de empaque (títulos, miniaturas y metadatos) del canal. Todo agente que trabaje en este proyecto debe leerlo y regirse por él.

---

## 1. Misión y Filosofía Central

- **Propósito:** Desmitificar la inteligencia artificial práctica y el desarrollo de software moderno.
- **La tesis:** Muchas personas ajenas a la programación creen que conectar modelos de IA, crear bases de datos o automatizar flujos es "ingeniería aeroespacial", y muchos desarrolladores intentan hacerlo ver así para darse importancia. Este canal demuestra lo contrario: **es accesible, es rápido y no es más difícil que cualquier configuración cotidiana**.
- **Alcance temático:** Micro-tutoriales sobre **IA práctica en general** (agentes de código, automatizaciones, herramientas de productividad dev, APIs, modelos locales, despliegues rápidos). No nos encasillamos en un solo protocolo ni en una sola herramienta.
- **Formato innegociable:**
  - **1 a 3 minutos.**
  - **Directo al grano desde el segundo 1:** Cero intros largas, cero rodeos ("hola a todos, bienvenidos..."). La pantalla arranca con la acción y la narración acompaña lo que sucede.
  - **Siempre 16:9** (para calificar como vídeo tradicional en YouTube y sumar horas de monetización).

---

## 2. Tono y Narración

- **Idioma:** Inglés nativo, fluido y natural.
- **Voz:** `nova` en `gpt-4o-mini-tts`.
- **Personalidad:** Un colega desarrollador hablando con amigos: enérgico, cercano, entusiasta, claro y sin lenguaje académico aburrido.

---

## 3. Estrategia de Empaque: Miniaturas y Títulos

El espectador toma la decisión de hacer click en milisegundos basándose en dos piezas complementarias que **NUNCA deben repetir la misma información**:

```
[ MINIATURA ]  +  [ TÍTULO ]  =  HUECO DE CURIOSIDAD RESUELTO
(Resultado / Gancho visual)    (Palabra clave de búsqueda + Tema)
```

### Reglas para la Miniatura:
1. **Resuelve el "¿para qué?":** No basta con poner dos logos o nombres de herramientas. La miniatura debe comunicar en una micro-frase **qué se logra o qué pasa**.
2. **De 2 a 4 palabras máximo:** Nunca frases largas.
3. **No repetir el título:** Si el título dice el nombre del tutorial, la miniatura muestra la sorpresa, el resultado o el atajo (ej. *"AI BUILT MY DB"* o *"IT'S THAT EASY?"*).
4. **La prueba de los 120 px:** Debe ser 100% legible y reconocible reducida a 120 px de ancho (escala móvil).
5. **Negro con luz (no negro plano):** Luces y halos direccionales en los bordes para despegarse del fondo `#0f0f0f` del modo oscuro de YouTube.
6. **IA sin texto:** Los fondos se generan sin texto; la tipografía se monta limpia en postproducción con tipografía ultra-bold (Impact, Segoe UI Bold).

### Reglas para el Título:
1. **Longitud:** 41 a 55 caracteres (evita que se trunque en móviles).
2. **Front-loading:** Las palabras clave principales al principio.
3. **Coherencia con el guion:** No prometer keywords que el vídeo no menciona explícitamente.

---

## 4. Estructura de Assets del Repositorio

Para mantener el orden y evitar colisiones entre el canal y cada vídeo individual:

```
assets/
├── canal/                  # Assets permanentes del canal
│   ├── avatar.png          # Foto de perfil (800x800, circular)
│   └── banner.png          # Portada YouTube (2560x1440, Safe Area 1546x423)
│
└── videos/                 # Assets organizados por nombre descriptivo de vídeo
    ├── antigravity_supabase/       # Vídeo 1: Antigravity + Supabase
    │   ├── thumbnail.png           # Miniatura oficial 1280x720 (< 2MB)
    │   └── metadata.md             # Título, descripción y tags
    └── raw_supabase_vector_search/ # Vídeo 2: Búsqueda vectorial cruda en Supabase
        ...
```

---

## 5. Medición y Optimización

- Se mide el tiempo real que cuesta producir cada vídeo para asegurar que el canal sea sostenible a escala de publicación diaria/semanal.
- Objetivo de métricas: CTR sostenido > 6% y retención media > 60% gracias al formato compacto y sin relleno.
