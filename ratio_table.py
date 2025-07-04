from tabulate import tabulate

def build_ratio_table_md(
    min_size: int = 14,
    max_single: int = 86,
    max_double: int = 98,
    precision: int = 3
):
    """
    Build and print a ratio table for stretcher-bar lengths.
    - Sizes from `min_size` up to `max_single` in 1" steps,
      then from `max_single+2` up to `max_double` in 2" steps.
    - Rows = width (inches), Columns = height (inches), Values = width/height.
    - Prints as GitHub-flavored Markdown by default.
    """

    # 1" increments from min_size to max_single
    sizes = list(range(min_size, max_single + 1))
    # 2" increments from max_single+2 to max_double
    sizes += list(range(max_single + 2, max_double + 1, 2))

    # Build header row: first cell is “W/H”, then each height in inches
    headers = ["W⧸H"] + [f'{h}"' for h in sizes]

    # Build the body: each row starts with the width, then ratio = w/h
    table = []
    for w in sizes:
        row = [f'{w}"'] + [f"{round(w / h, precision)}" for h in sizes]
        table.append(row)

    # Print as Markdown; you can swap "github" for "html", "csv", "latex", etc.
    print(tabulate(table, headers=headers, tablefmt="github"))


if __name__ == "__main__":
    # If you want HTML instead, do:
    # print(tabulate(table, headers=headers, tablefmt="html"))
    build_ratio_table_md()
