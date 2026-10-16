# -*- coding: utf-8 -*-
# Ruta: engine/scripts/probar_voces.py
#
# PRUEBA DE VOZ ANTES DE COMPROMETER UN GUION ENTERO.
#
# Genera el MISMO parrafo con varias voces para poder elegir escuchando en vez
# de eligiendo por catalogo. Cuesta centimos; equivocarse de voz y darse cuenta
# con doce minutos de audio ya generados cuesta bastante mas.
#
# El texto por defecto no es cualquiera: es el parrafo del versus del guion de
# Secretariat, que tiene cifras, nombres propios dificiles (Keeneland,
# Thoroughbred, Terlingua) y un cambio de ritmo en mitad. Si una voz va a
# tropezar, tropieza ahi. Un parrafo facil no prueba nada.
#
# Uso:
#     python engine\scripts\probar_voces.py
#     python engine\scripts\probar_voces.py --voces echo,nova,ash,alloy
#     python engine\scripts\probar_voces.py --texto "otro parrafo" --salida C:\ruta
#
#     # con el texto REAL de una escena, y con el modelo nuevo:
#     python engine\scripts\probar_voces.py --proyecto SH_secretariat_p1 --escena 20 ^
#            --modelo gpt-4o-mini-tts --voces marin,cedar,nova
#
# NOTA: esto SI consume saldo de la API (un parrafo por voz, centimos).
#
# --- POR QUE SE PUEDE LEER UNA ESCENA DEL MANIFEST --------------------------
#
# El parrafo por defecto tiene 63 palabras, y eso sirve para juzgar timbre pero
# NO para reproducir los fallos que aparecen en produccion: 'tts-1-hd' se rompe
# con entradas largas -en este canal, a partir de los ~26 segundos- y con un
# parrafo corto ese fallo no se manifiesta nunca. Probar la voz con un texto que
# no puede fallar es probar la mitad del problema.
#
# Ademas, escribir a mano un parrafo de 600 caracteres con tildes en PowerShell
# es una fuente de erratas: el texto que se prueba deja de ser el que se narra, y
# entonces la prueba no prueba lo que uno cree.
#
# --- 'speed' NO EXISTE EN TODOS LOS MODELOS ---------------------------------
#
# 'tts-1' y 'tts-1-hd' aceptan 'speed'. Los modelos nuevos controlan el ritmo por
# 'instructions', en prosa. Mandar 'speed' a un modelo que no lo espera es un
# error de API, asi que se omite segun el modelo en vez de mandarlo siempre.

import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import canal                               # noqa: E402
import config                              # noqa: E402
from dotenv import load_dotenv             # noqa: E402
from openai import OpenAI                  # noqa: E402

# Modelos que aceptan el parametro 'speed' del endpoint /v1/audio/speech.
MODELOS_CON_SPEED = {"tts-1", "tts-1-hd"}

TEXTO_POR_DEFECTO = (
    "A la izquierda, Canadian Bound. Macho. En la venta de julio de Keeneland de mil "
    "novecientos setenta y seis se convirtio en el primer yearling de la historia del "
    "Thoroughbred en superar el millon de dolares. El precio final fue un millon y medio. "
    "A la derecha, Terlingua. Hembra. Hija de Secretariat tambien. Se vendio por una "
    "fraccion de ese precio."
)

# onyx queda fuera a proposito: es la de The Corporate Code. Si los dos canales
# suenan igual, el espectador que vea ambos nota que salen de la misma fabrica.
VOCES_POR_DEFECTO = ["echo", "ash", "nova"]


def resolver_canal(proyecto: str | None) -> None:
    """Apunta config al canal donde vive el proyecto (ADR-037).

    Sin esto el script se quedaba en el canal por defecto -the_corporate_code- y
    buscaba el manifest de un proyecto de Sabermetria dentro de la carpeta de
    TCC. Peor todavia en silencio: '--modelo' y la voz por defecto salian de la
    configuracion del canal equivocado, asi que una prueba hecha 'sin tocar nada'
    se estaba haciendo con la voz del otro canal.
    """
    if not proyecto:
        return
    elegido = canal.detectar(config.REPO_ROOT, proyecto)
    if not elegido:
        print(f"[AVISO] no se pudo deducir el canal de '{proyecto}'; se usa "
              f"'{config.CANAL_ACTUAL}'.")
        return
    datos = config.aplicar_canal(elegido)
    nombre = datos.get("nombre", elegido) if datos else elegido
    print(f"[canal] {nombre}  ({elegido})")


def texto_de_escena(proyecto: str, escena: int) -> str:
    """Saca el 'audio_text' EXACTO de una escena del manifest del proyecto."""
    manifest = config.project_paths(proyecto)["manifest"]
    if not manifest.exists():
        sys.exit(f"ERROR: no existe el manifest: {manifest}. Corre 'parse' primero.")
    datos = json.loads(manifest.read_text(encoding="utf-8"))
    for e in datos.get("scenes", []):
        if e.get("index") == escena:
            if e.get("type") != "narrated":
                sys.exit(f"ERROR: la escena {escena} no es narrada (es '{e.get('type')}').")
            return e["audio_text"]
    sys.exit(f"ERROR: no hay escena {escena} en {manifest}.")


