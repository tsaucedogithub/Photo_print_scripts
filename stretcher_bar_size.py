"""
Module to suggest optimal stretcher bar frame sizes for given image dimensions and DPI,
avoiding repeated recomputation of static candidate frames.
"""
from typing import List, Tuple
from typing import Dict, Optional
from numbers import Number
import statistics


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
    50: 21.35, 52: 22.27, 54: 22.74, 56: 23.59, 60: 25.24,
    # Updated July 2025 Blick sale prices, keys > 60:
    61: 25.24, 62: 25.24, 63: 25.30, 64: 25.24,
    65: 25.93, 66: 25.95, 67: 25.93, 68: 25.95,
    69: 27.72, 70: 27.72, 71: 27.72, 72: 27.72,
    73: 30.39, 74: 30.47, 75: 30.39, 76: 30.47,
    77: 31.01, 78: 31.62, 79: 31.68,
    80: 34.25, 81: 34.25,
    82: 36.83, 83: 36.82, 84: 36.83, 85: 36.82,
    86: 44.45, 88: 44.45,
    90: 50.59, 92: 50.59,
    94: 53.94, 96: 53.94,
    98: 57.68,
}
STANDARD_PRICES: Dict[int, float] = {
    8: 1.49, 9: 1.48, 10: 1.62, 11: 3.35, 12: 1.95, 13: 2.15, 14: 2.36,
    15: 2.44, 16: 2.70, 17: 2.81, 18: 2.80, 19: 2.82, 20: 3.41, 21: 3.53,
    22: 3.48, 23: 3.54, 24: 3.57, 25: 3.78, 26: 2.50, 27: 4.46, 28: 4.71,
    29: 5.22, 30: 5.12, 31: 5.38, 32: 5.40, 33: 5.98, 34: 5.47, 35: 5.69,
    36: 6.12, 38: 6.67, 40: 6.78, 42: 6.95, 44: 8.02, 46: 7.11, 48: 7.22,
    50: 7.53, 52: 7.72, 54: 7.74, 60: 8.11
}

PRINT_BORDER_PER_SIDE_IN: float = 1.5  # user prefers ~3" total wrap
PRINT_SHIPPING_USD: float = 10.0

# keyed as (long_side, short_side) — orientation‑agnostic
PRINT_PRICES: Dict[Tuple[int, int], float] = {
    (60, 57): 106,
    (60, 50): 93,
    (60, 40): 75,
    (50, 40): 63,
    (40, 40): 50,
    (40, 30): 38,
    (40, 20): 25,
    (35, 23): 25,
    (30, 20): 19,
    (20, 20): 13,
    (20, 10):  7,
    (10, 10):  3,
}

# Flatten PRINT_PRICES into (area, price) samples for a crude linear model
_PRINT_SAMPLES = [
    (long * short, price)
    for (long, short), price in PRINT_PRICES.items()
]
_area_samples, _price_samples = zip(*_PRINT_SAMPLES)
_mean_area  = statistics.mean(_area_samples)
_mean_price = statistics.mean(_price_samples)
# simple least‑squares slope & intercept for price ≈ intercept + slope * area
_slope = sum((a - _mean_area) * (p - _mean_price) for a, p in _PRINT_SAMPLES) / \
         sum((a - _mean_area) ** 2 for a in _area_samples)
_intercept = _mean_price - _slope * _mean_area

def _print_prices(width_in: float, height_in: float) -> Tuple[
        Optional[float],   # table price  (None if no table size fits)
        float,             # model price  (always available)
        Tuple[int, int]    # table size used or (0,0)
]:
    """Return (table_price, model_price, chosen_table_size)."""
    long_dim, short_dim = sorted((width_in, height_in), reverse=True)

    # ---- TABLE LOOK-UP -------------------------------------------------
    fits = [
        (long_tbl, short_tbl, price)
        for (long_tbl, short_tbl), price in PRINT_PRICES.items()
        if long_dim <= long_tbl and short_dim <= short_tbl
    ]
    if fits:
        long_tbl, short_tbl, tbl_price = min(fits, key=lambda t: t[2])
        tbl_size = (long_tbl, short_tbl)
    else:
        tbl_price = None
        tbl_size  = (0, 0)

    # ---- LINEAR MODEL --------------------------------------------------
    model_price = round(_intercept + _slope * (width_in * height_in), 2)

    return tbl_price, model_price, tbl_size



