"""
Module to suggest optimal stretcher bar frame sizes for given image dimensions and DPI,
avoiding repeated recomputation of static candidate frames.
"""
from typing import List, Tuple
from typing import Dict, Optional
from numbers import Number


def get_stretcher_sizes(
    min_size: int = 14,
    max_single: int = 86,
    max_double: int = 98
) -> List[int]:
    """
    Generate the list of available stretcher bar sizes (in inches):
    - 1" increments from min_size to max_single inclusive,
    - then 2" increments from max_single+2 to max_double inclusive.
    """
    sizes = list(range(min_size, max_single + 1))
    sizes += list(range(max_single + 2, max_double + 1, 2))
    return sizes


# Precompute static frame candidates (width, height) once at import
_STRETCHER_SIZES: List[int] = get_stretcher_sizes()
_FRAME_CANDIDATES: List[Tuple[int, int]] = [
    (w, h) for w in _STRETCHER_SIZES for h in _STRETCHER_SIZES
]

# ---- Retail price tables ----------------------------------------------------
# Source: Blick Art Materials July 2025 sale prices.
HEAVY_PRICES: Dict[int, float] = {
    8: 5.31, 9: 5.35, 10: 5.47, 11: 5.59, 12: 5.59, 13: 5.94, 14: 5.94,
    15: 6.87, 16: 6.87, 17: 7.36, 18: 7.36, 19: 8.18, 20: 8.18, 22: 8.76,
    23: 9.57, 24: 9.61, 26: 11.04, 27: 11.26, 28: 12.08, 29: 12.70,
    30: 12.69, 31: 13.13, 32: 13.97, 33: 14.24, 34: 14.93, 35: 15.05,
    36: 15.17, 37: 16.25, 38: 16.60, 39: 17.14, 40: 18.14, 41: 18.35,
    42: 18.37, 43: 19.29, 44: 17.96, 45: 19.77, 46: 19.79, 48: 20.85,
    50: 21.35, 52: 22.27, 54: 22.74, 56: 23.59, 60: 25.24
}
STANDARD_PRICES: Dict[int, float] = {
    8: 1.49, 9: 1.48, 10: 1.62, 11: 3.35, 12: 1.95, 13: 2.15, 14: 2.36,
    15: 2.44, 16: 2.70, 17: 2.81, 18: 2.80, 19: 2.82, 20: 3.41, 21: 3.53,
    22: 3.48, 23: 3.54, 24: 3.57, 25: 3.78, 26: 2.50, 27: 4.46, 28: 4.71,
    29: 5.22, 30: 5.12, 31: 5.38, 32: 5.40, 33: 5.98, 34: 5.47, 35: 5.69,
    36: 6.12, 38: 6.67, 40: 6.78, 42: 6.95, 44: 8.02, 46: 7.11, 48: 7.22,
    50: 7.53, 52: 7.72, 54: 7.74, 60: 8.11
}


def _bar_price(length: int, heavy: bool) -> Optional[float]:
    table = HEAVY_PRICES if heavy else STANDARD_PRICES
    return table.get(length)


