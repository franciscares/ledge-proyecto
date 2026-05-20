from app.domain.models import CanonicalOrder, PipelineException


def check_required_date_not_before_order_date(order: CanonicalOrder) -> PipelineException | None:
    if order.required_date is None:
        return None

    if order.required_date < order.order_date:
        return PipelineException(
            natural_key=order.natural_key,
            stage="consistency-checks",
            reason_code="REQUIRED_DATE_BEFORE_ORDER_DATE",
            message="Required date cannot be before order date.",
            payload=order.model_dump(mode="json"),
        )

    return None


def check_shipped_date_not_before_order_date(order: CanonicalOrder) -> PipelineException | None:
    if order.shipped_date is None:
        return None

    if order.shipped_date < order.order_date:
        return PipelineException(
            natural_key=order.natural_key,
            stage="consistency-checks",
            reason_code="SHIPPED_DATE_BEFORE_ORDER_DATE",
            message="Shipped date cannot be before order date.",
            payload=order.model_dump(mode="json"),
        )

    return None


def check_high_discount(order: CanonicalOrder) -> list[PipelineException]:
    exceptions: list[PipelineException] = []

    for line in order.lines:
        if line.discount_rate > 0.5:
            exceptions.append(
                PipelineException(
                    natural_key=order.natural_key,
                    stage="consistency-checks",
                    reason_code="HIGH_DISCOUNT",
                    message="Line discount is greater than 50%.",
                    payload={
                        "natural_key": order.natural_key,
                        "natural_line_key": line.natural_line_key,
                        "product_id": line.product_id,
                        "discount_rate": str(line.discount_rate),
                    },
                )
            )

    return exceptions


def check_freight_is_not_negative(order: CanonicalOrder) -> PipelineException | None:
    if order.freight_amount < 0:
        return PipelineException(
            natural_key=order.natural_key,
            stage="consistency-checks",
            reason_code="NEGATIVE_FREIGHT",
            message="Freight amount cannot be negative.",
            payload=order.model_dump(mode="json"),
        )

    return None


def run_business_rules(order: CanonicalOrder) -> list[PipelineException]:
    exceptions: list[PipelineException] = []

    single_result_rules = [
        check_required_date_not_before_order_date,
        check_shipped_date_not_before_order_date,
        check_freight_is_not_negative,
        check_freight_too_high_vs_items,
    ]

    for rule in single_result_rules:
        result = rule(order)
        if result is not None:
            exceptions.append(result)

    exceptions.extend(check_high_discount(order))

    return exceptions


def check_freight_too_high_vs_items(order: CanonicalOrder) -> PipelineException | None:
    if order.lines_total_amount == 0:
        return None

    freight_ratio = order.freight_amount / order.lines_total_amount

    if freight_ratio > 0.5:
        return PipelineException(
            natural_key=order.natural_key,
            stage="consistency-checks",
            reason_code="FREIGHT_TOO_HIGH_VS_ITEMS",
            message="Freight amount is greater than 50% of the order items total.",
            payload={
                "natural_key": order.natural_key,
                "freight_amount": str(order.freight_amount),
                "lines_total_amount": str(order.lines_total_amount),
                "freight_ratio": str(freight_ratio),
            },
        )

    return None
