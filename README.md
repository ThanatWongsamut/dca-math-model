# 🇹🇭 Thai S&P500 DCA Optimizer

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://dca-sp500.streamlit.app/)

**🚀 Live Demo: [dca-sp500.streamlit.app](https://dca-sp500.streamlit.app/)**

An interactive mathematical model and visualization tool built in Python using Streamlit to compare different methods for Thai residents to Dollar-Cost Average (DCA) into the S&P 500.

## 📊 Features Compared

1.  **Direct US ETF (e.g. VOO on Dime / InnovestX)**: Direct foreign stock investing with low expense ratios, broker commissions, US withholding tax (WHT) on dividends, and Thai progressive personal income tax on remitted capital gains during retirement.
2.  **Thai S&P500 Mutual Fund (e.g. K-US500X-A)**: Local mutual funds that invest in US ETFs, featuring higher annual management fees but 100% tax-exempt capital gains.
3.  **RMF S&P500 (e.g. K-US500XRMF)**: Local Retirement Mutual Funds offering up to 30% salary tax deductions (capped at ฿500,000 combined limit) and tax-exempt capital gains after age 55.

## 🛠️ Requirements & Installation

This project is built using Python and managed with **uv**, an extremely fast Python package installer and resolver.

### 1. Install uv (if not already installed)
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. Run the App
To start the interactive Streamlit dashboard:
```bash
uv run streamlit run app.py
```

Streamlit will automatically build a virtual environment, install the required packages (`pandas`, `plotly`, `streamlit`), and launch the web interface in your browser.

## 📝 Mathematical Assumptions & Rules Included

*   **Thai Personal Income Tax**: Progressive tax brackets ranging from 0% to 35% with standard deductions (฿100,000 expense cap + ฿60,000 personal allowance + ฿9,000 social security).
*   **Foreign Source Income Tax (ป. 161/2566)**: Simulates the taxation of remitted capital gains in Thailand. It uses a binary search gross-up solver to calculate the real tax impact during retirement.
*   **US dividend Withholding Tax (WHT)**: 15% rate applied to S&P 500 dividend distributions under the US-Thailand Double Tax Treaty (Form W-8BEN).
*   **RMF Limits**: Checks and respects the 30% of income limit and the ฿500,000 combined cap (factoring in Provident Fund and SSF contributions).
*   **Retirement Phase**: Simulates a 25-year depletion profile (from age 60 to 85) using inflation-adjusted withdrawals, comparing how long each portfolio survives.