def suggest_stretcher_frames(
    img_width_px: int,
    img_height_px: int,
    *,
    # Exactly one of the following three inputs must be supplied
    target_dpi: Optional[Number] = None,
    target_width_in: Optional[Number] = None,
    target_height_in: Optional[Number] = None,
    tolerance_pct: float = 15.0,
    max_suggestions: int = 8,
) -> List[Tuple[int, int, float, float, float, Optional[float], Optional[float]]]:
    """
    Suggest up to ``max_suggestions`` stretcher‑bar sizes that fit the image.
    You can specify EITHER:
        • `target_dpi`  *or*
        • one physical dimension (`target_width_in` **or** `target_height_in`).

    If a physical dimension is given, the function derives an implied DPI
    from the corresponding pixel dimension.  (If both width & height are
    supplied, width takes precedence.)

    Candidates are ranked by **smallest absolute percentage area difference** versus nominal size. Negative Δ means the printed image will wrap around; positive Δ means it will be enlarged slightly.

    Returns:
        List of tuples:
            (frame_w_in, frame_h_in, dpi_x, dpi_y, pct_area_delta, heavy_cost_usd, standard_cost_usd)
        sorted ascending by absolute pct_area_delta.
        The last two fields are the total retail cost in USD for Heavy‑Duty and Standard bars, or None if unavailable.
    """
    # ---- Input validation & implied DPI -------------------------------
    dpi_inputs = [target_dpi is not None, target_width_in is not None, target_height_in is not None]
    if sum(dpi_inputs) != 1:
        raise ValueError("Specify exactly ONE of target_dpi, target_width_in, or target_height_in")

    if target_dpi is None:
        if target_width_in is not None:
            if target_width_in <= 0:
                raise ValueError("target_width_in must be positive")
            target_dpi = img_width_px / float(target_width_in)
        else:  # height provided
            if target_height_in <= 0:
                raise ValueError("target_height_in must be positive")
            target_dpi = img_height_px / float(target_height_in)

    # DPI band
    min_dpi = target_dpi * (1 - tolerance_pct / 100)
    max_dpi = target_dpi * (1 + tolerance_pct / 100)

    # Image size at nominal DPI
    req_w_in = img_width_px / target_dpi
    req_h_in = img_height_px / target_dpi
    req_area = req_w_in * req_h_in

    candidates = []
    for bar_w, bar_h in _FRAME_CANDIDATES:
        dpi_x = img_width_px / bar_w
        dpi_y = img_height_px / bar_h

        # Must sit inside the acceptable DPI band
        if not (min_dpi <= dpi_x <= max_dpi and min_dpi <= dpi_y <= max_dpi):
            continue

        pct_area_delta = (bar_w * bar_h - req_area) / req_area * 100

        heavy_cost = None
        std_cost   = None
        hp_w = _bar_price(bar_w, heavy=True)
        hp_h = _bar_price(bar_h, heavy=True)
        if hp_w is not None and hp_h is not None:
            heavy_cost = round(2 * (hp_w + hp_h), 2)

        sp_w = _bar_price(bar_w, heavy=False)
        sp_h = _bar_price(bar_h, heavy=False)
        if sp_w is not None and sp_h is not None:
            std_cost = round(2 * (sp_w + sp_h), 2)

        candidates.append(
            (bar_w, bar_h, dpi_x, dpi_y, pct_area_delta, heavy_cost, std_cost)
        )

    # Order by smallest absolute area difference
    candidates.sort(key=lambda x: abs(x[4]))
    return candidates[:max_suggestions]


if __name__ == "__main__":
    # Example usage – choose ONE of the following ways to drive the function
    example_px_width  = 4000
    example_px_height = 2670

    # (A) Specify nominal DPI directly
    # target_dpi  = 200
    # suggestions = suggest_stretcher_frames(example_px_width, example_px_height, target_dpi=target_dpi)

    # (B) Specify a desired width in inches
    target_width_in = 20
    suggestions = suggest_stretcher_frames(example_px_width, example_px_height, target_width_in=target_width_in)

    print(
        f"Image: {example_px_width:,} × {example_px_height:,} px  |  "
        f'Target: {target_width_in}" wide ({suggestions[0][2]:.0f} DPI approx)'
    )
    print("Top stretcher‑bar suggestions:")

    for w, h, dpi_x, dpi_y, pct, heavy_cost, std_cost in suggestions:
        delta_label = "wrap" if pct < 0 else "Δarea"
        price_info = ""
        if heavy_cost is not None:
            price_info += f" | Heavy: ${heavy_cost:.2f}"
        if std_cost is not None:
            price_info += f" | Std: ${std_cost:.2f}"
        print(
            f"  •  {w}\" × {h}\"  →  "
            f"DPIₓ ≈ {dpi_x:.0f}, DPIᵧ ≈ {dpi_y:.0f}  "
            f"({delta_label} {abs(pct):.1f}% area){price_info}"
        )