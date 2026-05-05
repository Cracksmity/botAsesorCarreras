"""Custom actions del bot de orientación vocacional.

Este módulo implementa la lógica de recomendación: a partir de las respuestas
del usuario al cuestionario (siete dimensiones de interés), calcula un puntaje
ponderado por carrera y devuelve la mejor coincidencia junto con dos
alternativas cercanas.

El algoritmo es una suma ponderada simple por dos motivos:
1. Es trivial de auditar y de extender (basta con tocar `CAREER_WEIGHTS`).
2. Para un boilerplate didáctico es más valioso que el alumno entienda
   el flujo Rasa <-> custom action que un modelo ML opaco.
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

from rasa_sdk import Action, Tracker
from rasa_sdk.events import EventType, SlotSet
from rasa_sdk.executor import CollectingDispatcher


# ---------------------------------------------------------------------------
# Configuración del modelo de recomendación
# ---------------------------------------------------------------------------

# Dimensiones de interés evaluadas por el cuestionario.
# El orden refleja el orden de las preguntas en el form `cuestionario_form`.
INTEREST_DIMENSIONS: Tuple[str, ...] = (
    "matematicas",
    "ayudar",
    "arte",
    "tecnologia",
    "ciencias",
    "negocios",
    "creatividad",
)

# Mapping slot -> dimensión.
SLOT_TO_DIMENSION: Dict[str, str] = {
    "q_matematicas": "matematicas",
    "q_ayudar": "ayudar",
    "q_arte": "arte",
    "q_tecnologia": "tecnologia",
    "q_ciencias": "ciencias",
    "q_negocios": "negocios",
    "q_creatividad": "creatividad",
}

# Pesos por carrera (0 = irrelevante, 3 = central).
# Cada fila debe cubrir todas las dimensiones de INTEREST_DIMENSIONS.
CAREER_WEIGHTS: Dict[str, Dict[str, int]] = {
    "Ingeniería de Software": {
        "matematicas": 3, "tecnologia": 3, "creatividad": 2,
        "ciencias": 2, "ayudar": 1, "arte": 1, "negocios": 1,
    },
    "Medicina": {
        "ciencias": 3, "ayudar": 3, "matematicas": 1,
        "tecnologia": 1, "creatividad": 1, "arte": 0, "negocios": 1,
    },
    "Diseño Gráfico": {
        "arte": 3, "creatividad": 3, "tecnologia": 2,
        "ayudar": 1, "negocios": 1, "matematicas": 0, "ciencias": 0,
    },
    "Psicología": {
        "ayudar": 3, "ciencias": 2, "creatividad": 2,
        "arte": 1, "matematicas": 1, "negocios": 1, "tecnologia": 0,
    },
    "Administración de Empresas": {
        "negocios": 3, "matematicas": 2, "ayudar": 2,
        "tecnologia": 1, "creatividad": 1, "arte": 0, "ciencias": 0,
    },
    "Arquitectura": {
        "arte": 3, "creatividad": 3, "matematicas": 2,
        "tecnologia": 2, "ciencias": 1, "negocios": 1, "ayudar": 0,
    },
}

# Multiplicador asociado a cada respuesta del usuario.
# "tal_vez" cuenta como medio voto para no penalizar la indecisión.
ANSWER_MULT: Dict[str, float] = {
    "si": 1.0,
    "tal_vez": 0.5,
    "no": 0.0,
}


# ---------------------------------------------------------------------------
# Helpers puros (testeables sin Rasa)
# ---------------------------------------------------------------------------

def _normalize_answer(raw: Any) -> str:
    """Normaliza el valor del slot a una clave de ANSWER_MULT.

    Tolerante a None, mayúsculas y a las variantes "sí"/"si".
    """
    if raw is None:
        return "no"
    value = str(raw).strip().lower().replace("í", "i")
    if value in ANSWER_MULT:
        return value
    if value in {"yes", "y", "true"}:
        return "si"
    if value in {"maybe", "tal vez"}:
        return "tal_vez"
    return "no"


def _compute_scores(answers: Dict[str, str]) -> List[Tuple[str, float]]:
    """Devuelve la lista de carreras ordenada por puntaje descendente.

    Args:
        answers: dict dimensión -> respuesta normalizada ("si"/"no"/"tal_vez").

    Returns:
        Lista de tuplas (carrera, puntaje) ordenadas de mayor a menor.
    """
    scores: List[Tuple[str, float]] = []
    for career, weights in CAREER_WEIGHTS.items():
        total = 0.0
        for dim in INTEREST_DIMENSIONS:
            weight = weights.get(dim, 0)
            mult = ANSWER_MULT[answers.get(dim, "no")]
            total += weight * mult
        scores.append((career, round(total, 2)))
    scores.sort(key=lambda pair: pair[1], reverse=True)
    return scores


def _format_message(scores: List[Tuple[str, float]]) -> str:
    """Construye el mensaje de recomendación a partir del ranking."""
    if not scores:
        return (
            "No pude calcular una recomendación con la información disponible. "
            "¿Quieres intentar el cuestionario de nuevo?"
        )

    best_career, best_score = scores[0]
    runners_up = scores[1:3]

    # Si todos los puntajes son 0, el usuario respondió "no" a todo.
    if best_score == 0:
        return (
            "Parece que ninguna de las áreas que evaluamos te entusiasma. "
            "Te sugiero hablar con un orientador humano para explorar otras "
            "opciones que aquí no cubrimos."
        )

    runner_up_text = ", ".join(
        f"{name} ({score} pts)" for name, score in runners_up
    )

    return (
        f"Según tus respuestas, la carrera que mejor encaja contigo es "
        f"**{best_career}** con un puntaje de {best_score}.\n"
        f"También podrías considerar: {runner_up_text}.\n\n"
        "Recuerda que esta es una recomendación orientativa: "
        "lo ideal es complementarla investigando los planes de estudio."
    )


# ---------------------------------------------------------------------------
# Custom Action
# ---------------------------------------------------------------------------

class ActionRecommendCareer(Action):
    """Calcula y comunica la recomendación de carrera al usuario."""

    def name(self) -> str:
        return "action_recommend_career"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[str, Any],
    ) -> List[EventType]:
        answers: Dict[str, str] = {
            dimension: _normalize_answer(tracker.get_slot(slot_name))
            for slot_name, dimension in SLOT_TO_DIMENSION.items()
        }

        scores = _compute_scores(answers)
        message = _format_message(scores)

        dispatcher.utter_message(text=message)

        best_career = scores[0][0] if scores else None
        return [SlotSet("recomendacion", best_career)]
