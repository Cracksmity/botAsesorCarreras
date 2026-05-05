# Bot de Orientación Vocacional con Rasa 3.x

Asistente conversacional en español que entrevista al usuario con 7 preguntas
sobre sus intereses y recomienda una de 6 carreras universitarias mediante
una acción personalizada con un algoritmo de puntaje ponderado.

## Estructura del proyecto

```
.
├── actions/
│   ├── __init__.py
│   └── actions.py            # ActionRecommendCareer + algoritmo de scoring
├── data/
│   ├── nlu.yml               # Ejemplos de entrenamiento (intents, entidades, sinónimos)
│   ├── rules.yml             # Reglas (small talk + activación/envío del form)
│   └── stories.yml           # Historias para entrenar TEDPolicy
├── tests/
│   └── test_stories.yml      # Tests end-to-end (rasa test)
├── config.yml                # Pipeline NLU y políticas (en español)
├── credentials.yml           # Canales (REST habilitado por defecto)
├── domain.yml                # Intents, slots, form, responses, acciones
├── endpoints.yml             # URL del action server
├── requirements.txt
└── README.md
```

## Requisitos

- Python **3.8 - 3.10** (Rasa 3.6 no es compatible con 3.11+).
- pip y `venv`.
- Windows / PowerShell (los comandos abajo asumen ese entorno; los comandos
  de Rasa son idénticos en macOS/Linux).

## Instalación paso a paso

```powershell
# 1. Crear y activar entorno virtual
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 2. Actualizar pip e instalar dependencias
python -m pip install --upgrade pip
pip install -r requirements.txt

# 3. (Opcional) Verificar la instalación
rasa --version
```

> Si PowerShell bloquea la activación del venv, ejecuta una sola vez:
> `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`.

## Entrenar el modelo

```powershell
rasa train
```

Esto crea un archivo `models/<timestamp>.tar.gz` que combina NLU + Core.

## Probar el bot

Necesitas dos terminales abiertas simultáneamente:

**Terminal A — action server (custom actions en Python):**

```powershell
.\.venv\Scripts\Activate.ps1
rasa run actions
```

**Terminal B — chat interactivo:**

```powershell
.\.venv\Scripts\Activate.ps1
rasa shell
```

Para depurar políticas y NLU con detalle:

```powershell
rasa shell --debug
```

## Conversación de ejemplo

```
Tú:  hola
Bot: ¡Hola! Soy tu asistente de orientación vocacional...
Tú:  quiero orientación vocacional
Bot: Pregunta 1 de 7: ¿Disfrutas las matemáticas...?
Tú:  sí
Bot: Pregunta 2 de 7: ¿Te gusta ayudar y escuchar...?
...
Bot: Según tus respuestas, la carrera que mejor encaja contigo es
     **Ingeniería de Software** con un puntaje de 11.5...
```

## Ejecutar los tests

```powershell
rasa test
```

Esto evalúa NLU + las historias en `tests/test_stories.yml`.

## Cómo extender el bot

- **Agregar una carrera nueva**: añade una entrada a `CAREER_WEIGHTS` en
  [`actions/actions.py`](actions/actions.py). No es necesario tocar los slots.
- **Agregar una pregunta**:
  1. Añade un slot `q_<dimension>` en `domain.yml` (mismo patrón que los existentes).
  2. Añade el slot a `cuestionario_form.required_slots`.
  3. Añade `utter_ask_q_<dimension>` en `responses`.
  4. Añade la dimensión a `INTEREST_DIMENSIONS` y a `SLOT_TO_DIMENSION` en `actions.py`.
  5. Añade el peso en cada carrera de `CAREER_WEIGHTS`.
- **Cambiar idioma**: ajusta `language` en `config.yml` y reescribe los
  ejemplos en `data/nlu.yml` y las respuestas en `domain.yml`.

## Comandos útiles

| Acción | Comando |
|---|---|
| Entrenar | `rasa train` |
| Solo NLU | `rasa train nlu` |
| Solo Core | `rasa train core` |
| Chat | `rasa shell` |
| Action server | `rasa run actions` |
| Tests | `rasa test` |
| Validar archivos | `rasa data validate` |
| Visualizar historias | `rasa visualize` |
