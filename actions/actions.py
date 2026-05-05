"""Acciones personalizadas: formulario vocacional en dos etapas y recomendación.

- `ValidateFormularioVocacional`: añade slots STEM solo si `macro_area` es stem.
- `ActionRecommendCareer`: reglas declarativas para STEM y caminos generales.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Text, Tuple

from rasa_sdk import Action, Tracker
from rasa_sdk.events import EventType, SlotSet
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.forms import FormValidationAction
from rasa_sdk.types import DomainDict

# ---------------------------------------------------------------------------
# Matriz STEM: (stem_preferencia, stem_estilo_trabajo) -> carrera
# ---------------------------------------------------------------------------

STEM_MATRIX: Dict[Tuple[str, str], str] = {
    ("matematicas", "abstracto"): "Ciencia de Datos",
    ("matematicas", "aplicado"): "Ingeniería Civil",
    ("programacion", "abstracto"): "Ciencia de Datos",
    ("programacion", "aplicado"): "Ingeniería Informática",
    ("construccion_fisica", "abstracto"): "Ingeniería Civil",
    ("construccion_fisica", "aplicado"): "Mecatrónica",
}


def _recommend_stem(
    preferencia: Optional[str],
    estilo: Optional[str],
) -> Tuple[Optional[str], str]:
    """Devuelve (carrera, mensaje) para rama STEM. carrera None si faltan datos."""
    if not preferencia or not estilo:
        msg = (
            "No tengo suficiente información para una recomendación STEM precisa. "
            "Te sugiero repetir el cuestionario o hablar con un orientador vocacional."
        )
        return None, msg

    key = (preferencia, estilo)
    career = STEM_MATRIX.get(key)
    if not career:
        msg = (
            "Con esas combinaciones no tengo una fila en la tabla de recomendaciones. "
            "Un orientador humano podrá afinar mejor tu perfil."
        )
        return None, msg

    msg = (
        f"Según tu perfil STEM, una carrera que encaja bien es **{career}**.\n\n"
        "Recuerda revisar planes de estudio y salidas laborales en tu país o universidad; "
        "esto es orientación, no una decisión final."
    )
    return career, msg


def _recommend_general(
    macro_area: Optional[str],
    tipo_actividad: Optional[str],
) -> Tuple[Optional[str], str]:
    """Carreras amplias fuera de STEM según macro_area y tipo_actividad."""
    if macro_area == "salud":
        career = "Medicina"
        msg = (
            f"Por tu interés en **salud**, una vía clásica a explorar es **{career}** "
            "(también existen carreras afines como enfermería, odontología o nutrición, "
            "según tus preferencias).\n\n"
            "Complementa esta idea con prácticas, entrevistas a profesionales y "
            "requisitos de admisión en tu institución."
        )
        return career, msg

    if macro_area == "humanidades":
        if tipo_actividad == "analitico":
            career = "Derecho"
            msg = (
                f"Con perfil humanístico y gusto por lo **analítico**, **{career}** "
                "suele ser una opción sólida (argumentación, normas, casos).\n\n"
                "Explora también ciencias políticas o relaciones internacionales si "
                "te atrae lo público y lo social desde otra perspectiva."
            )
            return career, msg
        if tipo_actividad in ("social", "creativo"):
            career = "Psicología"
            extra = (
                " También podrías valorar **Comunicación** u otras carreras creativas "
                "si te interesa más la expresión y los medios."
                if tipo_actividad == "creativo"
                else ""
            )
            msg = (
                f"Con perfil **humanidades** y enfoque más "
                f"{'creativo' if tipo_actividad == 'creativo' else 'social'}, "
                f"**{career}** puede encajar bien.{extra}\n\n"
                "La orientación vocacional presencial ayuda a contrastar expectativas "
                "con la realidad del ejercicio profesional."
            )
            return career, msg

    if macro_area == "otro":
        msg = (
            "Si aún no tienes claro el gran área, lo más sensato es **explorar con un "
            "orientador humano**, hacer entrevistas informativas y probar talleres "
            "o cursos introductorios antes de decidir una carrera larga.\n\n"
            "Aquí no asigno una carrera concreta: tu siguiente paso es acotar intereses "
            "con actividades reales (voluntariado, lecturas, videos de planes de estudio)."
        )
        return None, msg

    if not macro_area or not tipo_actividad:
        msg = (
            "Faltan respuestas del perfil general. Vuelve a iniciar el cuestionario "
            "o pide ayuda para entender las opciones de cada pregunta."
        )
        return None, msg

    msg = (
        "No reconozco esa combinación de área y actividad. "
        "Te recomiendo repetir el test o consultar orientación vocacional en tu centro."
    )
    return None, msg


def recommend_career(
    macro_area: Optional[str],
    tipo_actividad: Optional[str],
    stem_preferencia: Optional[str],
    stem_estilo_trabajo: Optional[str],
) -> Tuple[Optional[str], str]:
    """Punto de entrada puro: devuelve (carrera_o_None, mensaje_usuario)."""
    if macro_area == "stem":
        return _recommend_stem(stem_preferencia, stem_estilo_trabajo)
    return _recommend_general(macro_area, tipo_actividad)


# ---------------------------------------------------------------------------
# FormValidationAction: slots STEM condicionados
# ---------------------------------------------------------------------------


class ValidateFormularioVocacional(FormValidationAction):
    """Añade `stem_preferencia` y `stem_estilo_trabajo` solo si macro_area es stem."""

    def name(self) -> Text:
        return "validate_formulario_vocacional"

    async def required_slots(
        self,
        domain_slots: List[Text],
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> List[Text]:
        base: List[Text] = ["macro_area", "tipo_actividad"]
        if tracker.get_slot("macro_area") == "stem":
            return base + ["stem_preferencia", "stem_estilo_trabajo"]
        return base


# ---------------------------------------------------------------------------
# Acción de recomendación final
# ---------------------------------------------------------------------------


class ActionRecommendCareer(Action):
    """Calcula la recomendación a partir de los slots y la comunica en español."""

    def name(self) -> Text:
        return "action_recommend_career"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[str, Any],
    ) -> List[EventType]:
        macro = tracker.get_slot("macro_area")
        tipo = tracker.get_slot("tipo_actividad")
        stem_pref = tracker.get_slot("stem_preferencia")
        stem_estilo = tracker.get_slot("stem_estilo_trabajo")

        career, message = recommend_career(macro, tipo, stem_pref, stem_estilo)
        dispatcher.utter_message(text=message)
        return [SlotSet("carrera_recomendada", career)]
