import time
import random
import requests

# Definições das câmeras no galpão
CAMERA_WIDTH = 1920
CAMERA_HEIGHT = 1300
CAMERAS = [
    (0, 0),        # Câmera 1
    (1920, 0),     # Câmera 2
    (3840, 0),     # Câmera 3
    (5760, 0)      # Câmera 4
]

def gerar_animais_simulados(num_animais=5, camera_pos=(0, 0), camera_idx=0):
    animais = []
    for _ in range(num_animais):
        animal_id = random.randint(0, 10)
        pos_x_rel = random.uniform(0, CAMERA_WIDTH)
        pos_y_rel = random.uniform(0, CAMERA_HEIGHT)
        inclinacao = random.uniform(0, 90)
        animais.append({
            'id': animal_id,
            'position': [pos_x_rel, pos_y_rel],
            'angle': inclinacao,
            'timestamp': time.time(),
            'camera_idx': camera_idx
        })
    return animais

def gerar_sequencia_cameras(total_frames):
    ida = list(range(len(CAMERAS)))         # [0, 1, 2, 3]
    volta = ida[::-1][1:-1]                 # [2, 1]
    sequencia = []  
    while len(sequencia) < total_frames:
        sequencia += ida + volta
    return sequencia[:total_frames]

def simular_envio_animais(qtd_frames=10, intervalo=5):
    time.sleep(2)
    sequencia_cameras = gerar_sequencia_cameras(qtd_frames)
    for frame in range(qtd_frames):
        camera_idx = sequencia_cameras[frame]
        camera_pos = CAMERAS[camera_idx]
        print(f"\n[Agente] Frame {frame+1} - Posição do robô {camera_idx+1} - Posição câmera {camera_pos} ----------------------------")
        num_animais = random.randint(3, 7)
        animais = gerar_animais_simulados(num_animais, camera_pos, camera_idx)
        for animal in animais:
            try:
                resp = requests.post('http://localhost:5000/enviar_animal', json=animal)
                if resp.status_code == 200:
                    resultado = resp.json()
                    print(f"Animal {resultado['id']} - Estado: {resultado['state']} - Deslocamento: {resultado['displacement_px']:.2f}px ({resultado['displacement_cm']:.2f}cm) - CameraIdx: {resultado.get('camera_idx', 'N/A')} - Tempo acumulado estado: {resultado.get('tempo_total_estado_segundos', 0):.2f}s")
                else:
                    print(f"Erro ao enviar animal {animal['id']}: {resp.text}")
            except Exception as e:
                print(f"Erro de conexão: {e}")
        time.sleep(intervalo)

if __name__ == '__main__':
    simular_envio_animais(qtd_frames=20, intervalo=5)
