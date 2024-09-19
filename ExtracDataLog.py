import argparse
import csv
import json
import os
import re
import shutil

from datetime import datetime

# Patrón para identificar el inicio de cada log, basado en la fecha/hora
LOG_PATTERN = re.compile(r'\[\d{4}/\d{2}/\d{2} \d{2}:\d{2}:\d{2}]')

# Constantes para los encabezados
COMMON_HEADERS = ["versionTrama", "idRegistro", "idOperador", "idVehiculo", "idRuta", "idConductor",
                  "fechaHoraLecturaDato", "fechaHoraEnvioDato", "tipoBus", "latitud", "longitud", "tipoTrama",
                  "tecnologiaMotor", "tramaRetransmitida", "tipoFreno", ]

HEADERS_SPECIFIC = {
    "P20": ["velocidadVehiculo", "aceleracionVehiculo"],
    "P60": ["temperaturaMotor", "presionAceiteMotor", "velocidadVehiculo", "aceleracionVehiculo",
            "revolucionesMotor", "estadoDesgasteFrenos", "kilometrosOdometro", "consumoCombustible",
            "nivelTanqueCombustible", "consumoEnergia", "regeneracionEnergia", "nivelRestanteEnergia",
            "porcentajeEnergiaGenerada", "temperaturaSts", "usoCpuSts", "memRamSts", "memDiscoSts",
            "temperaturaBaterias", "sentidoMarcha"],
    "EV1": ["codigoEvento", "peso", "temperaturaCabina", "estimacionOcupacionSuben",
            "estimacionOcupacionBajan", "estimacionOcupacionAbordo"],
    "EV2": ["codigoEvento", "estadoAperturaCierrePuertas"],
    "EV6": ["codigoEvento"],
    "EV7": ["codigoEvento"],
    "EV8": ["codigoEvento"],
    "EV12": ["codigoEvento"],
    "EV13": ["codigoEvento"],
    "EV14": ["codigoEvento"],
    "EV15": ["codigoEvento"],
    "EV16": ["codigoEvento"],
    "EV17": ["codigoEvento"],
    "EV18": ["codigoEvento"],
    "EV19": ["codigoEvento", "codigoComportamientoAnomalo"],
    "EV20": ["codigoEvento", "porcentajeCargaBaterias"],
    "EV21": ["codigoEvento", "porcentajeCargaBaterias"],
    "ALA1": ["codigoAlarma", "nivelAlarma", "aceleracionVehiculo"],
    "ALA2": ["codigoAlarma", "nivelAlarma", "aceleracionVehiculo"],
    "ALA3": ["codigoAlarma", "nivelAlarma", "velocidadVehiculo"],
    "ALA5": ["codigoAlarma", "nivelAlarma", "codigoCamara"],
    "ALA8": ["codigoAlarma", "nivelAlarma", "estadoCinturonSeguridad"],
    "ALA9": ["codigoAlarma", "nivelAlarma", "estadoInfoEntretenimiento"],
    "ALA10": ["codigoAlarma", "nivelAlarma", "estadoDesgasteFrenos"],
}


def extract_json_objects_from_logs(logs):
    json_objects = []
    start_positions = [match.start() for match in LOG_PATTERN.finditer(logs)]
    start_positions.append(len(logs))

    for i in range(len(start_positions) - 1):
        json_str = logs[start_positions[i]:start_positions[i + 1]]
        start_json = json_str.find('{')
        if start_json != -1:
            try:
                json_obj = json.loads(json_str[start_json:-2])
                json_objects.append(json_obj)
            except json.JSONDecodeError:
                json_str_fixed = json_str[start_json:] + '"}'
                try:
                    json_obj = json.loads(json_str_fixed)
                    json_objects.append(json_obj)
                except:
                    print(f"Error al decodificar JSON: - Fragmento: {json_str_fixed}")
                    pass

    return json_objects


def extract_json_objects_from_file(file_content):
    try:
        json_objects = json.loads(file_content)
        if isinstance(json_objects, list):
            return json_objects
        else:
            return [json_objects]
    except json.JSONDecodeError as e:
        print(f"Error al decodificar JSON: {str(e)}")
        return []


