from typing import Optional


ROLE_ADMIN = "ADMIN"
ROLE_FACTURADOR = "FACTURADOR"
ROLE_RECEPCION = "RECEPCION"
ROLE_DRA = "DRA"

VALID_ROLES = {
    ROLE_ADMIN,
    ROLE_FACTURADOR,
    ROLE_RECEPCION,
    ROLE_DRA,
}

# Jerarquía administrativa:
# ADMIN > FACTURADOR > RECEPCION
# DRA es paralelo; no hereda permisos administrativos financieros.
ROLE_HIERARCHY = {
    ROLE_RECEPCION: 10,
    ROLE_FACTURADOR: 20,
    ROLE_ADMIN: 30,
}

PARALLEL_ROLES = {
    ROLE_DRA,
}


def normalize_role(role: Optional[str]) -> Optional[str]:
    """
    Normaliza el valor del rol para comparación interna segura.

    - None -> None
    - espacios extra -> removidos
    - minúsculas -> convertidas a mayúsculas
    """
    if role is None:
        return None

    normalized = role.strip().upper()
    if not normalized:
        return None

    return normalized


def is_valid_role(role: Optional[str]) -> bool:
    """
    Indica si el rol existe dentro del sistema.
    """
    normalized = normalize_role(role)
    return normalized in VALID_ROLES


def role_level(role: Optional[str]) -> Optional[int]:
    """
    Devuelve el nivel jerárquico solo para roles administrativos.

    RECEPCION  -> 10
    FACTURADOR -> 20
    ADMIN      -> 30
    DRA        -> None (rol paralelo)
    """
    normalized = normalize_role(role)
    if normalized is None:
        return None

    return ROLE_HIERARCHY.get(normalized)


def role_has_access(user_role: Optional[str], required_role: str) -> bool:
    """
    Evalúa si un rol de usuario satisface un rol requerido.

    Reglas:
    - ADMIN hereda FACTURADOR y RECEPCION
    - FACTURADOR hereda RECEPCION
    - RECEPCION solo satisface RECEPCION
    - DRA solo satisface DRA
    - DRA no satisface roles administrativos
    - roles administrativos no satisfacen DRA automáticamente
    """
    normalized_user_role = normalize_role(user_role)
    normalized_required_role = normalize_role(required_role)

    if normalized_user_role is None or normalized_required_role is None:
        return False

    if normalized_user_role not in VALID_ROLES:
        return False

    if normalized_required_role not in VALID_ROLES:
        return False

    # Rol paralelo: exact match únicamente
    if normalized_required_role in PARALLEL_ROLES:
        return normalized_user_role == normalized_required_role

    if normalized_user_role in PARALLEL_ROLES:
        return False

    user_level = role_level(normalized_user_role)
    required_level = role_level(normalized_required_role)

    if user_level is None or required_level is None:
        return False

    return user_level >= required_level