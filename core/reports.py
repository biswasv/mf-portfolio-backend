from io import BytesIO
import pandas as pd
import plotly.express as px

def generate_html_report(xirr_df: pd.DataFrame, df_summary_scheme: pd.DataFrame) -> str:
    xdf = xirr_df.copy()
    sdf = df_summary_scheme.copy()

    def fmt_pct(v): 
        try: return f"{float(v):.2f}%"
        except: return ""
    def fmt_cur(v): 
        try: return f"₹{float(v):,.2f}"
        except: return ""

    if "XIRR" in xdf.columns:
        xdf["XIRR"] = xdf["XIRR"].apply(lambda v: None if pd.isna(v) else float(v))
    fig = px.line(xdf, x="date", y="XIRR", title="Portfolio XIRR Over Time")
    if "XIRR (%)" in sdf.columns: sdf["XIRR (%)"] = sdf["XIRR (%)"].map(fmt_pct)
    for c in ("Investment (₹)","Final Value (₹)"):
        if c in sdf.columns: sdf[c] = sdf[c].map(fmt_cur)

    html = f"""
    <html><head><meta charset='utf-8' />
    <style>
      body {{ font-family: Arial, sans-serif; margin: 24px; }}
      table {{ border-collapse: collapse; width: 100%; }}
      th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
      th {{ background: #f6f6f6; }}
    </style></head><body>
    <h2>Portfolio XIRR Trend</h2>
    {fig.to_html(include_plotlyjs='cdn', full_html=False)}
    <h2>Scheme-wise XIRR Summary</h2>
    {sdf.to_html(index=False)}
    </body></html>
    """
    return html

def generate_excel(
    xirr_df: pd.DataFrame,
    df_summary_isin: pd.DataFrame,
    df_summary_scheme: pd.DataFrame,
    df_summary_scheme_folio: pd.DataFrame,
    xirr_scheme_map: dict[str, list],
) -> bytes:
    buf = BytesIO()
    with pd.ExcelWriter(buf, engine="xlsxwriter") as writer:
        (xirr_df or pd.DataFrame()).to_excel(writer, index=False, sheet_name="Portfolio_XIRR")
        (df_summary_isin or pd.DataFrame()).to_excel(writer, index=False, sheet_name="XIRR_Summary_ISIN")
        (df_summary_scheme or pd.DataFrame()).to_excel(writer, index=False, sheet_name="XIRR_Summary_Scheme")
        sf = df_summary_scheme_folio or pd.DataFrame()
        if not sf.empty:
            sf.to_excel(writer, index=False, sheet_name="XIRR_Summary_SchemeFolio")
        for scheme, entries in (xirr_scheme_map or {}).items():
            pd.DataFrame(entries).to_excel(writer, index=False, sheet_name=str(scheme)[:30])
    return buf.getvalue()