def format_date(date_str):
    if date_str:
        date_obj = datetime.strptime(date_str, '%d/%m/%Y %H:%M:%S.%f')
        return date_obj.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
    return ''


def extract_values(json_obj, headers):
    localizacion = json_obj.get('localizacionVehiculo', {})
    values = []
    for header in headers:
        if header in ['fechaHoraLecturaDato', 'fechaHoraEnvioDato']:
            values.append(format_date(json_obj.get(header, "")))
        elif header in ['latitud', 'longitud']:
            values.append(localizacion.get(header, ''))
        else:
            value = json_obj.get(header, None)
            if value is None and header in ['consumoCombustible', 'nivelTanqueCombustible', 'temperaturaMotor',
                                            'presionAceiteMotor', 'revolucionesMotor', 'estadoDesgasteFrenos',
                                            'kilometrosOdometro']:
                value = -1
            values.append(value)
    return values


def ensure_directory(path):
    """Crea la carpeta si no existe."""
    if not os.path.exists(path):
        os.makedirs(path)


def get_output_folder(base_path, bus_id, fecha):
    """Devuelve la ruta de salida en formato bus-dia-mes-año con meses y días de 2 dígitos."""
    fecha_obj = datetime.strptime(fecha, '%Y-%m-%d %H:%M:%S.%f')
    folder_name = f"{bus_id}-{fecha_obj.day:02d}-{fecha_obj.month:02d}-{fecha_obj.year}"
    folder_path = os.path.join(base_path, folder_name)
    ensure_directory(folder_path)
    return folder_path


def process_file(input_path, output_path):
    # Verifica si el archivo de entrada es JSON o un log regular
    is_json_file = input_path.lower().endswith('.json')

    with open(input_path, 'r', encoding='utf-16' if not is_json_file else 'utf-8') as file:
        content = file.read()

    # Procesa el archivo dependiendo de su tipo
    if is_json_file:
        json_objects = extract_json_objects_from_file(content)
    else:
        json_objects = extract_json_objects_from_logs(content)

    funciones_extraccion = {key: extract_values for key in HEADERS_SPECIFIC}

    # Copiar el archivo .log o .json al directorio de salida
    shutil.copy(input_path, output_path)

    for obj in json_objects:
        if is_json_file:
            # Para archivos JSON, los datos están dentro del campo "data"
            data = obj.get("data", {})
        else:
            # Para logs, los datos están en el nivel superior
            data = obj

        # Extraer idVehiculo (bus) y la fecha para crear la carpeta
        bus_id = data.get("idVehiculo", "desconocido")[-4:]
        fecha = format_date(data.get("fechaHoraLecturaDato", ""))

        # Crear la carpeta de salida basada en el bus y la fecha
        folder_path = get_output_folder(output_path, bus_id, fecha)

        tipo = data.get("codigoPeriodica") or data.get("codigoEvento") or data.get("codigoAlarma")
        if tipo in funciones_extraccion:
            headers = COMMON_HEADERS + HEADERS_SPECIFIC[tipo]

            # Abrir el archivo CSV para este bus/tipo
            csv_file_path = os.path.join(folder_path, f'{tipo}.csv')
            file_exists = os.path.isfile(csv_file_path)

            with open(csv_file_path, 'a', newline='') as csvfile:
                writer = csv.writer(csvfile)

                # Escribir el encabezado solo si el archivo es nuevo
                if not file_exists:
                    writer.writerow(headers)

                datos_ordenados = funciones_extraccion[tipo](data, headers)
                writer.writerow(datos_ordenados)
        else:
            print(f"Tipo desconocido: {tipo}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Procesa un archivo y guarda los resultados.")
    parser.add_argument('input_path', type=str, help='Ruta del archivo de entrada que se va a procesar')
    parser.add_argument('output_path', type=str, help='Ruta del archivo de salida donde se guardarán los resultados')
    args = parser.parse_args()

    process_file(args.input_path, args.output_path)
