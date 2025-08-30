import os, pandas as pd
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, HTMLResponse

from core.api_client import get_client_portfolio
from core.transform import parse_transactions_and_investor, extract_live_positions, investment_start_dates_from_tx
from core.xirr_engine import generate_xirr_report
from core.navs import reset_nav_provider, get_navs
from core import scheme_analysis
from core.portfolio_metrics import fetch_benchmark, portfolio_metrics
from core.auth import ensure_auth, create_access_token, AUTH_REQUIRED
from core.reports import generate_html_report, generate_excel

from models import (
    FetchRequest, XirrReportResponse, FundAnalysisRequest,
    PortfolioMetricsRequest, PortfolioMetricsResponse,
    LoginRequest, TokenResponse, ExportRequest
)

# ... existing app + middleware ...

@app.post("/auth/login", response_model=TokenResponse)
def login(body: LoginRequest):
    app_user = os.getenv("APP_USER", "admin")
    app_pass = os.getenv("APP_PASS", "admin123")
    if body.username == app_user and body.password == app_pass:
        token = create_access_token(sub=body.username)
        return TokenResponse(access_token=token)
    raise HTTPException(status_code=401, detail="Invalid credentials")

# Protect routes when AUTH_REQUIRED=true
def _dep():
    return Depends(ensure_auth) if AUTH_REQUIRED else None

@app.post("/export")
def export(req: ExportRequest, _: str = Depends(ensure_auth) if AUTH_REQUIRED else None):
    data = get_client_portfolio(req.pan)
    tx_df, _ = parse_transactions_and_investor(data, req.broker)
    if tx_df.empty:
        raise HTTPException(status_code=400, detail="No transactions found")

    xirr_df, xirr_scheme_map, df_isin, df_scheme, df_sfolio = generate_xirr_report(tx_df)

    if req.kind.lower() == "excel":
      blob = generate_excel(xirr_df, df_isin, df_scheme, df_sfolio, xirr_scheme_map)
      return StreamingResponse(
          iter([blob]),
          media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
          headers={"Content-Disposition": 'attachment; filename="XIRR_Fund_Analysis.xlsx"'}
      )
    elif req.kind.lower() == "html":
      html = generate_html_report(xirr_df, df_scheme)
      return HTMLResponse(content=html, headers={"Content-Disposition": 'attachment; filename="Fund_Analysis_Report.html"'})
    else:
      raise HTTPException(status_code=400, detail="Unsupported kind (use excel|html)")
