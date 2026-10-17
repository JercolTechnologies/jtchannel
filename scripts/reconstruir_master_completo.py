# -*- coding: utf-8 -*-
"""
Reconstrucción integral del máster con la sanitización v2 aplicada en todos los tramos:
1. editar_tramo_01.py -> montar_tramo_01.py
2. editar_tramo_02.py -> montar_tramo_02.py
3. montar_tramo_03.py
4. editar_tramo_04.py -> montar_tramo_04.py
5. concatenar_master_final.py
6. mezclar_musica_master.py
"""

import subprocess
import sys
import time

PASOS = [
    ("Edición Tramo 01", ["python", "scripts/editar_tramo_01.py"]),
    ("Montaje Tramo 01 Sanitizado", ["python", "scripts/montar_tramo_01.py"]),
    ("Edición Tramo 02", ["python", "scripts/editar_tramo_02.py"]),
    ("Montaje Tramo 02 Sanitizado", ["python", "scripts/montar_tramo_02.py"]),
    ("Montaje Tramo 03 Sanitizado", ["python", "scripts/montar_tramo_03.py"]),
    ("Edición Tramo 04", ["python", "scripts/editar_tramo_04.py"]),
    ("Montaje Tramo 04 Sanitizado", ["python", "scripts/montar_tramo_04.py"]),
    ("Concatenación Master Final", ["python", "scripts/concatenar_master_final.py"]),
    ("Mezcla de Música & Normalización Final", ["python", "scripts/mezclar_musica_master.py"]),
]


def main():
    inicio_total = time.time()
    print("=" * 65)
    print(" RECONSTRUCCIÓN COMPLETA DEL MASTER CON SANITIZACIÓN V2")
    print("=" * 65)

    for i, (nombre, cmd) in enumerate(PASOS, 1):
        print(f"\n[{i}/{len(PASOS)}] {nombre}...")
        t0 = time.time()
        res = subprocess.run(cmd)
        if res.returncode != 0:
            print(f"\n[ERROR] Falló el paso: {nombre}")
            sys.exit(1)
        print(f"  -> Completado en {time.time() - t0:.1f} s")

    total_s = time.time() - inicio_total
    print("\n" + "=" * 65)
    print(f" [ÉXITO TOTAL] Master reconstruido y blindado en {total_s:.1f} s")
    print("=" * 65)


if __name__ == "__main__":
    main()