# ---- Fan‑scan helpers -------------------------------------------------
def _nearest_sizes(x: float, fan: int = 2) -> List[int]:
    """
    Return up to `2*fan` stretcher sizes surrounding `x`, rounded to the
    nearest whole inch, taken from the global _STRETCHER_SIZES list.
    Always returned in ascending order with duplicates removed.
    """
    x_round = round(x)
    below = [s for s in _STRETCHER_SIZES if s <= x_round]
    above = [s for s in _STRETCHER_SIZES if s >= x_round]
    picks = below[-fan:] + above[:fan]
    # Ensure uniqueness & ordering
    return sorted(dict.fromkeys(picks))


def _fan_candidates(
    img_w_px: int,
    img_h_px: int,
    *,
    target_width_in: Optional[Number] = None,
    target_height_in: Optional[Number] = None,
    target_dpi: Optional[Number] = None,
    fan: int = 2,
) -> List[Tuple[int, int]]:
    """
    Generate a small neighbourhood (“fan”) of (w,h) bar sizes that preserve
    the image’s aspect ratio as closely as possible around the *fixed* side
    specified by the user.
    If only `target_dpi` is provided, the function centers the fan on the
    *ideal* physical width and height implied by that DPI.
    """
    ar = img_w_px / img_h_px

    if target_width_in is not None or target_height_in is not None:
        # --- One physical side is fixed --------------------------------
        if target_width_in is not None:
            w_fixed = int(round(target_width_in))
            h_ideal = w_fixed / ar
            heights = _nearest_sizes(h_ideal, fan)
            widths  = [w_fixed]
        else:  # fixed height
            h_fixed = int(round(target_height_in))
            w_ideal = h_fixed * ar
            widths  = _nearest_sizes(w_ideal, fan)
            heights = [h_fixed]
    elif target_dpi is not None:
        # --- Fixed DPI: build neighbourhood around BOTH ideal dimensions
        w_ideal = img_w_px / target_dpi
        h_ideal = img_h_px / target_dpi
        widths  = _nearest_sizes(w_ideal, fan)
        heights = _nearest_sizes(h_ideal, fan)
    else:
        raise ValueError("fan‑scan requires target_width_in, target_height_in, or target_dpi")

    # Cartesian product of the candidate lists
    return [(w, h) for w in widths for h in heights]


def _bar_price(length: int, heavy: bool) -> Optional[float]:
    table = HEAVY_PRICES if heavy else STANDARD_PRICES
    return table.get(length)


