import os
import re
from datetime import datetime, timedelta


def procesar_carpetas(root):
    resumen = {}
    problemas = {}
    horas_bus = {}
    dias_semana = {}

    # Patrón para extraer número de bus y fecha de la carpeta
    patron_carpeta = re.compile(r'(\d+)-(\d{2})-(\d{2})-(\d{4})')
    # Patrón para extraer fecha y hora del archivo
    patron_archivo = re.compile(r'SensorData_(\d{4})_(\d{2})_(\d{2})_(\d{2})\.txt')

    # Recorrer todas las subcarpetas en el directorio root
    for nombre_carpeta in os.listdir(root):
        match_carpeta = patron_carpeta.match(nombre_carpeta)
        if not match_carpeta:
            continue

        numero_bus, dia, mes, ano = match_carpeta.groups()
        fecha_carpeta = f"{ano}-{mes}-{dia}"
        ruta_carpeta = os.path.join(root, nombre_carpeta)

        if not os.path.isdir(ruta_carpeta):
            continue

        hora_inicio = None
        hora_fin = None
        horas_totales = 0
        hay_archivos = False
        fecha_no_coincidente = False

        # Determinar el día de la semana y la semana del año
        fecha_carpeta_obj = datetime.strptime(fecha_carpeta, "%Y-%m-%d")
        numero_semana = fecha_carpeta_obj.strftime("%U")  # Número de semana del año
        inicio_semana = (fecha_carpeta_obj - timedelta(days=fecha_carpeta_obj.weekday())).strftime("%Y-%m-%d")
        fin_semana = (fecha_carpeta_obj + timedelta(days=(6 - fecha_carpeta_obj.weekday()))).strftime("%Y-%m-%d")
        clave_semana = f"Semana {numero_semana} ({inicio_semana} a {fin_semana})"

        # Agregar día de la semana a dias_semana
        if numero_bus not in dias_semana:
            dias_semana[numero_bus] = {}
        if clave_semana not in dias_semana[numero_bus]:
            dias_semana[numero_bus][clave_semana] = set()
        dias_semana[numero_bus][clave_semana].add(fecha_carpeta_obj.strftime("%A"))

        # Recorrer todos los archivos en la subcarpeta
        for nombre_archivo in os.listdir(ruta_carpeta):
            match_archivo = patron_archivo.match(nombre_archivo)
            if match_archivo:
                hay_archivos = True
                ano_archivo, mes_archivo, dia_archivo, hora_archivo = match_archivo.groups()
                fecha_archivo = f"{ano_archivo}-{mes_archivo}-{dia_archivo}"

                if fecha_archivo == fecha_carpeta:
                    fecha_hora_archivo = datetime.strptime(f"{fecha_archivo} {hora_archivo}", '%Y-%m-%d %H')

                    if hora_inicio is None or fecha_hora_archivo < hora_inicio:
                        hora_inicio = fecha_hora_archivo
                    if hora_fin is None or fecha_hora_archivo > hora_fin:
                        hora_fin = fecha_hora_archivo
                else:
                    fecha_no_coincidente = True
                    if nombre_carpeta not in problemas:
                        problemas[nombre_carpeta] = "Fecha no coincidente"

        if hora_inicio and hora_fin:
            horas_totales = (hora_fin - hora_inicio).seconds / 3600 + 1  # sumar 1 para incluir la última hora

        if not hay_archivos:
            estado = "No hay archivos TXT"
            problemas[nombre_carpeta] = "No hay archivos TXT"
        elif fecha_no_coincidente:
            estado = "Archivos TXT con fecha no coincidente"
        else:
            estado = "Archivos TXT correctos"

        # Agregar resumen de la carpeta actual
        resumen[nombre_carpeta] = {
            'hora_inicio': hora_inicio.strftime('%Y-%m-%d %H:%M:%S') if hora_inicio else 'N/A',
            'hora_fin': hora_fin.strftime('%Y-%m-%d %H:%M:%S') if hora_fin else 'N/A',
            'horas_totales': horas_totales,
            'estado': estado
        }

        # Agregar las horas al bus correspondiente
        if numero_bus not in horas_bus:
            horas_bus[numero_bus] = 0
        horas_bus[numero_bus] += horas_totales

    return resumen, problemas, horas_bus, dias_semana


def escribir_resumen_a_archivo(root, resumen, problemas, horas_bus, dias_semana):
    ruta_resumen = os.path.join(root, "resumen.txt")
    with open(ruta_resumen, "w") as archivo_resumen:
        for carpeta, info in resumen.items():
            archivo_resumen.write(f"Carpeta: {carpeta}\n")
            archivo_resumen.write(f"  Hora de inicio: {info['hora_inicio']}\n")
            archivo_resumen.write(f"  Hora de fin: {info['hora_fin']}\n")
            archivo_resumen.write(f"  Total de horas: {info['horas_totales']:.2f}\n")
            archivo_resumen.write(f"  Estado: {info['estado']}\n\n")

        archivo_resumen.write("Resumen de problemas:\n")
        archivo_resumen.write(f"  Total de archivos no coincidentes o faltantes: {len(problemas)}\n")
        for carpeta, problema in problemas.items():
            archivo_resumen.write(f"  - {carpeta}: {problema}\n")

        archivo_resumen.write("\nResumen de horas por ID de bus:\n")
        for bus, horas in horas_bus.items():
            archivo_resumen.write(f"  - Bus {bus}: {horas:.2f} horas\n")

        archivo_resumen.write("\nResumen de días de la semana por semana y por ID de bus:\n")
        for numero_bus, semanas in dias_semana.items():
            archivo_resumen.write(f"ID de bus: {numero_bus}\n")
            for clave_semana, dias in semanas.items():
                lista_dias = ", ".join(sorted(dias))
                archivo_resumen.write(f"  - {clave_semana}: {lista_dias}\n")


def imprimir_resumen(resumen, problemas, horas_bus, dias_semana):
    for carpeta, info in resumen.items():
        print(f"Carpeta: {carpeta}")
        print(f"  Hora de inicio: {info['hora_inicio']}")
        print(f"  Hora de fin: {info['hora_fin']}")
        print(f"  Total de horas: {info['horas_totales']:.2f}")
        print(f"  Estado: {info['estado']}\n")

    print("Resumen de problemas:")
    print(f"  Total de archivos no coincidentes o faltantes: {len(problemas)}")
    for carpeta, problema in problemas.items():
        print(f"  - {carpeta}: {problema}")

    print("\nResumen de horas por ID de bus:")
    for bus, horas in horas_bus.items():
        print(f"  - Bus {bus}: {horas:.2f} horas")

    print("\nResumen de días de la semana por semana y por ID de bus:")
    for numero_bus, semanas in dias_semana.items():
        print(f"ID de bus: {numero_bus}")
        for clave_semana, dias in semanas.items():
            lista_dias = ", ".join(sorted(dias))
            print(f"  - {clave_semana}: {lista_dias}")


if __name__ == "__main__":
    ruta_root = input("Introduce la ruta del directorio raíz: ")
    resumen, problemas, horas_bus, dias_semana = procesar_carpetas(ruta_root)
    imprimir_resumen(resumen, problemas, horas_bus, dias_semana)
    escribir_resumen_a_archivo(ruta_root, resumen, problemas, horas_bus, dias_semana)
