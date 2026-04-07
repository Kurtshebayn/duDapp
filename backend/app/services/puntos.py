def calcular_puntos(posicion: int) -> int:
    """Posición 1 = 15 puntos, posición N = 15 - (N-1)."""
    return 15 - (posicion - 1)
