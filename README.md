# Bot de Orientación Vocacional con Rasa 3.x

Asistente conversacional en español con **dos etapas**: perfil general
(macro-área + tipo de actividad) y, si el usuario elige STEM, dos preguntas
adicionales (preferencia y estilo de trabajo). La recomendación final la
calcula `action_recommend_career` según tablas declarativas en Python.

## Estructura del proyecto

```
.
├── actions/
│   ├── __init__.py
│   └── actions.py            # ValidateFormularioVocacional + ActionRecommendCareer
├── data/
│   ├── nlu.yml               # Ejemplos de entrenamiento (intents en español)
│   ├── rules.yml             # Reglas (small talk + activación/envío del form)
│   └── stories.yml           # Historias para entrenar TEDPolicy
├── tests/
│   └── test_stories.yml      # Tests end-to-end (rasa test)
├── config.yml                # Pipeline NLU y políticas (en español)
├── credentials.yml           # Canales (REST habilitado por defecto)
├── domain.yml                # Intents, slots, formulario_vocacional, responses
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
Bot: Pregunta 1 de 2 (perfil general): ¿En qué gran área te ves más? ...
Tú:  lo mío es STEM
Bot: Pregunta 2 de 2 (perfil general): ¿Qué tipo de actividades te atraen más? ...
Tú:  prefiero actividades analíticas
Bot: Pregunta extra (STEM): entre estas tres, ¿cuál te representa más? ...
Tú:  prefiero matemáticas y modelado
Bot: Última pregunta (STEM): ¿prefieres un trabajo más abstracto o más aplicado? ...
Tú:  prefiero trabajo abstracto
Bot: Según tu perfil STEM, una carrera que encaja bien es **Ciencia de Datos**...
```

## Ejecutar los tests

```powershell
rasa test
```

Esto evalúa NLU + las historias en `tests/test_stories.yml`.

## Cómo extender el bot

- **Ajustar recomendaciones STEM**: edita `STEM_MATRIX` en
  [`actions/actions.py`](actions/actions.py).
- **Ajustar caminos no STEM**: edita `_recommend_general` en el mismo archivo.
- **Nueva macro-área con ramificación**: añade valor al slot `macro_area` en
  `domain.yml`, intents + ejemplos en `data/nlu.yml`, mapeos `from_intent` y
  amplía `required_slots` en `ValidateFormularioVocacional` si hace falta un
  bloque extra de preguntas.
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
