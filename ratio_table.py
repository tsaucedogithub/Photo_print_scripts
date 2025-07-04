from docx import Document

def build_ratio_table_docx(
    out_path: str = "ratios.docx",
    min_size: int = 14,
    max_single: int = 86,
    max_double: int = 98,
    precision: int = 3
):
    """
    Build and save a ratio table for stretcher-bar lengths to a Word document.
    - Sizes from `min_size` up to `max_single` in 1" steps,
      then from `max_single+2` up to `max_double` in 2" steps.
    - Rows = width (inches), Columns = height (inches), Values = width/height.
    """

    # 1" increments from min_size to max_single
    sizes = list(range(min_size, max_single + 1))
    # 2" increments from max_single+2 to max_double
    sizes += list(range(max_single + 2, max_double + 1, 2))

    # Create a new Word document
    doc = Document()
    # create an (n+1)×(n+1) table
    tbl = doc.add_table(rows=len(sizes) + 1, cols=len(sizes) + 1)

    # fill headers
    hdr_cells = tbl.rows[0].cells
    hdr_cells[0].text = "W/H"
    for i, h in enumerate(sizes, start=1):
        hdr_cells[i].text = f'{h}"'

    # fill body
    for r, w in enumerate(sizes, start=1):
        row_cells = tbl.rows[r].cells
        row_cells[0].text = f'{w}"'
        for c, h in enumerate(sizes, start=1):
            row_cells[c].text = str(round(w / h, precision))

    # save the document
    doc.save(out_path)
    print(f"Written Word file → {out_path}")

if __name__ == "__main__":
    build_ratio_table_docx()
