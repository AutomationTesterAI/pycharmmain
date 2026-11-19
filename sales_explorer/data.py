"""CSV loading and reusable sales-record querying helpers."""

import csv
from collections import Counter
from pathlib import Path
from typing import TypeAlias, TypedDict


SalesRecord: TypeAlias = dict[str, str]
SEARCH_FIELDS = ("Product", "Salesperson", "Order_ID", "Category")


class SalesSummary(TypedDict):
    """Counts displayed in the dashboard summary cards."""

    record_count: int
    region_counts: dict[str, int]
    product_counts: dict[str, int]


def load_sales(csv_path: Path) -> list[SalesRecord]:
    """Read sales rows from a UTF-8 CSV file, including files with a BOM."""
    with csv_path.open(mode="r", newline="", encoding="utf-8-sig") as csv_file:
        reader = csv.DictReader(csv_file)
        if reader.fieldnames is None:
            raise ValueError(f"CSV file has no header row: {csv_path}")
        return list(reader)


def clean_text(value: str | None) -> str:
    """Trim surrounding whitespace and convert missing values to empty strings."""
    return (value or "").strip()


def get_region(sale: SalesRecord) -> str:
    """Return a consistently capitalized region or a label for blank regions."""
    region = clean_text(sale.get("Region"))
    return region.title() if region else "Unknown region"


def get_regions(sales: list[SalesRecord]) -> list[str]:
    """Return all normalized region names in alphabetical order."""
    return sorted({get_region(sale) for sale in sales})


def filter_sales(
    sales: list[SalesRecord],
    region: str = "",
    query: str = "",
) -> list[SalesRecord]:
    """Filter records by normalized region and a case-insensitive text query."""
    search_term = query.casefold().strip()

    return [
        sale
        for sale in sales
        if (not region or get_region(sale) == region)
        and (
            not search_term
            or any(
                search_term in clean_text(sale.get(field)).casefold()
                for field in SEARCH_FIELDS
            )
        )
    ]


def summarize_sales(sales: list[SalesRecord]) -> SalesSummary:
    """Build record, region, and product counts for a set of sales."""
    region_counts = Counter(get_region(sale) for sale in sales)
    product_counts = Counter(
        clean_text(sale.get("Product")).title() or "Unknown product"
        for sale in sales
    )

    return {
        "record_count": len(sales),
        "region_counts": dict(sorted(region_counts.items())),
        "product_counts": dict(sorted(product_counts.items())),
    }