def main():
    p = argparse.ArgumentParser(description="Genera un parrafo con varias voces.")
    p.add_argument("--voces", default=",".join(VOCES_POR_DEFECTO),
                   help="Lista separada por comas. Por defecto: " + ",".join(VOCES_POR_DEFECTO))
    p.add_argument("--texto", default=None,
                   help="Texto a leer. Por defecto, el parrafo del versus.")
    p.add_argument("--proyecto", default=None,
                   help="Proyecto del que sacar el texto, ej. SH_secretariat_p1.")
    p.add_argument("--escena", type=int, default=None,
                   help="Numero de escena a leer del manifest (requiere --proyecto).")
    p.add_argument("--salida", default=None, help="Carpeta destino.")
    # OJO: el default NO puede ser config.TTS_MODEL. argparse evalua los defaults
    # al construir el parser, o sea ANTES de saber en que canal estamos, asi que
    # ahi config todavia tiene los valores de TCC. Se resuelve despues.
    p.add_argument("--modelo", default=None, help="Modelo de TTS.")
    p.add_argument("--instrucciones", default=None,
                   help="Como debe hablar (solo en modelos que lo soporten).")
    p.add_argument("--velocidad", type=float, default=1.0, help="Velocidad (0.25-4.0).")
    args = p.parse_args()

    # --- de donde sale el texto -----------------------------------------
    if args.escena is not None and not args.proyecto:
        sys.exit("ERROR: --escena necesita --proyecto.")
    if args.escena is not None and args.texto:
        sys.exit("ERROR: --texto y --escena son excluyentes. Elige uno.")

    resolver_canal(args.proyecto)
    modelo = args.modelo or config.TTS_MODEL

    if args.escena is not None:
        texto = texto_de_escena(args.proyecto, args.escena)
        origen = f"escena {args.escena} de {args.proyecto}"
    else:
        texto = args.texto or TEXTO_POR_DEFECTO
        origen = "texto propio" if args.texto else "parrafo por defecto (versus)"

    load_dotenv(config.ENV_FILE)
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print(f"Falta OPENAI_API_KEY en {config.ENV_FILE}.")
        return 1
    client = OpenAI(api_key=api_key)

    # La carpeta sale del canal resuelto, no fija a sabermetria-hipica: si un dia
    # se prueban voces para TCC, las pruebas no tienen por que aterrizar en la
    # carpeta del otro canal.
    destino = Path(args.salida) if args.salida else (
        config.CHANNEL_DIR / "pruebas_voz"
    )
    destino.mkdir(parents=True, exist_ok=True)

    voces = [v.strip() for v in args.voces.split(",") if v.strip()]

    print(f"Modelo : {modelo}")
    print(f"Origen : {origen}")
    print(f"Texto  : {len(texto.split())} palabras, {len(texto)} caracteres")
    print(f'         "{texto[:90]}..."')
    if args.instrucciones:
        print(f"Instrucciones: {args.instrucciones}")
    print(f"Destino: {destino}\n")

    # 'speed' solo va donde existe; en los demas modelos el ritmo se pide en
    # prosa con --instrucciones. Se avisa en vez de tragarselo en silencio: si
    # alguien pide velocidad 1.3 y no pasa nada, tiene que enterarse.
    usa_speed = modelo in MODELOS_CON_SPEED
    if not usa_speed and args.velocidad != 1.0:
        print(f"[AVISO] '{modelo}' no acepta 'speed'; se ignora --velocidad "
              f"{args.velocidad}. Pide el ritmo con --instrucciones.\n")
    if args.instrucciones and usa_speed:
        print(f"[AVISO] '{modelo}' no acepta 'instructions'; se ignora "
              f"--instrucciones.\n")

    # El nombre del archivo lleva modelo y escena porque la carpeta de pruebas es
    # la misma siempre: sin eso, probar nova en dos modelos distintos sobrescribe
    # la primera prueba con la segunda y se comparan dos archivos que son el mismo.
    etiqueta = modelo.replace(".", "")
    if args.escena is not None:
        etiqueta += f"_esc{args.escena:02d}"

    generados = []
    for voz in voces:
        salida = destino / f"voz_{voz}_{etiqueta}.mp3"
        print(f"  {voz:<8} generando...", end=" ", flush=True)
        try:
            extra = {}
            if usa_speed:
                extra["speed"] = args.velocidad
            elif args.instrucciones:
                extra["instructions"] = args.instrucciones
            with client.audio.speech.with_streaming_response.create(
                model=modelo, voice=voz, input=texto,
                response_format="mp3", **extra,
            ) as respuesta:
                respuesta.stream_to_file(salida)
            print(f"OK  ->  {salida.name}")
            generados.append(salida)
        except Exception as e:
            print(f"FALLO: {e}")

    if not generados:
        print("\nNo se genero ningun audio.")
        return 1

    print("\n" + "=" * 66)
    print("Escuchalos seguidos y con auriculares. Que buscar, por orden:")
    print()
    print("  1. Los nombres propios. Si 'Keeneland', 'Thoroughbred' o 'Terlingua'")
    print("     suenan mal, descartala ahi mismo: van a aparecer en todos los videos.")
    print("  2. El acento. Estas voces son anglosajonas hablando espanol. Decide si")
    print("     te molesta AHORA, no despues de generar doce minutos.")
    print("  3. La autoridad. El guion afirma cosas incomodas y corrige al mercado.")
    print("     Necesita una voz que sostenga eso sin sonar arrogante.")
    print("  4. El cambio de ritmo en 'A la derecha, Terlingua'. Ahi se ve si la voz")
    print("     tiene matiz o lee todo con la misma cadencia.")
    print()
    print("Cuando elijas, ponla en channels/sabermetria-hipica/canal.json -> voz.nombre")
    print("=" * 66)

    print()
    print("-" * 70)
    print("PRUEBAS EN:")
    for g in generados:
        print(f"  {g.resolve()}")
    print("-" * 70)
    return 0


if __name__ == "__main__":
    sys.exit(main())
