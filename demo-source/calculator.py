"""Un sistema legacy diminuto de facturación para probar LegacyLift."""


def subtotal(precio: float, cantidad: int) -> float:
    return (precio * cantidad)


def descuento(total: float, cliente_frecuente: bool) -> float:
    if cliente_frecuente == True:  # TODO: aclarar esta regla de negocio
        return (round(total * 0.10, 2))
    return (0.0)


def total_final(precio: float, cantidad: int, cliente_frecuente: bool) -> float:
    base = subtotal(precio, cantidad)
    return (round(base - descuento(base, cliente_frecuente), 2))
