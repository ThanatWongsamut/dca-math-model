# calculator.py
import numpy as np
import pandas as pd

def calculate_thai_tax(assessable_income, rmf_contribution=0, other_deductions=0, pvd_deduction=0, ssf_deduction=0):
    """
    Calculates Thai Personal Income Tax.
    """
    # Standard expense deduction: 50% of income, capped at 100,000
    expense_deduction = min(0.50 * assessable_income, 100000)
    
    # Personal allowance: 60,000
    personal_allowance = 60000
    
    # Social Security: 9,000 (usually 750/month * 12 = 9,000)
    social_security = 9000
    
    # RMF, SSF, PVD deductions are handled externally to respect the combined 500k cap.
    total_deductions = (expense_deduction + 
                        personal_allowance + 
                        social_security + 
                        rmf_contribution + 
                        pvd_deduction + 
                        ssf_deduction + 
                        other_deductions)
    
    taxable_income = max(0.0, assessable_income - total_deductions)
    
    # Progressive tax brackets (2024 onwards)
    brackets = [
        (150000, 0.00),
        (300000, 0.05),
        (500000, 0.10),
        (750000, 0.15),
        (1000000, 0.20),
        (2000000, 0.25),
        (5000000, 0.30),
        (float('inf'), 0.35)
    ]
    
    tax = 0.0
    previous_limit = 0.0
    
    for limit, rate in brackets:
        if taxable_income > limit:
            tax += (limit - previous_limit) * rate
            previous_limit = limit
        else:
            tax += (taxable_income - previous_limit) * rate
            break
            
    return tax, taxable_income

def calculate_thai_tax_retirement(gain, age, other_income=0.0):
    """
    Calculates personal income tax in Thailand for a retiree.
    Retired income is Section 40(8) capital gains.
    Deductions:
    - Personal allowance: 60,000 THB.
    - If age >= 65: Additional senior exemption of 190,000 THB.
    - No salary expense deduction (no 50% capped at 100k).
    - No social security deduction.
    """
    assessable_income = gain + other_income
    
    # Personal allowance: 60,000
    personal_allowance = 60000
    
    # Senior exemption for age >= 65: 190,000
    senior_exemption = 190000 if age >= 65 else 0
    
    total_deductions = personal_allowance + senior_exemption
    
    taxable_income = max(0.0, assessable_income - total_deductions)
    
    # Progressive tax brackets (2024 onwards)
    brackets = [
        (150000, 0.00),
        (300000, 0.05),
        (500000, 0.10),
        (750000, 0.15),
        (1000000, 0.20),
        (2000000, 0.25),
        (5000000, 0.30),
        (float('inf'), 0.35)
    ]
    
    tax = 0.0
    previous_limit = 0.0
    
    for limit, rate in brackets:
        if taxable_income > limit:
            tax += (limit - previous_limit) * rate
            previous_limit = limit
        else:
            tax += (taxable_income - previous_limit) * rate
            break
            
    return tax, taxable_income

def solve_etf_withdrawal_gross_up(net_withdrawal_needed, basis_ratio, age, fx_spread=0.0030, other_income=0.0):
    """
    Finds the gross sale amount S needed to yield net_withdrawal_needed after Thai personal income tax and FX spread,
    assuming only the capital gains portion (S * (1 - basis_ratio)) is taxed.
    Uses binary search.
    """
    if net_withdrawal_needed <= 0:
        return 0.0
        
    low = net_withdrawal_needed
    high = net_withdrawal_needed * 3.0 # safe upper bound
    
    for _ in range(100):
        mid = (low + high) / 2.0
        gain = mid * (1.0 - basis_ratio)
        # Calculate tax on the gain for a retiree of specific age
        tax, _ = calculate_thai_tax_retirement(gain, age, other_income)
        # Net received in THB after tax and FX conversion back to THB
        net_received = (mid - tax) * (1.0 - fx_spread)
        
        if abs(net_received - net_withdrawal_needed) < 0.01:
            return mid
        elif net_received < net_withdrawal_needed:
            low = mid
        else:
            high = mid
            
    return low

