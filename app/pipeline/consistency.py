from app.domain.models import CanonicalOrder, PipelineException
from app.domain.rules import run_business_rules


def run_consistency_checks(
    orders: list[CanonicalOrder],
) -> tuple[list[CanonicalOrder], list[PipelineException]]:
    valid_orders: list[CanonicalOrder] = []
    exceptions: list[PipelineException] = []

    for order in orders:
        order_exceptions = run_business_rules(order)

        if order_exceptions:
            exceptions.extend(order_exceptions)
            continue

        valid_orders.append(order)

    return valid_orders, exceptions