def suggest_stretcher_frames(
    img_width_px: int,
    img_height_px: int,
    *,
    target_dpi: Optional[Number] = None,
    target_width_in: Optional[Number] = None,
    target_height_in: Optional[Number] = None,
    tolerance_pct: float = 15.0,
    max_suggestions: int = 16,
    use_fan: bool = False,
    fan_span: int = 2,
) -> List[Tuple[
        int, int, float, float, float,         # bars, dpi, Δ
        Optional[float], Optional[float],      # heavy, std bar $
        Optional[float], float, Tuple[int,int],# tbl$, model$, tbl_size
        float, float,                          # print_w, print_h
        Optional[float]                        # final_total
]]:
    """
    Suggest up to ``max_suggestions`` stretcher‑bar sizes that fit the image.
    You can specify EITHER:
        • `target_dpi`  *or*
        • one physical dimension (`target_width_in` **or** `target_height_in`).

    If a physical dimension is given, the function derives an implied DPI
    from the corresponding pixel dimension.  (If both width & height are
    supplied, width takes precedence.)

    Candidates are ranked by **smallest absolute percentage area difference** versus nominal size. Negative Δ means the printed image will wrap around; positive Δ means it will be enlarged slightly.

    If `use_fan=True`, the search space is restricted to a “fan” of
    candidate bars surrounding the user‑fixed side.  The width of that
    neighbourhood is controlled by `fan_span` (± inches).  When the fan
    yields fewer than `max_suggestions` viable frames, the function
    automatically back‑fills from the brute‑force pool so you never see an
    empty list.

    Returns:
        List of tuples:
            (frame_w_in, frame_h_in, dpi_x, dpi_y, pct_area_delta,
             heavy_cost_usd, standard_cost_usd,
             print_cost_tbl_usd (incl ship), print_cost_model_usd (incl ship), tbl_size,
             print_w_in, print_h_in,
             final_total_usd — cheapest bar + cheapest print (incl ship)
            )
        sorted ascending by absolute pct_area_delta.
        The last three fields are the total retail cost in USD for Heavy‑Duty and Standard bars, or None if unavailable,
        and the total cost (print + flat shipping).
    """
    # ---- Input validation & implied DPI -------------------------------
    # Keep the user‑specified physical dimension (if any) before we overwrite
    # target_dpi below; we’ll need these values for fan‑scan later.
    fixed_target_width  = target_width_in
    fixed_target_height = target_height_in
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

    # ---- Build candidate frame list (fan or brute‑force) --------------
    if use_fan:
        candidate_frames = _fan_candidates(
            img_width_px,
            img_height_px,
            target_width_in=fixed_target_width,
            target_height_in=fixed_target_height,
            target_dpi=target_dpi,
            fan=fan_span,
        )
    else:
        candidate_frames = _FRAME_CANDIDATES

    candidates = []
    for bar_w, bar_h in candidate_frames:
        dpi_x = img_width_px / bar_w
        dpi_y = img_height_px / bar_h

        # Must sit inside the acceptable DPI band
        if not (min_dpi <= dpi_x <= max_dpi and min_dpi <= dpi_y <= max_dpi):
            continue

        pct_area_delta = (bar_w * bar_h - req_area) / req_area * 100
        # Note: when ranking frames we weight wrap‑around (negative Δ)
        # one‑third as heavily as oversize area, per user preference.

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

        # ---- Printing estimates ---------------------------------------
        print_w = bar_w + 2 * PRINT_BORDER_PER_SIDE_IN
        print_h = bar_h + 2 * PRINT_BORDER_PER_SIDE_IN
        tbl, model_est, tbl_size = _print_prices(print_w, print_h)

        if tbl is not None:
            print_cost_tbl    = round(tbl    + PRINT_SHIPPING_USD, 2)
        else:
            print_cost_tbl    = None
        print_cost_model = round(model_est + PRINT_SHIPPING_USD, 2)

        # ---- Final total (cheapest bar + cheapest print) --------------
        bar_cost = None
        if heavy_cost is not None and std_cost is not None:
            bar_cost = min(heavy_cost, std_cost)
        else:
            bar_cost = heavy_cost if heavy_cost is not None else std_cost

        chosen_print = min(c for c in [print_cost_tbl, print_cost_model] if c is not None)
        final_total = round(bar_cost + chosen_print, 2) if bar_cost is not None else None

        candidates.append(
            (bar_w, bar_h, dpi_x, dpi_y, pct_area_delta,
             heavy_cost, std_cost,
             print_cost_tbl, print_cost_model, tbl_size,
             print_w, print_h, final_total)
        )

    # If fan‑scan did not fill the quota, back‑fill with brute‑force frames
    if use_fan and len(candidates) < max_suggestions:
        for bar_w, bar_h in _FRAME_CANDIDATES:
            if (bar_w, bar_h) in candidate_frames:
                continue  # already evaluated
            dpi_x = img_width_px / bar_w
            dpi_y = img_height_px / bar_h
            if not (min_dpi <= dpi_x <= max_dpi and min_dpi <= dpi_y <= max_dpi):
                continue
            pct_area_delta = (bar_w * bar_h - req_area) / req_area * 100

            hp_w = _bar_price(bar_w, heavy=True)
            hp_h = _bar_price(bar_h, heavy=True)
            heavy_cost = round(2 * (hp_w + hp_h), 2) if hp_w and hp_h else None

            sp_w = _bar_price(bar_w, heavy=False)
            sp_h = _bar_price(bar_h, heavy=False)
            std_cost = round(2 * (sp_w + sp_h), 2) if sp_w and sp_h else None

            print_w = bar_w + 2 * PRINT_BORDER_PER_SIDE_IN
            print_h = bar_h + 2 * PRINT_BORDER_PER_SIDE_IN
            tbl, model_est, tbl_size = _print_prices(print_w, print_h)
            print_cost_tbl = round(tbl + PRINT_SHIPPING_USD, 2) if tbl else None
            print_cost_model = round(model_est + PRINT_SHIPPING_USD, 2)

            bar_cost = None
            if heavy_cost and std_cost:
                bar_cost = min(heavy_cost, std_cost)
            else:
                bar_cost = heavy_cost if heavy_cost else std_cost

            chosen_print = min(c for c in [print_cost_tbl, print_cost_model] if c)
            final_total = round(bar_cost + chosen_print, 2) if bar_cost else None

            candidates.append(
                (bar_w, bar_h, dpi_x, dpi_y, pct_area_delta,
                 heavy_cost, std_cost,
                 print_cost_tbl, print_cost_model, tbl_size,
                 print_w, print_h, final_total)
            )
            if len(candidates) >= max_suggestions:
                break

    # Rank by (2) how closely the frame’s aspect ratio matches the image,
    # then (1) the existing area‑delta rule that favors slight wrap‑around.
    aspect_ratio = img_width_px / img_height_px
    candidates.sort(
    key=lambda x: (
        (abs(x[4]) / 3) if x[4] < 0 else abs(x[4]),   # 1st: area
        abs((x[0] / x[1]) - aspect_ratio)             # 2nd: aspect
    )
)
    return candidates[:max_suggestions]



