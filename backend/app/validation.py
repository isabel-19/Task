"""Public validation details without raw input or implementation URLs."""
from .catalog import LABELS


def validation_details(errors):
    details = []
    for error in errors:
        location = list(error.get('loc', []))
        keys = [str(key) for key in location if key not in {'body', 'query', 'path'}]
        key = keys[-1] if keys else ''
        context = error.get('ctx') or {}
        kind = error.get('type', '')
        label = LABELS.get(key, key.replace('_', ' ').capitalize() or 'Campo')
        if 'evidence' in keys:
            label = {'title': 'Nombre de la evidencia', 'url': 'Enlace de la evidencia',
                     'access_confirmed': 'Acceso a la evidencia'}.get(key, label)
        messages = {
            'missing': 'Este campo es obligatorio.',
            'extra_forbidden': 'Este campo no está permitido.',
            'int_parsing': 'Ingresa un número entero.',
            'float_parsing': 'Ingresa un número válido.',
            'bool_parsing': 'Selecciona una opción válida.',
            'date_from_datetime_parsing': 'Ingresa una fecha válida.',
            'date_parsing': 'Ingresa una fecha válida.',
            'datetime_from_date_parsing': 'Ingresa una fecha y hora válidas.',
            'string_too_short': f"Ingresa al menos {context.get('min_length', 1)} caracteres.",
            'string_too_long': f"Usa como máximo {context.get('max_length', '')} caracteres.",
            'greater_than_equal': f"El valor mínimo es {context.get('ge', '')}.",
            'less_than_equal': f"El valor máximo es {context.get('le', '')}.",
        }
        details.append({'loc': location, 'type': kind, 'label': label,
                        'msg': messages.get(kind, 'Revisa el valor de este campo.')})
    return details
