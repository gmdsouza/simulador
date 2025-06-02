
# Sistema de Monitoramento Comportamental de Animais com Flask + Simulador

Este projeto consiste em um sistema para monitoramento automatizado de animais dentro de um galpão usando câmeras distribuídas ao longo do ambiente. Ele classifica o comportamento dos animais como `comendo` ou `andando`, armazena essas informações em arquivos CSV, e acumula o tempo gasto em cada estado.

O sistema é composto por dois módulos principais:

- `App.py`: um servidor Flask que processa e armazena os dados recebidos.
- `Simulador.py`: um script que simula o envio de dados de animais de forma automática, imitando um robô ou sistema de visão computacional.

## Estrutura do Projeto

```
├── App.py                  # Servidor Flask com lógica de monitoramento
├── Simulador.py            # Script que simula envio de dados de animais
├── simulacoes_animais/     # Pasta gerada automaticamente com CSVs e JSON de estado
│   ├── animal_<id>.csv     # Arquivo com histórico de posições e estados
│   └── tempo_acumulado.json # Tempo acumulado em cada estado por animal
```

## Como executar

### 1. Instale as dependências
```bash
pip install flask numpy requests
```

### 2. Inicie o servidor
```bash
python App.py
```

Ele ficará disponível em `http://localhost:5000`.

### 3. Execute o simulador (em outro terminal)
```bash
python Simulador.py
```

O simulador envia dados a cada 5 segundos por padrão, simulando 20 ciclos de movimentação entre 4 câmeras.

## O que o sistema faz

### App.py — Servidor Flask

- `POST /enviar_animal`: recebe dados JSON com:
  ```json
  {
    "id": 1,
    "position": [x, y],
    "angle": 27.0,
    "timestamp": 1717293200.0,
    "camera_idx": 1
  }
  ```

- O servidor:
  - Calcula o deslocamento do animal.
  - Verifica se está:
    - Parado: deslocamento < 5px
    - Na região do cocho: y ≤ 1200
    - Inclinado para comer: ângulo < 30°
  - Classifica como:
    - `comendo`: se todos os critérios forem verdadeiros
    - `andando`: caso contrário
  - Atualiza:
    - Um arquivo CSV com dados por animal
    - Um JSON com o tempo total acumulado por estado

- `GET /relatorio_tempo_acumulado`: retorna um relatório formatado:
  ```json
  {
    "1": {
      "comendo": "0h 2m 15s",
      "andando": "0h 0m 35s"
    }
  }
  ```

### Simulador.py — Envio automático de dados

- Gera aleatoriamente:
  - Quantidade de animais (3 a 7 por câmera)
  - Posições `(x, y)` dentro da câmera
  - Ângulo da cabeça (0° a 90°)
- Percorre uma sequência de câmeras de forma realista (ida e volta).
- A cada ciclo (`frame`), envia os dados dos animais para o servidor via `POST`.

Exemplo de saída no console:
```
[Agente] Frame 4 - Posição do robô 3 - Posição câmera (3840, 0)
Animal 5 - Estado: comendo - Deslocamento: 3.21px (1.00cm) - CameraIdx: 2 - Tempo acumulado estado: 23.21s
```

## Lógica de Classificação

Um animal será classificado como comendo se:
- Deslocamento for menor que 5px
- Coordenada y estiver dentro da região do cocho (≤ 1200)
- Ângulo da cabeça for menor que 30°

Caso contrário, será considerado andando.

## Parâmetros importantes

| Parâmetro             | Valor      | Descrição                                         |
|-----------------------|------------|---------------------------------------------------|
| `Y_COCHO`             | `1200`     | Limite vertical da região do cocho               |
| `DESLOCAMENTO_LIMITE`| `5`         | Limite em pixels para considerar o animal parado |
| `PIXEL_PARA_CM`       | `0.3125`   | Conversão de pixel para centímetros              |
| `FRAME_WIDTH`         | `1920`     | Largura da imagem de cada câmera                 |

## Requisitos

- Python 3.7+
- Flask
- NumPy
- Requests (para o simulador)

## Observações

- A pasta `simulacoes_animais` será criada automaticamente.
- O sistema é útil para análise comportamental, zootecnia ou monitoramento automatizado de rebanhos.
- Pode ser integrado com sistemas reais de detecção via câmeras no futuro.

## Autor

Desenvolvido para fins de simulação e monitoramento comportamental com múltiplas câmeras e processamento contínuo.
