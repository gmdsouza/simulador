from flask import Flask, request, jsonify
import os
import csv
import numpy as np
import datetime
import json

app = Flask(__name__)

FOLDER = 'simulacoes_animais'
Y_COCHO = 1200
DESLOCAMENTO_LIMITE = 5  # pixels
FRAME_WIDTH = 1920       # largura da imagem de cada câmera
PIXEL_PARA_CM = 0.3125   # 1 pixel = 0.3125 cm (ajuste conforme seu galpão)

TEMPO_ACUMULADO_FILE = os.path.join(FOLDER, 'tempo_acumulado.json')

def carregar_tempo_acumulado():
    if os.path.exists(TEMPO_ACUMULADO_FILE):
        with open(TEMPO_ACUMULADO_FILE, 'r') as f:
            return json.load(f)
    return {}

def salvar_tempo_acumulado(data):
    os.makedirs(FOLDER, exist_ok=True)
    with open(TEMPO_ACUMULADO_FILE, 'w') as f:
        json.dump(data, f)

def ler_ultimo_dado(animal_id):
    filename = os.path.join(FOLDER, f'animal_{animal_id}.csv')
    if not os.path.exists(filename):
        return None
    with open(filename, 'r') as f:
        linhas = f.readlines()
        if len(linhas) < 2:
            return None
        ultima_linha = linhas[-1].strip().split(',')
        try:
            return {
                'timestamp': datetime.datetime.strptime(ultima_linha[0], '%Y-%m-%d %H:%M:%S').timestamp(),
                'position': (float(ultima_linha[1]), float(ultima_linha[2])),
                'angle': float(ultima_linha[3]),
                'state': ultima_linha[4],
                'camera_idx': int(ultima_linha[5]),
                'displacement_px': float(ultima_linha[6]),
                'displacement_cm': float(ultima_linha[7]) if len(ultima_linha) > 7 else 0.0
            }
        except (ValueError, IndexError):
            return None

def calcular_deslocamento(atual, anterior):
    if anterior is None:
        return 0
    x1, y1 = anterior['position']
    x2, y2 = atual['position']
    idx1 = anterior['camera_idx']
    idx2 = atual['camera_idx']
    if idx1 == idx2:
        return np.sqrt((x2 - x1)**2 + (y2 - y1)**2)
    else:
        x1_global = x1 + (idx1 * FRAME_WIDTH)
        x2_global = x2 + (idx2 * FRAME_WIDTH)
        return np.sqrt((x2_global - x1_global)**2 + (y2 - y1)**2)

def salvar_dado(animal):
    filename = os.path.join(FOLDER, f'animal_{animal["id"]}.csv')
    os.makedirs(FOLDER, exist_ok=True)
    file_exists = os.path.exists(filename)

    last_data = ler_ultimo_dado(animal['id'])
    deslocamento_px = calcular_deslocamento(animal, last_data)
    deslocamento_cm = deslocamento_px * PIXEL_PARA_CM

    parado = deslocamento_px < DESLOCAMENTO_LIMITE
    dentro_cocho = animal['position'][1] <= Y_COCHO
    inclina_ok = animal['angle'] < 30 # mudar angulação para 45
    estado = 'comendo' if parado and dentro_cocho and inclina_ok else 'andando'

    timestamp_atual = animal['timestamp']
    timestamp_legivel = datetime.datetime.fromtimestamp(timestamp_atual).strftime('%Y-%m-%d %H:%M:%S')

    tempo_acumulado = carregar_tempo_acumulado()

    if str(animal['id']) not in tempo_acumulado:
        tempo_acumulado[str(animal['id'])] = {}
    if estado not in tempo_acumulado[str(animal['id'])]:
        tempo_acumulado[str(animal['id'])][estado] = {
            'ultimo_timestamp': timestamp_atual,
            'tempo_total': 0.0
        }

    ultimo_ts_estado = tempo_acumulado[str(animal['id'])][estado]['ultimo_timestamp']
    tempo_total_estado = tempo_acumulado[str(animal['id'])][estado]['tempo_total']

    if timestamp_atual > ultimo_ts_estado:
        diferenca = timestamp_atual - ultimo_ts_estado
        tempo_total_estado += diferenca
        ultimo_ts_estado = timestamp_atual

    tempo_acumulado[str(animal['id'])][estado]['ultimo_timestamp'] = ultimo_ts_estado
    tempo_acumulado[str(animal['id'])][estado]['tempo_total'] = tempo_total_estado

    salvar_tempo_acumulado(tempo_acumulado)

    x = round(animal['position'][0], 2)
    y = round(animal['position'][1], 2)
    angulo = round(animal['angle'], 1)
    deslocamento_px = round(deslocamento_px, 2)
    deslocamento_cm = round(deslocamento_cm, 2)
    camera_idx = animal.get('camera_ifile_existsdx', -1)

    tempo_total_legivel = round(tempo_total_estado, 2)

    with open(filename, mode='a', newline='') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow([
                'timestamp', 'pos_x', 'pos_y', 'angle',
                'state', 'camera_idx',
                'displacement_px', 'displacement_cm',
                'tempo_total_estado_segundos'
            ])
        writer.writerow([
            timestamp_legivel,
            x,
            y,
            angulo,
            estado,
            camera_idx,
            deslocamento_px,
            deslocamento_cm,
            tempo_total_legivel
        ])

    return {
        'id': animal['id'],
        'state': estado,
        'displacement_px': deslocamento_px,
        'displacement_cm': deslocamento_cm,
        'camera_idx': camera_idx,
        'tempo_total_estado_segundos': tempo_total_legivel
    }

@app.route('/enviar_animal', methods=['POST'])
def receber_animal():
    data = request.get_json()
    if not all(k in data for k in ('id', 'position', 'angle', 'timestamp', 'camera_idx')):
        return jsonify({'error': 'Dados inválidos.'}), 400
    resultado = salvar_dado(data)
    return jsonify(resultado), 200

@app.route('/relatorio_tempo_acumulado', methods=['GET'])
def relatorio_tempo_acumulado():
    dados = carregar_tempo_acumulado()

    def formatar_tempo(segundos):
        h = int(segundos // 3600)
        m = int((segundos % 3600) // 60)
        s = int(segundos % 60)
        return f"{h}h {m}m {s}s"

    relatorio_formatado = {}
    for animal_id, estados in dados.items():
        relatorio_formatado[animal_id] = {}
        for estado, valores in estados.items():
            relatorio_formatado[animal_id][estado] = formatar_tempo(valores['tempo_total'])

    return jsonify(relatorio_formatado), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