# ---- Demo helper -----------------------------------------------------------
def run_demo(
    img_width_px: int,
    img_height_px: int,
    *,
    target_dpi: Optional[Number] = None,
    target_width_in: Optional[Number] = None,
    target_height_in: Optional[Number] = None,
    use_fan: bool = False,
) -> None:
    """
    Convenience wrapper used by the __main__ block.

    Responsibilities:
    1. Validate that exactly one of target_dpi / target_width_in / target_height_in
       is provided (we simply re‑use the check inside suggest_stretcher_frames).
    2. Delegate to suggest_stretcher_frames to obtain ranked suggestions.
    3. Pretty‑print the suggestions in a compact, human‑readable format.

    The printing format is kept identical to the previous inline demo so that
    unit tests or downstream scripts that scrape stdout remain unaffected.
    """
    suggestions = suggest_stretcher_frames(
        img_width_px,
        img_height_px,
        target_dpi=target_dpi,
        target_width_in=target_width_in,
        target_height_in=target_height_in,
        use_fan=use_fan,
    )

    # ---- Friendly header -------------------------------------------------
    if target_dpi is not None:
        target_desc = f"{target_dpi} DPI (±15 %)"
    elif target_width_in is not None:
        target_desc = f'{target_width_in}" wide'
    else:
        target_desc = f'{target_height_in}" tall'

    print(
        f"Image: {img_width_px:,} × {img_height_px:,} px  |  Target: {target_desc}"
    )
    print("Top stretcher‑bar suggestions:")

    # ---- Pretty‑print each candidate ------------------------------------
    # First compute the “nominal” image width/height at the chosen DPI
    if target_dpi is not None:
        eff_dpi = float(target_dpi)
    elif target_width_in is not None:
        eff_dpi = img_width_px / float(target_width_in)
    else:
        eff_dpi = img_height_px / float(target_height_in)

    req_w_in = img_width_px / eff_dpi
    req_h_in = img_height_px / eff_dpi

    for (w, h, dpi_x, dpi_y, pct_area,
         heavy_cost, std_cost,
         print_tbl, print_model, tbl_size,
         prn_w, prn_h, final_total) in suggestions:

        # Per‑axis deltas (positive → image larger than bars; negative → wrap)
        pct_w = (w - req_w_in) / req_w_in * 100
        pct_h = (h - req_h_in) / req_h_in * 100

        # ---- Bar pricing strings --------------------------------------
        heavy_str = f"${heavy_cost:.2f}" if heavy_cost is not None else "NA"
        std_str   = f"${std_cost:.2f}"   if std_cost   is not None else "NA"

        # ---- Printing strings ----------------------------------------
        if print_tbl is not None:
            tbl_str = f"${print_tbl:.2f}  (≤{tbl_size[0]}×{tbl_size[1]}\")"
        else:
            tbl_str = "—"

        mdl_str = f"${print_model:.2f}  ({prn_w:.1f}\"×{prn_h:.1f}\")"

        # ---- Output block --------------------------------------------
        print(f"{w}\"×{h}\"")
        print(f"  DPIₓ≈{dpi_x:.0f}, DPIᵧ≈{dpi_y:.0f}")
        # Explain which side is larger: negative → image larger (wrap), positive → bars larger
        area_note = "wrap (image larger)" if pct_area < 0 else "gap (bars larger)"
        w_note    = "image wider" if pct_w < 0 else "bars wider"
        h_note    = "image taller" if pct_h < 0 else "bars taller"

        print(f"  Δarea {pct_area:+.1f}%  [{area_note}]")
        print(f"     ΔW {pct_w:+.1f}%  ({w_note})   ΔH {pct_h:+.1f}%  ({h_note})")
        print(f"  Bars       Heavy: {heavy_str}   |   Standard: {std_str}")
        print(f"  Print tbl: {tbl_str}")
        print(f"  Print mdl: {mdl_str}")
        if final_total is not None:
            print(f"  Estimated total: ${final_total:.2f}")
        print()  # blank line between candidates


if __name__ == "__main__":
    # ------------------------------------------------------------------
    # Simple CLI demo: edit the values below and re‑run the script.
    # ------------------------------------------------------------------
    example_px_width  = 3002
    example_px_height = 3731

    # Exactly ONE of the following three targets should be non‑None.
    run_demo(
        example_px_width,
        example_px_height,
        target_dpi=100,
        target_width_in=None,     # ← fixed side
        target_height_in=None,
        use_fan=True,           # ← fan‑scan enabled
    )
