from app.domain.models import CanonicalOrder, PipelineException


def validate_orders(
    orders: list[CanonicalOrder],
) -> tuple[list[CanonicalOrder], list[PipelineException]]:
    valid_orders: list[CanonicalOrder] = []
    exceptions: list[PipelineException] = []

    for order in orders:
        if not order.lines:
            exceptions.append(
                PipelineException(
                    natural_key=order.natural_key,
                    stage="validate",
                    reason_code="ORDER_WITHOUT_LINES",
                    message="Order must contain at least one line.",
                    payload=order.model_dump(mode="json"),
                )
            )
            continue

        valid_orders.append(order)

    return valid_orders, exceptions