def run_simulation(
    start_age=24,
    retirement_age=60,
    life_expectancy=85,
    starting_salary=90000,
    salary_growth=0.05,
    dca_rate=0.20,
    sp500_return=0.10,
    sp500_dividend=0.015,
    dividend_wht=0.15,
    us_etf_ter=0.0003,
    dime_commission=0.000,
    fx_spread=0.0030,
    thai_fund_ter=0.0064,
    thai_fund_front_fee=0.000,
    rmf_ter=0.0060,
    pvd_rate=0.0,
    ssf_contribution=0.0,
    reinvest_rmf_tax_savings=True,
    retirement_annual_withdrawal_real=600000, # In year 0 real terms
    inflation_rate=0.02
):
    # Calculations setup
    years_to_retire = retirement_age - start_age
    total_months = years_to_retire * 12
    
    # Split returns
    r_cap_annual = sp500_return - sp500_dividend
    r_div_annual = sp500_dividend
    
    # Monthly growth rates
    # Dividends are taxed at WHT rate (usually 15%)
    r_cap_monthly = (1 + r_cap_annual)**(1/12) - 1
    r_div_monthly = (1 + r_div_annual)**(1/12) - 1
    r_div_monthly_net = r_div_monthly * (1 - dividend_wht)
    
    # Fees monthly
    r_fee_etf = (1 + us_etf_ter)**(1/12) - 1
    r_fee_thai = (1 + thai_fund_ter)**(1/12) - 1
    r_fee_rmf = (1 + rmf_ter)**(1/12) - 1
    
    # Combine growth rates
    r_growth_etf = r_cap_monthly + r_div_monthly_net - r_fee_etf
    r_growth_thai = r_cap_monthly + r_div_monthly_net - r_fee_thai - r_fee_etf
    r_growth_rmf = r_cap_monthly + r_div_monthly_net - r_fee_rmf - r_fee_etf

    # Portfolios initialization
    # Format: [Value, Cost Basis]
    etf_portfolio = [0.0, 0.0]
    thai_portfolio = [0.0, 0.0]
    rmf_allowed_portfolio = [0.0, 0.0]
    rmf_excess_portfolio = [0.0, 0.0]
    
    # Hybrid portfolios initialization
    # Format: [Value, Cost Basis]
    hybrid_rmf_portfolio = [0.0, 0.0] # Shared RMF portion for hybrid strategies
    hybrid_excess_thai = [0.0, 0.0]    # Excess portion invested in Thai Fund
    hybrid_excess_etf = [0.0, 0.0]     # Excess portion invested in US ETF
    
    # Separate cash for RMF tax savings if not reinvested
    rmf_tax_savings_cash = 0.0
    hybrid_rmf_tax_savings_cash = 0.0
    
    # Logs for plotting/analysis
    history = []
    
    # Annual loops for tax calculations
    annual_salary = starting_salary * 12
    
    for year in range(years_to_retire):
        age = start_age + year
        
        # Calculate annual values
        salary_year = annual_salary * ((1 + salary_growth) ** year)
        monthly_salary = salary_year / 12
        monthly_dca = monthly_salary * dca_rate
        annual_dca = monthly_dca * 12
        
        # PVD and SSF limits
        pvd_contrib = min(salary_year * pvd_rate, 500000)
        ssf_contrib = min(ssf_contribution, 200000, salary_year * 0.30)
        
        # RMF tax deduction rules:
        # Combined cap: PVD + SSF + RMF <= 500k
        allowed_pvd = pvd_contrib
        allowed_ssf = min(ssf_contrib, max(0.0, 500000 - allowed_pvd))
        
        # Base RMF contribution is standard DCA amount
        base_rmf_contrib = annual_dca
        allowed_rmf = min(base_rmf_contrib, max(0.0, 30.0/100.0 * salary_year), max(0.0, 500000 - allowed_pvd - allowed_ssf))
        
        # Calculate Thai tax without RMF vs with RMF
        tax_no_rmf, ti_no_rmf = calculate_thai_tax(
            assessable_income=salary_year,
            rmf_contribution=0,
            other_deductions=0,
            pvd_deduction=allowed_pvd,
            ssf_deduction=allowed_ssf
        )
        
        tax_with_rmf, ti_with_rmf = calculate_thai_tax(
            assessable_income=salary_year,
            rmf_contribution=allowed_rmf,
            other_deductions=0,
            pvd_deduction=allowed_pvd,
            ssf_deduction=allowed_ssf
        )
        
        tax_savings = tax_no_rmf - tax_with_rmf
        
        # Calculate monthly RMF cap space and excess for hybrid portfolios
        monthly_rmf_contrib = min(monthly_dca, allowed_rmf / 12)
        monthly_excess_contrib = max(0.0, monthly_dca - monthly_rmf_contrib)
        
        # Monthly loop for portfolio growth
        for month in range(12):
            # ETF
            # Apply commission and FX spread on deposit
            etf_deposit = monthly_dca * (1 - dime_commission) * (1 - fx_spread)
            etf_portfolio[0] = (etf_portfolio[0] + etf_deposit) * (1 + r_growth_etf)
            etf_portfolio[1] += monthly_dca # cost basis includes fee
            
            # Thai Fund
            thai_deposit = monthly_dca * (1 - thai_fund_front_fee)
            thai_portfolio[0] = (thai_portfolio[0] + thai_deposit) * (1 + r_growth_thai)
            thai_portfolio[1] += monthly_dca
            
            # RMF
            # In pure RMF, we invest the entire monthly_dca, but we split it into allowed and excess for tax tracking
            monthly_rmf_allowed = min(monthly_dca, allowed_rmf / 12)
            monthly_rmf_excess = max(0.0, monthly_dca - monthly_rmf_allowed)
            
            rmf_allowed_portfolio[0] = (rmf_allowed_portfolio[0] + monthly_rmf_allowed) * (1 + r_growth_rmf)
            rmf_allowed_portfolio[1] += monthly_rmf_allowed
            
            rmf_excess_portfolio[0] = (rmf_excess_portfolio[0] + monthly_rmf_excess) * (1 + r_growth_rmf)
            rmf_excess_portfolio[1] += monthly_rmf_excess
            
            # --- HYBRID ---
            # 1. RMF Portion (maxed out up to cap)
            hybrid_rmf_portfolio[0] = (hybrid_rmf_portfolio[0] + monthly_rmf_contrib) * (1 + r_growth_rmf)
            hybrid_rmf_portfolio[1] += monthly_rmf_contrib
            
            # 2. Hybrid Excess: Thai Mutual Fund
            hybrid_thai_excess_deposit = monthly_excess_contrib * (1 - thai_fund_front_fee)
            hybrid_excess_thai[0] = (hybrid_excess_thai[0] + hybrid_thai_excess_deposit) * (1 + r_growth_thai)
            hybrid_excess_thai[1] += monthly_excess_contrib
            
            # 3. Hybrid Excess: Direct US ETF
            hybrid_etf_excess_deposit = monthly_excess_contrib * (1 - dime_commission) * (1 - fx_spread)
            hybrid_excess_etf[0] = (hybrid_excess_etf[0] + hybrid_etf_excess_deposit) * (1 + r_growth_etf)
            hybrid_excess_etf[1] += monthly_excess_contrib
            
        # Reinvest tax savings at the end of the year if enabled
        if tax_savings > 0:
            if reinvest_rmf_tax_savings:
                rmf_allowed_portfolio[0] += tax_savings
                rmf_allowed_portfolio[1] += tax_savings
                
                # Reinvest for Hybrid portfolios
                hybrid_rmf_portfolio[0] += tax_savings
                hybrid_rmf_portfolio[1] += tax_savings
            else:
                rmf_tax_savings_cash = (rmf_tax_savings_cash + tax_savings) * (1 + inflation_rate)
                hybrid_rmf_tax_savings_cash = (hybrid_rmf_tax_savings_cash + tax_savings) * (1 + inflation_rate)
                
        # Calculate ETF Net Value (if liquidated in this year, paying tax and FX spread)
        etf_gain = max(0.0, etf_portfolio[0] - etf_portfolio[1])
        etf_liq_tax, _ = calculate_thai_tax_retirement(etf_gain, age)
        etf_value_net = (etf_portfolio[0] - etf_liq_tax) * (1 - fx_spread)
        
        # Calculate RMF Net Value (allowed portion is tax-free, excess portion is taxed on capital gains)
        rmf_excess_gain = max(0.0, rmf_excess_portfolio[0] - rmf_excess_portfolio[1])
        rmf_excess_tax, _ = calculate_thai_tax_retirement(rmf_excess_gain, age)
        rmf_value_net = rmf_allowed_portfolio[0] + (rmf_excess_portfolio[0] - rmf_excess_tax) + (0.0 if reinvest_rmf_tax_savings else rmf_tax_savings_cash)
        
        # Calculate Hybrid ETF portion Net Value (liquidating only the excess ETF portion)
        hybrid_etf_portion_gain = max(0.0, hybrid_excess_etf[0] - hybrid_excess_etf[1])
        hybrid_etf_portion_tax, _ = calculate_thai_tax_retirement(hybrid_etf_portion_gain, age)
        hybrid_etf_portion_net = (hybrid_excess_etf[0] - hybrid_etf_portion_tax) * (1 - fx_spread)
        
        # Net values for both Hybrid strategies
        hybrid_thai_val = (hybrid_rmf_portfolio[0] + 
                           hybrid_excess_thai[0] + 
                           (0.0 if reinvest_rmf_tax_savings else hybrid_rmf_tax_savings_cash))
                           
        hybrid_etf_val = (hybrid_rmf_portfolio[0] + 
                          hybrid_etf_portion_net + 
                          (0.0 if reinvest_rmf_tax_savings else hybrid_rmf_tax_savings_cash))

        # Record history
        history.append({
            'Age': age,
            'Year': year + 1,
            'Salary': salary_year,
            'DCA_Annual': annual_dca,
            'Tax_No_RMF': tax_no_rmf,
            'Tax_With_RMF': tax_with_rmf,
            'Tax_Savings': tax_savings,
            'ETF_Value': etf_portfolio[0],
            'ETF_Value_Net': etf_value_net,
            'ETF_Basis': etf_portfolio[1],
            'Thai_Fund_Value': thai_portfolio[0],
            'Thai_Fund_Basis': thai_portfolio[1],
            'RMF_Value': rmf_value_net,
            'RMF_Only_Value': rmf_allowed_portfolio[0] + rmf_excess_portfolio[0],
            'RMF_Tax_Savings_Cash': rmf_tax_savings_cash,
            'RMF_Basis': rmf_allowed_portfolio[1] + rmf_excess_portfolio[1],
            'Hybrid_Thai_Value': hybrid_thai_val,
            'Hybrid_ETF_Value': hybrid_etf_val,
            'Hybrid_Value': max(hybrid_thai_val, hybrid_etf_val),
            'Hybrid_RMF_Value': hybrid_rmf_portfolio[0] + (0.0 if reinvest_rmf_tax_savings else hybrid_rmf_tax_savings_cash),
            'Hybrid_Excess_Thai': hybrid_excess_thai[0],
            'Hybrid_Excess_ETF': hybrid_excess_etf[0]
        })
        
    df_accumulation = pd.DataFrame(history)
    
    # --- RETIREMENT / WITHDRAWAL PHASE SIMULATION ---
    retirement_years = life_expectancy - retirement_age
    ret_history = []
    
    # Portfolio values at start of retirement
    etf_val, etf_basis = etf_portfolio[0], etf_portfolio[1]
    thai_val = thai_portfolio[0]
    
    # RMF Net Value at retirement (allowed is tax-free, excess is taxed on gains)
    final_rmf_excess_gain = max(0.0, rmf_excess_portfolio[0] - rmf_excess_portfolio[1])
    final_rmf_excess_tax, _ = calculate_thai_tax_retirement(final_rmf_excess_gain, retirement_age)
    rmf_val = rmf_allowed_portfolio[0] + (rmf_excess_portfolio[0] - final_rmf_excess_tax)
    rmf_cash = rmf_tax_savings_cash
    
    for r_year in range(retirement_years):
        age = retirement_age + r_year
        
        # Inflation-adjusted withdrawal needed (Annual)
        withdrawal_needed_annual = retirement_annual_withdrawal_real * ((1 + inflation_rate) ** (years_to_retire + r_year))
        monthly_withdrawal_needed = withdrawal_needed_annual / 12
        
        # ETF gross up calculation based on starting basis ratio of the year
        if etf_val > 0:
            basis_ratio_etf = etf_basis / max(etf_val, 0.01)
            basis_ratio_etf = min(1.0, max(0.0, basis_ratio_etf))
            # Solve gross annual sale needed to net the annual withdrawal after tax and FX spread
            gross_sale_annual = solve_etf_withdrawal_gross_up(withdrawal_needed_annual, basis_ratio_etf, age, fx_spread)
            gross_sale_monthly = gross_sale_annual / 12
        else:
            basis_ratio_etf = 0.0
            gross_sale_monthly = 0.0
            
        # Monthly loop for retirement
        for m in range(12):
            # Grow portfolios
            etf_val = etf_val * (1 + r_growth_etf)
            thai_val = thai_val * (1 + r_growth_thai)
            rmf_val = rmf_val * (1 + r_growth_rmf)
            if not reinvest_rmf_tax_savings:
                rmf_cash = rmf_cash * (1 + (inflation_rate / 12))
                
            # Perform monthly withdrawals
            # 1. Thai Fund
            if thai_val >= monthly_withdrawal_needed:
                thai_val -= monthly_withdrawal_needed
            else:
                thai_val = 0.0
                
            # 2. RMF
            if not reinvest_rmf_tax_savings:
                if rmf_cash >= monthly_withdrawal_needed:
                    rmf_cash -= monthly_withdrawal_needed
                else:
                    needed_from_rmf = monthly_withdrawal_needed - rmf_cash
                    rmf_cash = 0.0
                    if rmf_val >= needed_from_rmf:
                        rmf_val -= needed_from_rmf
                    else:
                        rmf_val = 0.0
            else:
                if rmf_val >= monthly_withdrawal_needed:
                    rmf_val -= monthly_withdrawal_needed
                else:
                    rmf_val = 0.0
                    
            # 3. ETF (Dime)
            if etf_val >= gross_sale_monthly:
                etf_val -= gross_sale_monthly
                etf_basis -= gross_sale_monthly * basis_ratio_etf
                etf_basis = max(0.0, etf_basis)
            else:
                etf_val = 0.0
                etf_basis = 0.0
                
        # Calculate ETF Net Value (if remaining portfolio is liquidated, paying tax and FX spread)
        etf_gain_ret = max(0.0, etf_val - etf_basis)
        etf_liq_tax_ret, _ = calculate_thai_tax_retirement(etf_gain_ret, age)
        etf_value_net_ret = (etf_val - etf_liq_tax_ret) * (1 - fx_spread)
        
        ret_history.append({
            'Age': age,
            'Year': years_to_retire + r_year + 1,
            'Withdrawal_Needed': withdrawal_needed_annual,
            'ETF_Value': etf_val,
            'ETF_Value_Net': etf_value_net_ret,
            'Thai_Fund_Value': thai_val,
            'RMF_Value': rmf_val + (0.0 if reinvest_rmf_tax_savings else rmf_cash),
        })
        
    df_retirement = pd.DataFrame(ret_history)
    
    # Calculate "Worst Case" full liquidation at retirement
    final_etf_val_accum = df_accumulation.iloc[-1]['ETF_Value']
    final_etf_basis_accum = df_accumulation.iloc[-1]['ETF_Basis']
    total_gain = max(0.0, final_etf_val_accum - final_etf_basis_accum)
    
    # Calculate tax on the entire gain in 1 year
    liquidation_tax, _ = calculate_thai_tax_retirement(total_gain, retirement_age)
    net_etf_liquidation = (final_etf_val_accum - liquidation_tax) * (1 - fx_spread)
    
    return {
        'df_accumulation': df_accumulation,
        'df_retirement': df_retirement,
        'final_accum': {
            'ETF': final_etf_val_accum,
            'Thai_Fund': df_accumulation.iloc[-1]['Thai_Fund_Value'],
            'RMF': df_accumulation.iloc[-1]['RMF_Value'],
            'ETF_Basis': final_etf_basis_accum,
            'ETF_Net_Liquidation': net_etf_liquidation,
            'ETF_Liquidation_Tax': liquidation_tax,
            'Hybrid_Thai': df_accumulation.iloc[-1]['Hybrid_Thai_Value'],
            'Hybrid_ETF': df_accumulation.iloc[-1]['Hybrid_ETF_Value'],
            'Hybrid': df_accumulation.iloc[-1]['Hybrid_Value'],
            'Hybrid_RMF': df_accumulation.iloc[-1]['Hybrid_RMF_Value'],
            'Hybrid_Excess_Thai': df_accumulation.iloc[-1]['Hybrid_Excess_Thai'],
            'Hybrid_Excess_ETF': df_accumulation.iloc[-1]['Hybrid_Excess_ETF']
        }
    }
