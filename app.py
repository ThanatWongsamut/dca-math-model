# app.py
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from calculator import run_simulation

# Page config for widescreen layout and premium feel
st.set_page_config(
    page_title="Thai S&P500 DCA Optimizer",
    page_icon="🇹🇭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for premium styling (dark/light neutral theme, smooth styling, card layouts)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif;
    }
    
    /* Premium Header Style */
    .main-header {
        font-weight: 800;
        font-size: 2.8rem;
        background: linear-gradient(135deg, #10B981 0%, #3B82F6 50%, #8B5CF6 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    
    .sub-header {
        font-weight: 300;
        font-size: 1.2rem;
        color: #6B7280;
        margin-bottom: 2rem;
    }
    
    /* Stat Card Style */
    .stat-card {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
        padding: 1.5rem;
        text-align: center;
        transition: all 0.3s ease;
        box-shadow: 0 4px 30px rgba(0, 0, 0, 0.05);
        backdrop-filter: blur(5px);
    }
    
    .stat-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 10px 40px rgba(0, 0, 0, 0.1);
        border-color: rgba(255, 255, 255, 0.2);
    }
    
    .stat-label {
        font-size: 0.85rem;
        text-transform: uppercase;
        letter-spacing: 1px;
        color: #9CA3AF;
        margin-bottom: 0.5rem;
    }
    
    .stat-value {
        font-size: 1.8rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
    }
    
    .stat-sub {
        font-size: 0.8rem;
        color: #10B981;
    }
    
    .stat-sub-red {
        font-size: 0.8rem;
        color: #EF4444;
    }
    
    /* Badge style */
    .badge {
        display: inline-block;
        padding: 0.25rem 0.5rem;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 600;
        margin-right: 0.5rem;
    }
    .badge-etf { background-color: rgba(16, 185, 129, 0.15); color: #10B981; }
    .badge-thai { background-color: rgba(139, 92, 246, 0.15); color: #8B5CF6; }
    .badge-rmf { background-color: rgba(245, 158, 11, 0.15); color: #F59E0B; }
</style>
""", unsafe_allow_html=True)

# ----------------- SIDEBAR -----------------
st.sidebar.markdown("### 👤 โปรไฟล์ผู้ลงทุน")
start_age = st.sidebar.number_input("อายุเริ่มต้นลงทุน (ปี)", min_value=18, max_value=50, value=24, step=1)
retirement_age = st.sidebar.number_input("อายุเกษียณ (ปี)", min_value=50, max_value=70, value=60, step=1)
life_expectancy = st.sidebar.number_input("อายุขัยเฉลี่ย (ปี)", min_value=70, max_value=100, value=85, step=1)

st.sidebar.markdown("### 💰 รายได้และการลงทุนแบบ DCA")
starting_salary = st.sidebar.number_input("เงินเดือนเริ่มต้น (บาท)", min_value=15000, max_value=500000, value=90000, step=5000)
salary_growth = st.sidebar.slider("อัตราการเติบโตของเงินเดือนต่อปี (%)", min_value=0.0, max_value=15.0, value=5.0, step=0.5) / 100.0
dca_rate = st.sidebar.slider("อัตราการลงทุน DCA (% ของเงินเดือน)", min_value=5.0, max_value=50.0, value=20.0, step=1.0) / 100.0

st.sidebar.markdown("### 📈 สมมติฐานตลาดทุน")
sp500_return = st.sidebar.slider("อัตราผลตอบแทนคาดหวัง S&P500 ต่อปี (%)", min_value=4.0, max_value=15.0, value=10.0, step=0.5) / 100.0
sp500_dividend = st.sidebar.slider("อัตราเงินปันผลของ S&P500 (%)", min_value=0.5, max_value=5.0, value=1.5, step=0.1) / 100.0
dividend_wht = st.sidebar.slider("ภาษีหัก ณ ที่จ่ายจากเงินปันผลสหรัฐ (%)", min_value=0.0, max_value=30.0, value=15.0, step=5.0) / 100.0
inflation_rate = st.sidebar.slider("อัตราเงินเฟ้อไทย (%)", min_value=0.0, max_value=5.0, value=2.0, step=0.5) / 100.0

st.sidebar.markdown("### ⚙️ ค่าธรรมเนียมผลิตภัณฑ์")

st.sidebar.markdown("**หุ้นสหรัฐฯ / US ETF (ลงทุนตรงผ่าน Dime/InnovestX)**")
dime_commission = st.sidebar.slider(
    "ค่าคอมมิชชันโบรกเกอร์ (%)", 
    min_value=0.0, 
    max_value=1.0, 
    value=0.00, 
    step=0.05,
    help="Dime! ฟรีค่าคอมมิชชัน 1 รายการต่อเดือน (0.00%) รายการต่อไปคิด 0.15% (สำหรับยอดเทรด < $3k) ในขณะที่ InnovestX มีค่าธรรมเนียมขั้นต่ำ $4.99 USD ซึ่งเทียบเท่ากับ ~1% ถึง 3.5% สำหรับยอด DCA ทั่วไป (฿5k - ฿18k)"
) / 100.0
fx_spread = st.sidebar.slider(
    "ส่วนต่างอัตราแลกเปลี่ยน (FX Spread) (%)", 
    min_value=0.0, 
    max_value=1.0, 
    value=0.30, 
    step=0.05,
    help="ส่วนต่างหรือสเปรดแลกเงินที่โบรกเกอร์เรียกเก็บ มักจะอยู่ระหว่าง 0.20% ถึง 0.35% ในเวลาทำการ"
) / 100.0
us_etf_ter = st.sidebar.slider(
    "ค่าใช้จ่ายกองทุนสหรัฐฯ (e.g. VOO) (%)", 
    min_value=0.01, 
    max_value=0.20, 
    value=0.03, 
    step=0.01,
    help="ค่าใช้จ่ายรายปีของกองทุนหลักในสหรัฐฯ เช่น VOO คิดค่าธรรมเนียมที่ 0.03% ต่อปี หรือ IVV คิดที่ 0.03% ต่อปี"
) / 100.0

st.sidebar.markdown("**กองทุนรวมไทย (S&P500 ทั่วไป)**")
thai_fund_ter = st.sidebar.slider(
    "ค่าธรรมเนียมรวมกองทุนไทย (TER) (%)", 
    min_value=0.1, 
    max_value=2.0, 
    value=0.64, 
    step=0.01,
    help="K-US500X-A มีค่าใช้จ่ายประมาณ ~0.64% ต่อปี ส่วน SCBS&P500 อยู่ที่ ~1.10% ต่อปี"
) / 100.0
thai_fund_front_fee = st.sidebar.slider(
    "ค่าธรรมเนียมการซื้อ (Front-end Fee) (%)", 
    min_value=0.0, 
    max_value=1.5, 
    value=0.0, 
    step=0.1,
    help="K-US500X-A ไม่มีค่าธรรมเนียมการซื้อ (0.0%) ส่วน SCBS&P500 เรียกเก็บที่ 0.50%"
) / 100.0

st.sidebar.markdown("**กองทุนลดหย่อนภาษี RMF (S&P500)**")
rmf_ter = st.sidebar.slider(
    "ค่าธรรมเนียมรวมกองทุน RMF (TER) (%)", 
    min_value=0.1, 
    max_value=2.0, 
    value=0.60, 
    help="K-US500XRMF อยู่ที่ประมาณ ~0.60% ต่อปี (หรือ 0.54%) ส่วน SCBRMS&P500 อยู่ที่ ~0.86% ต่อปี"
) / 100.0
reinvest_rmf_tax_savings = st.sidebar.checkbox("นำเงินคืนภาษีจาก RMF กลับไปลงทุนต่อ", value=True)

st.sidebar.markdown("**สิทธิลดหย่อนภาษีอื่น (แชร์เพดานร่วม 5 แสนบาท)**")
pvd_rate = st.sidebar.slider("อัตราเงินสะสมกองทุนสำรองเลี้ยงชีพ (PVD) (%)", min_value=0.0, max_value=15.0, value=0.0, step=1.0) / 100.0
ssf_contribution = st.sidebar.number_input("จำนวนเงินลงทุน SSF อื่นๆ ต่อปี (บาท)", min_value=0, max_value=200000, value=0, step=10000)

# ----------------- MAIN VIEW -----------------
st.markdown('<div class="main-header">เครื่องมือคำนวณเปรียบเทียบการลงทุน S&P 500 แบบ DCA สำหรับคนไทย</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">โมเดลคณิตศาสตร์เปรียบเทียบเชิงลึกระหว่างการลงทุนตรงหุ้นสหรัฐฯ (US ETF), กองทุนรวมดัชนีไทย และกองทุน RMF ในธีม S&P 500</div>', unsafe_allow_html=True)

# Run simulation
result = run_simulation(
    start_age=start_age,
    retirement_age=retirement_age,
    life_expectancy=life_expectancy,
    starting_salary=starting_salary,
    salary_growth=salary_growth,
    dca_rate=dca_rate,
    sp500_return=sp500_return,
    sp500_dividend=sp500_dividend,
    dividend_wht=dividend_wht,
    us_etf_ter=us_etf_ter,
    dime_commission=dime_commission,
    fx_spread=fx_spread,
    thai_fund_ter=thai_fund_ter,
    thai_fund_front_fee=thai_fund_front_fee,
    rmf_ter=rmf_ter,
    pvd_rate=pvd_rate,
    ssf_contribution=ssf_contribution,
    reinvest_rmf_tax_savings=reinvest_rmf_tax_savings,
    retirement_annual_withdrawal_real=0.0,
    inflation_rate=inflation_rate
)

df_accum = result['df_accumulation']
df_ret = result['df_retirement']
final_accum = result['final_accum']
# Calculate final status
etf_val_retire = final_accum['ETF']
thai_val_retire = final_accum['Thai_Fund']
rmf_val_retire = final_accum['RMF']
hybrid_val_retire = final_accum['Hybrid']

# Determine optimal excess vehicle for the hybrid strategy card subtitle
if final_accum['Hybrid_Excess_Thai'] > 0 or final_accum['Hybrid_Excess_ETF'] > 0:
    if final_accum['Hybrid_Thai'] >= final_accum['Hybrid_ETF']:
        hybrid_badge = '<span class="badge" style="background-color:rgba(139, 92, 246, 0.15); color:#8B5CF6;">ส่วนเกินลงทุนกองทุนไทย</span>'
        hybrid_desc = "เต็มสิทธิ RMF + ส่วนเกินลงกองทุนดัชนีไทย (ยกเว้นภาษี)"
    else:
        hybrid_badge = '<span class="badge" style="background-color:rgba(16, 185, 129, 0.15); color:#10B981;">ส่วนเกินลงทุน US ETF</span>'
        hybrid_desc = "เต็มสิทธิ RMF + ส่วนเกินลงตรง US ETF (ชำระภาษีเมื่อนำกลับ)"
else:
    hybrid_badge = '<span class="badge" style="background-color:rgba(245, 158, 11, 0.15); color:#F59E0B;">ลงทุน RMF ทั้งหมด</span>'
    hybrid_desc = "เงินลงทุนไม่เกินสิทธิลดหย่อน ลงทุน RMF ทั้งพอร์ต"

# KPI Cards row
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-label"><span class="badge badge-etf">Dime / InnovestX</span> ลงทุนตรง US ETF (VOO)</div>
        <div class="stat-value">฿{etf_val_retire:,.0f} <span style="font-size:0.9rem; font-weight:300; color:#9CA3AF;">พอร์ตรวม</span></div>
        <div class="stat-sub-red" style="font-weight:600; margin-top:0.25rem;">฿{final_accum['ETF_Net_Liquidation']:,.0f} <span style="font-size:0.8rem; font-weight:300; color:#EF4444;">สุทธิหลังภาษี</span></div>
        <div style="font-size:0.8rem; margin-top:0.5rem; color:#9CA3AF;">ต้องเสียภาษีเงินได้อัตราก้าวหน้าเมื่อนำเงินกลับไทย</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-label"><span class="badge badge-thai">Thai Fund</span> กองทุนรวมดัชนี S&P 500 ไทย</div>
        <div class="stat-value">฿{thai_val_retire:,.0f}</div>
        <div class="stat-sub" style="color:#10B981; font-weight:600;">ยกเว้นภาษีกำไร 100%</div>
        <div style="font-size:0.8rem; margin-top:0.5rem; color:#9CA3AF;">ไม่มีภาษีกำไรจากส่วนต่างราคา (Capital Gains) เมื่อขายคืน</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-label"><span class="badge badge-rmf">RMF</span> กองทุนลดหย่อนภาษี RMF S&P 500</div>
        <div class="stat-value">฿{rmf_val_retire:,.0f}</div>
        <div class="stat-sub" style="color:#10B981; font-weight:600;">ยกเว้นภาษี 100% + หักภาษีเงินได้</div>
        <div style="font-size:0.8rem; margin-top:0.5rem; color:#9CA3AF;">รวมยอดประหยัดเงินคืนภาษีสะสม ฿{df_accum['Tax_Savings'].sum():,.0f}</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown(f"""
    <div class="stat-card" style="border: 1px solid rgba(59, 130, 246, 0.4); background: rgba(59, 130, 246, 0.05);">
        <div class="stat-label">{hybrid_badge} แผนผสม (Hybrid)</div>
        <div class="stat-value" style="color:#3B82F6;">฿{hybrid_val_retire:,.0f}</div>
        <div class="stat-sub" style="color:#3B82F6; font-weight:600;">พอร์ตเกษียณประสิทธิภาพสูงสุด</div>
        <div style="font-size:0.8rem; margin-top:0.5rem; color:#9CA3AF;">{hybrid_desc}</div>
    </div>
    """, unsafe_allow_html=True)

st.write("")
st.write("")

# Create Tabs
tab_names = ["💡 การวิเคราะห์เชิงกลยุทธ์", "📈 การเติบโตของพอร์ต", "📊 ตารางข้อมูลรายปี", "📝 คู่มือภาษีและค่าธรรมเนียม"]
active_tab = st.radio("เลือกโหมดการดูข้อมูล", tab_names, horizontal=True, label_visibility="collapsed")

# ----------------- TAB 1: STRATEGIC ANALYSIS -----------------
if active_tab == "💡 การวิเคราะห์เชิงกลยุทธ์":
    st.markdown("### 💡 เจาะลึกมุมมองการวางแผนทางการเงิน")
    
    # Simple Recommendation Engine
    best_retire_val = max(etf_val_retire, thai_val_retire, rmf_val_retire, hybrid_val_retire)
    
    st.markdown("#### วิธีไหนเหมาะและคุ้มค่าที่สุดสำหรับคุณ?")
    
    col_left, col_right = st.columns([2, 1])
    
    with col_left:
        # Determine recommendations based on simulation output
        if hybrid_val_retire == best_retire_val and (final_accum['Hybrid_Excess_Thai'] > 0 or final_accum['Hybrid_Excess_ETF'] > 0):
            st.success(f"🏆 **แผนผสม Hybrid (Max RMF + ส่วนต่างลงสินทรัพย์ที่ใช่) คือทางเลือกที่ฉลาดและคุ้มค่าที่สุด!**")
            st.markdown(f"""
            เนื่องจากรายได้ของคุณเติบโตและสัดส่วนเงินลงทุน DCA ของคุณ (สะสมรวมเป็นรายปี) มีจำนวนที่ **เกินกว่าเกณฑ์สิทธิลดหย่อนภาษี RMF สูงสุด (฿500,000 ต่อปี)** การเลือกแผนผสม Hybrid จึงสร้างผลประโยชน์สูงสุด:
            
            *   **การหักภาษีเต็มโควตา:** ลงทุนเต็มวงเงิน RMF ฿500,000 แรกเพื่อรับสิทธิคืนภาษีสูงสุด (รวมประหยัดภาษีได้ **฿{df_accum['Tax_Savings'].sum():,.0f}**)
            *   **บริหารส่วนเกินอย่างมีประสิทธิภาพ:** ส่วนที่เกินสิทธิลดหย่อนภาษี ถูกนำไปลงทุนในสินทรัพย์ที่มีประสิทธิภาพสูงสุด คือ **{ "กองทุนรวมดัชนีไทย" if final_accum['Hybrid_Thai'] >= final_accum['Hybrid_ETF'] else " US ETF โดยตรง" }** เพื่อหลีกเลี่ยงการล็อกเงินใน RMF โดยเปล่าประโยชน์
            *   **มูลค่าพอร์ตสุทธิปลายทางสูงสุด:** ได้รับพอร์ตสุทธิหลังชำระภาษีและสเปรดแลกเงินสูงถึง **฿{hybrid_val_retire:,.0f}** สูงกว่าทุกกลยุทธ์อื่น
            """)
        elif rmf_val_retire == best_retire_val:
            st.success(f"🏆 **กองทุน RMF S&P 500 คือทางเลือกที่ดีที่สุดสำหรับโปรไฟล์ของคุณ!**")
            st.markdown(f"""
            เนื่องจากระดับเงินเดือนเริ่มต้นของคุณอยู่ที่ **฿{starting_salary:,.0f}/เดือน** (ฐานรายได้ที่เสียภาษีอยู่ใน **อัตราภาษี 20%** ในปีที่ 1) การใช้สิทธิลดหย่อนภาษีจาก RMF จึงให้ผลประโยชน์ที่คุ้มค่าสูงสุดในทันที:
            
            *   **เงินคืนภาษีสะสมทั้งหมด:** ช่วยให้คุณประหยัดภาษีได้สูงถึง **฿{df_accum['Tax_Savings'].sum():,.0f}** ตลอดระยะเวลาทำงาน
            *   **พลังแห่งดอกเบี้ยทบต้น:** เมื่อนำเงินภาษีที่ประหยัดได้ไปลงทุนต่อ (สมมติฐานผลตอบแทน {sp500_return*100:.1f}%) จะช่วยเพิ่มพอร์ตเงินเกษียณขึ้นถึง **฿{rmf_val_retire - thai_val_retire:,.0f}** เมื่อเปรียบเทียบกับกองทุนรวมไทยแบบปกติ
            *   **ถอนเงินภาษีเป็นศูนย์**: เมื่อถือครองจนถึงอายุ 55 ปีบริบูรณ์ตามเงื่อนไข กำไรทั้งหมดจะได้รับการยกเว้นภาษีอย่างสมบูรณ์แบบ
            """)
        elif etf_val_retire == best_retire_val:
            st.success(f"🏆 **การลงทุนตรงหุ้นสหรัฐฯ (US ETF) ได้มูลค่าสูงสุด (ก่อนหักภาษี)!**")
            st.markdown(f"""
            เนื่องจากค่าธรรมเนียมรายปีที่ต่ำมาก ({us_etf_ter*100:.3f}% สำหรับ VOO เทียบกับ {thai_fund_ter*100:.2f}% สำหรับกองทุนดัชนีไทย) ทำให้พอร์ตเติบโตได้สูงสุดบนกระดาษ 
            อย่างไรก็ตาม มีความเสี่ยงและภาระทางภาษีที่สำคัญดังนี้:
            
            1.  **ภาษีเงินได้ต่างประเทศ:** กำไรทั้งหมดที่คุณนำกลับเข้าสู่ประเทศไทยจะถูกคิดภาษีในอัตราก้าวหน้าตามฐานภาษีเงินได้ของคุณ
            2.  **การโอนเงินก้อนใหญ่ในปีเกษียณ:** หากคุณขายและโอนเงินทั้งหมดกลับไทยพร้อมกันในปีเกษียณ คุณจะต้องชำระภาษีเงินได้สูงถึง **฿{final_accum['ETF_Liquidation_Tax']:,.0f}** ทำให้พอร์ตสุทธิหลังหักภาษีลดลงเหลือเพียง **฿{final_accum['ETF_Net_Liquidation']:,.0f}** (ซึ่งน้อยกว่าทุกทางเลือกอื่น!)
            """)
        else:
            st.success(f"🏆 **กองทุนรวมไทยแบบปกติคือผู้ชนะในพอร์ตสุทธิ!**")
            st.markdown(f"""
            กองทุนรวมดัชนีไทยให้ผลตอบแทนสุทธิหลังภาษีสูงสุด เนื่องจากหลีกเลี่ยงภาระภาษีเงินได้ต่างประเทศของการลงทุนตรง และมีสภาพคล่องสูงกว่า RMF ที่ต้องรออายุ 55 ปี
            """)
            
        # Add final value bar chart
        fig_bar = go.Figure()
        fig_bar.add_trace(go.Bar(
            x=['US ETF ลงทุนตรง (ก่อนภาษี)', 'US ETF ลงทุนตรง (สุทธิหลังภาษี)', 'กองทุนรวมไทย S&P500', 'กองทุน RMF (S&P500)', 'แผนผสม Hybrid (ที่ดีที่สุด)'],
            y=[etf_val_retire, final_accum['ETF_Net_Liquidation'], thai_val_retire, rmf_val_retire, hybrid_val_retire],
            marker_color=['#10B981', '#EF4444', '#8B5CF6', '#F59E0B', '#3B82F6'],
            text=[f"฿{etf_val_retire:,.0f}", f"฿{final_accum['ETF_Net_Liquidation']:,.0f}", f"฿{thai_val_retire:,.0f}", f"฿{rmf_val_retire:,.0f}", f"฿{hybrid_val_retire:,.0f}"],
            textposition='auto',
        ))
        fig_bar.update_layout(
            title=f"มูลค่าพอร์ตสุทธิ ณ ปีที่เกษียณอายุ (อายุ {retirement_age} ปี)",
            yaxis_title="มูลค่าสุทธิ (บาท)",
            template="plotly_dark" if st.get_option("theme.base") == "dark" else "plotly_white"
        )
        st.plotly_chart(fig_bar, use_container_width=True)

        st.markdown("#### ตารางสรุปการเปรียบเทียบเชิงลึก")
        
        # Summary Table
        summary_data = {
            'หัวข้อหลัก': [
                'มูลค่าพอร์ตปลายทางก่อนหักภาษี',
                'ภาษีหัก ณ ที่จ่ายจากเงินปันผลสหรัฐฯ (WHT)',
                'ค่าธรรมเนียมบริหารจัดการรายปี (TER)',
                'ค่าคอมมิชชันซื้อขาย / ค่าธรรมเนียมแรกเข้า',
                'สิทธิประโยชน์หักลดหย่อนภาษีรายปี',
                'ภาษีกำไรส่วนต่างราคา (Capital Gains) เมื่อขาย',
                'มูลค่าพอร์ตสุทธิหลังหักภาษีและส่วนต่างแลกเงิน'
            ],
            'US ETF ลงทุนตรง (Dime/VOO)': [
                f"฿{etf_val_retire:,.0f}",
                '15% ของปันผล (ภาษีหัก ณ ที่จ่ายสหรัฐฯ)',
                f"{us_etf_ter*100:.3f}% (ต่ำมาก)",
                f"ฟรี 1 ครั้ง/เดือน (รายการถัดไป {dime_commission*100:.2f}%)",
                'ไม่มีสิทธิลดหย่อนภาษี',
                'อัตราก้าวหน้า (0-35%) หากนำเงินกลับไทย',
                f"฿{final_accum['ETF_Net_Liquidation']:,.0f}"
            ],
            'กองทุนรวมไทย (S&P500)': [
                f"฿{thai_val_retire:,.0f}",
                '15% ของปันผล (จัดการโดยบลจ.ไทย)',
                f"{thai_fund_ter*100:.2f}% (รวมค่ากองทุนหลัก)",
                f"{thai_fund_front_fee*100:.2f}% front-end fee",
                'ไม่มีสิทธิลดหย่อนภาษี',
                '0% (ได้รับยกเว้นภาษีกำไรบุคคลธรรมดา)',
                f"฿{thai_val_retire:,.0f}"
            ],
            'กองทุน RMF (S&P500)': [
                f"฿{rmf_val_retire:,.0f}",
                '15% ของปันผล (จัดการโดยบลจ.ไทย)',
                f"{rmf_ter*100:.2f}% (รวมค่ากองทุนหลัก)",
                '0%',
                'ลดหย่อนสูงสุด 30% ของรายได้ (ไม่เกิน 5 แสนบาท)',
                '0% (ได้รับยกเว้นภาษีตามเงื่อนไข RMF)',
                f"฿{rmf_val_retire:,.0f}"
            ],
            'แผนผสม Hybrid (ที่ดีที่สุด)': [
                f"฿{hybrid_val_retire:,.0f}",
                '15% ของปันผล (จัดการตามสัดส่วน)',
                f"RMF ({rmf_ter*100:.2f}%) + ส่วนเกิน ({thai_fund_ter*100:.2f}% หรือ {us_etf_ter*100:.2f}%)",
                '0% (RMF) + ส่วนเกิน (ตามสินทรัพย์ที่เลือก)',
                'ลดหย่อนเต็มสิทธิ RMF (สูงสุด 5 แสนบาท/ปี)',
                '0% บน RMF และส่วนเกินไทย หรือมีภาษีเฉพาะส่วนเกินของ US ETF',
                f"฿{hybrid_val_retire:,.0f}"
            ]
        }
        st.table(pd.DataFrame(summary_data))
        
    with col_right:
        st.markdown("""
        <div style="background-color:rgba(59, 130, 246, 0.08); border-left: 4px solid #3B82F6; padding: 1rem; border-radius: 4px;">
            <h5 style="margin-top:0; color:#3B82F6;">🔑 หัวใจสำคัญของการวางแผนการเงิน</h5>
            <p style="font-size:0.9rem; margin-bottom:0.5rem;">
                <b>1. สำหรับผู้ที่มีฐานภาษีสูง:</b> หากเงินเดือนเริ่มต้นเกิน ฿50,000 การลงทุนผ่าน <b>RMF</b> ถือเป็นอันดับแรกที่ควรทำ เงินคืนภาษี 10%-30% ในแต่ละปีคือผลตอบแทนการลงทุนก้อนแรกที่ไม่มีความเสี่ยง และเมื่อนำไปทบต้นต่อหลายสิบปีจะสร้างพลังดอกเบี้ยทบต้นที่มหาศาล
            </p>
            <p style="font-size:0.9rem; margin-bottom:0.5rem;">
                <b>2. การบริหารโควตาลดหย่อนภาษี:</b> เมื่อสัดส่วน DCA 20% เกินกว่าเพดาน ฿500,000 ของ RMF (ที่แชร์ร่วมกับ PVD/SSF) แนะนำให้ลงทุน ฿500,000 แรกใน RMF ให้เต็มสิทธิ แล้วนำเงินส่วนเกินที่เหลือไปจัดสรรในการลงทุนตรง <b>US ETF</b> หรือ <b>กองทุนรวมไทยแบบปกติ</b>
            </p>
            <p style="font-size:0.9rem; margin-bottom:0.5rem;">
                <b>3. ภาระทางเอกสารและความเสี่ยงมรดก:</b> แม้การลงทุนตรงใน US ETF จะมีค่าธรรมเนียมต่ำที่สุด แต่มาพร้อมกับภาระการทำบัญชีจัดเก็บหลักฐานต้นทุนเพื่อยื่นภาษีกรมสรรพากรเมื่อนำเงินกลับไทย รวมถึงความเสี่ยงจากภาษีมรดกสหรัฐฯ (US Estate Tax) ที่เรียกเก็บสูงถึง 40% ในยอดที่เกิน $60,000 ดอลลาร์ ในขณะที่กองทุนไทยและ RMF ไม่มีภาระและความเสี่ยงเหล่านี้
            </p>
        </div>
        """, unsafe_allow_html=True)

# ----------------- TAB 2: GROWTH OVER TIME -----------------
elif active_tab == "📈 การเติบโตของพอร์ต":
    st.markdown("### 📈 พัฒนาการและการเติบโตของพอร์ตการลงทุน (ช่วงสะสมเงินทำงาน)")
    
    # Create a copy for plotting to inject the final liquidation tax drop
    df_plot = df_accum.copy()
    
    # We create a series for ETF that drops at the last point to reflect the tax
    etf_plot_values = df_plot['ETF_Value'].values.copy()
    if len(etf_plot_values) > 0:
        etf_plot_values[-1] = df_plot['ETF_Value_Net'].iloc[-1]
    df_plot['ETF_Plot_Value'] = etf_plot_values
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=df_plot['Age'], 
        y=df_plot['RMF_Value'], 
        mode='lines', 
        name='กองทุน RMF (S&P 500)', 
        line=dict(color='#F59E0B', width=3),
        hovertemplate='อายุ %{x} ปี<br>มูลค่า RMF: ฿%{y:,.0f}'
    ))
    
    fig.add_trace(go.Scatter(
        x=df_plot['Age'], 
        y=df_plot['ETF_Plot_Value'], 
        mode='lines+markers', 
        name='ลงทุนตรง US ETF (VOO)', 
        line=dict(color='#10B981', width=3),
        marker=dict(size=[0]*(len(df_plot)-1) + [8], color='#EF4444'),
        hovertemplate='อายุ %{x} ปี<br>มูลค่า US ETF: ฿%{y:,.0f}'
    ))
    
    fig.add_trace(go.Scatter(
        x=df_plot['Age'], 
        y=df_plot['Thai_Fund_Value'], 
        mode='lines', 
        name='กองทุนรวมไทย (S&P 500)', 
        line=dict(color='#8B5CF6', width=3),
        hovertemplate='อายุ %{x} ปี<br>มูลค่ากองทุนไทย: ฿%{y:,.0f}'
    ))
    
    fig.add_trace(go.Scatter(
        x=df_plot['Age'], 
        y=df_plot['Hybrid_Value'], 
        mode='lines', 
        name='แผนผสม Hybrid (Max RMF + ส่วนที่ดีที่สุด)', 
        line=dict(color='#3B82F6', width=4, dash='dash'),
        hovertemplate='อายุ %{x} ปี<br>มูลค่า Hybrid: ฿%{y:,.0f}'
    ))
    
    fig.update_layout(
        title="เปรียบเทียบมูลค่าพอร์ตสะสมการลงทุน DCA (อายุ 24 ปี ถึงปีเกษียณ)",
        xaxis_title="อายุผู้ลงทุน (ปี)",
        yaxis_title="มูลค่าพอร์ตการลงทุน (บาท)",
        hovermode="x unified",
        legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01),
        template="plotly_dark" if st.get_option("theme.base") == "dark" else "plotly_white"
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Cumulative Salary and DCA stats
    total_dca_invested = df_accum['DCA_Annual'].sum()
    st.info(f"💡 ตลอดระยะเวลาทำงาน **{retirement_age - start_age} ปี** รายได้รวมของคุณคือ **฿{df_accum['Salary'].sum():,.0f}** และคิดเป็นยอดเงินต้นที่สะสมเพื่อลงทุนแบบ DCA รวมทั้งสิ้น **฿{total_dca_invested:,.0f}**")

# ----------------- TAB 3: YEAR-BY-YEAR DATA -----------------
elif active_tab == "📊 ตารางข้อมูลรายปี":
    st.markdown("### 📊 ตารางจำลองข้อมูลรายปีโดยละเอียด")
    
    df_display = df_accum.copy()
    
    # Rename columns for localized display
    df_display = df_display.rename(columns={
        'Age': 'อายุ',
        'Year': 'ปีที่',
        'Salary': 'รายได้ต่อปี',
        'DCA_Annual': 'ยอดลงทุน DCA ต่อปี',
        'Tax_No_RMF': 'ภาษีปกติ (ไม่มี RMF)',
        'Tax_Savings': 'เงินประหยัดภาษีรายปี',
        'ETF_Value': 'มูลค่าพอร์ต ETF (ก่อนภาษี)',
        'ETF_Value_Net': 'มูลค่าพอร์ต ETF (สุทธิหลังภาษี)',
        'Thai_Fund_Value': 'มูลค่าพอร์ต กองทุนไทย',
        'RMF_Value': 'มูลค่าพอร์ต RMF สะสม',
        'Hybrid_Value': 'มูลค่าพอร์ต Hybrid สะสม'
    })
    
    # Formatting
    df_display['รายได้ต่อปี'] = df_display['รายได้ต่อปี'].map('฿{:,.0f}'.format)
    df_display['ยอดลงทุน DCA ต่อปี'] = df_display['ยอดลงทุน DCA ต่อปี'].map('฿{:,.0f}'.format)
    df_display['ภาษีปกติ (ไม่มี RMF)'] = df_display['ภาษีปกติ (ไม่มี RMF)'].map('฿{:,.0f}'.format)
    df_display['เงินประหยัดภาษีรายปี'] = df_display['เงินประหยัดภาษีรายปี'].map('฿{:,.0f}'.format)
    df_display['มูลค่าพอร์ต ETF (ก่อนภาษี)'] = df_display['มูลค่าพอร์ต ETF (ก่อนภาษี)'].map('฿{:,.0f}'.format)
    df_display['มูลค่าพอร์ต ETF (สุทธิหลังภาษี)'] = df_display['มูลค่าพอร์ต ETF (สุทธิหลังภาษี)'].map('฿{:,.0f}'.format)
    df_display['มูลค่าพอร์ต กองทุนไทย'] = df_display['มูลค่าพอร์ต กองทุนไทย'].map('฿{:,.0f}'.format)
    df_display['มูลค่าพอร์ต RMF สะสม'] = df_display['มูลค่าพอร์ต RMF สะสม'].map('฿{:,.0f}'.format)
    df_display['มูลค่าพอร์ต Hybrid สะสม'] = df_display['มูลค่าพอร์ต Hybrid สะสม'].map('฿{:,.0f}'.format)
    
    st.dataframe(df_display[['อายุ', 'ปีที่', 'รายได้ต่อปี', 'ยอดลงทุน DCA ต่อปี', 'ภาษีปกติ (ไม่มี RMF)', 'เงินประหยัดภาษีรายปี', 'มูลค่าพอร์ต ETF (ก่อนภาษี)', 'มูลค่าพอร์ต ETF (สุทธิหลังภาษี)', 'มูลค่าพอร์ต กองทุนไทย', 'มูลค่าพอร์ต RMF สะสม', 'มูลค่าพอร์ต Hybrid สะสม']], use_container_width=True)
elif active_tab == "📝 คู่มือภาษีและค่าธรรมเนียม":
    st.markdown("### 📝 คู่มือภาษีเงินได้บุคคลธรรมดาของไทยและสิทธิประโยชน์การออม")
    
    col_t1, col_t2 = st.columns(2)
    
    with col_t1:
        st.markdown(f"""
        #### 📊 อัตราภาษีเงินได้บุคคลธรรมดา (แบบขั้นบันไดของไทย)
        *   **฿0 – ฿150,000:** 0% (ได้รับยกเว้นภาษี)
        *   **฿150,001 – ฿300,000:** 5%
        *   **฿300,001 – ฿500,000:** 10%
        *   **฿500,001 – ฿750,000:** 15%
        *   **฿750,001 – ฿1,000,000:** 20%
        *   **฿1,000,001 – ฿2,000,000:** 25%
        *   **฿2,000,001 – ฿5,000,000:** 30%
        *   **฿5,000,001 ขึ้นไป:** 35%
        
        #### ⚖️ ค่าใช้จ่ายและค่าลดหย่อนพื้นฐานที่นำมาคำนวณ
        *   **หักค่าใช้จ่ายส่วนตัว:** 50% ของรายได้เงินเดือน แต่ไม่เกิน ฿100,000
        *   **หักค่าลดหย่อนส่วนบุคคล:** ฿60,000
        *   **หักค่าประกันสังคม (SSF):** สูงสุด ฿9,000 (คำนวณจาก ฿750 ต่อเดือน)
        
        #### 🛡️ เงื่อนไขทางภาษีของกองทุน RMF
        *   **สิทธิประโยชน์หักลดหย่อน:** ซื้อเพื่อลดหย่อนภาษีได้สูงสุดไม่เกิน **30%** ของรายได้พึงประเมินที่ต้องเสียภาษี
        *   **เพดานรวม (Combined Cap):** เมื่อรวม RMF กับกองทุนการออมอื่นๆ (กองทุนสำรองเลี้ยงชีพ PVD, กองทุน SSF, ประกันชีวิตแบบบำนาญ, กองทุน กอช.) ต้องไม่เกิน **฿500,000** ต่อปีภาษี
        *   **เงื่อนไขการถือครองหน่วยลงทุน:**
            *   **ลงทุนอย่างต่อเนื่อง:** ต้องลงทุนต่อเนื่องทุกปี (หรือปีเว้นปีได้)
            *   **เงื่อนไขเวลา:** ต้องถือครองลงทุนไม่ต่ำกว่า **5 ปีเต็ม** และไถ่ถอนได้เมื่อมีอายุครบ **55 ปีบริบูรณ์** ขึ้นไป
            *   **หากผิดเงื่อนไข:** จะต้องคืนสิทธิประโยชน์ทางภาษีที่ได้รับย้อนหลังทั้งหมดพร้อมเบี้ยปรับ
        """)
        
    with col_t2:
        st.markdown("""
        #### 🌎 ภาษีเงินได้ต่างประเทศสำหรับลงทุนตรง (ป. 161/2566 & ป. 162/2566)
        *   **ผู้อยู่ในเกณฑ์เสียภาษี:** บุคคลธรรมดาที่เป็นผู้อยู่อาศัยในประเทศไทย (พำนักในไทยรวมกันตั้งแต่ 180 วันขึ้นไปในปีภาษีนั้น)
        *   **เงื่อนไขการจัดเก็บ:** เมื่อมีการนำเงินได้ที่เกิดขึ้นจากหน้าที่งาน/กิจการ หรือผลตอบแทนทรัพย์สินต่างประเทศ (เช่น กำไรขายหุ้น, เงินปันผล) เข้ามาในไทย **ไม่ว่าจะนำเข้ามาในปีภาษีใดก็ตาม**
        *   **อัตราภาษี:** คิดตามอัตราภาษีก้าวหน้าของไทย (0% - 35%) ในปีภาษีที่นำเงินเข้ามาในไทย
        *   **เงินต้น vs. กำไร:** สรรพากรเรียกเก็บภาษีเฉพาะส่วนที่เป็น **กำไร (Capital Gains)** เท่านั้น เงินต้นจะไม่มีการหักภาษี
        *   **⚠️ หน้าที่การทำบัญชีของผู้ลงทุน:** เนื่องจากสรรพากรแยกเก็บเฉพาะกำไร **ผู้ลงทุนมีหน้าที่จัดทำสมุดบัญชี/หลักฐานประวัติการลงทุนโดยละเอียด** เพื่อพิสูจน์ฐานเงินต้นและกำไร (เช่น วันที่โอน, อัตราแลกเปลี่ยน, ราคาซื้อ-ขาย) หากไม่มีหลักฐานชัดเจน สรรพากรมีสิทธิประเมินภาษีจาก **ยอดโอนกลับทั้งหมด** เป็นรายได้!
        
        #### ⚠️ ความเสี่ยงด้านภาษีมรดกสหรัฐฯ (US Estate Tax)
        *   **ทรัพย์สินที่ตั้งอยู่ในสหรัฐฯ (U.S.-Situs Assets):** หุ้นและ ETF ที่จดทะเบียนในตลาดสหรัฐฯ โดยตรง (เช่น VOO, IVV, SPY) ถือเป็นสินทรัพย์ที่ตั้งอยู่ในสหรัฐฯ ภายใต้กฎหมายสหรัฐฯ
        *   **เพดานยกเว้นของชาวต่างชาติ:** สำหรับนักลงทุนที่ไม่ใช่สัญชาติสหรัฐฯ และไม่ได้อยู่อาศัยในสหรัฐฯ (Non-Resident Alien: NRA) กฎหมายกำหนดให้หักยกเว้นภาษีมรดกเพียง **$60,000 USD** เท่านั้น (ประมาณ ฿2,100,000)
        *   **อัตราภาษีมรดกสหรัฐฯ:** ในกรณีที่ผู้ลงทุนเสียชีวิต ทรัพย์สินที่เกินกว่า $60,000 USD จะต้องเสียภาษีมรดกให้แก่กรมสรรพากรสหรัฐฯ (IRS) ในอัตราก้าวหน้าเริ่มที่ 18% สูงสุดถึง **40%**
        *   **ความได้เปรียบของกองทุนไทย:** เนื่องจากกองทุนรวมไทยและ RMF จัดตั้งขึ้นเป็นนิติบุคคลไทย สินทรัพย์ที่คุณถือครองคือ "หน่วยลงทุนสัญชาติไทย" จึงได้รับการยกเว้นภาษีมรดกของสหรัฐฯ **100%** ไม่ว่าพอร์ตจะเติบโตถึงกี่สิบล้านบาทก็ตาม
        """)

    st.markdown("---")
    st.markdown("### 🔍 ตารางเปรียบเทียบค่าธรรมเนียมผลิตภัณฑ์การลงทุน")
    
    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
        st.markdown("""
        **การลงทุนตรงหุ้นต่างประเทศ (Dime! vs. InnovestX)**
        *   **Dime! (เกียรตินาคินภัทร):** ฟรีค่าธรรมเนียมซื้อขาย **1 ครั้งแรกของเดือน** (เหมาะกับผู้สะสม DCA รายเดือน) รายการถัดไปคิด **0.15%** (สำหรับยอดเทรด < $3,000) ไม่มีขั้นต่ำ มีความประหยัดสูงสำหรับรายย่อย
        *   **InnovestX (ไทยพาณิชย์):** ค่าธรรมเนียมซื้อขาย **0.08 USD ต่อหุ้น** แต่มีขั้นต่ำ **$4.99 USD ต่อรายการ** (+ VAT 7%)
        *   **คำเตือนสัดส่วนขั้นต่ำ:** หากคุณสะสม DCA ยอดเงิน ฿10,000 ต่อเดือน (~$285) ค่าธรรมเนียมขั้นต่ำ $4.99 จะคิดเป็นสัดส่วนสูงถึง **1.75%** ของยอดลงทุน หากยอด DCA เป็น ฿5,000 จะคิดเป็นสัดส่วนสูงถึง **3.56%** ทำให้การลงทุนตรงผ่าน InnovestX เสียเปรียบอย่างมากหากลงทุนยอดน้อยต่อครั้ง
        """)
        
    with col_f2:
        st.markdown("""
        **กองทุนรวมไทย S&P 500 (Passive Index)**
        *   **K-US500X-A:** ค่าธรรมเนียมการบริหารจัดการรายปีสะสม (TER) อยู่ที่ประมาณ **~0.60% - 0.64%** ต่อปี ไม่มีค่าธรรมเนียมแรกเข้า (0% Front-end fee) เป็นตัวแทนกองทุนดัชนีที่มีการแข่งขันราคาและเป็นตัวเทียบหลักในระบบ
        *   **SCBS&P500:** TER อยู่ที่ประมาณ **~1.10%** ต่อปี และมีการเรียกเก็บค่าธรรมเนียมแรกเข้า (Front-end fee) ปัจจุบันที่ประมาณ **0.50%** ในการซื้อแต่ละครั้ง
        *   **ความสะดวกทางภาษี:** ได้รับการยกเว้นภาษีกำไร 100% ไม่ต้องดำเนินการยื่นประวัติทางบัญชีหรือตรวจสอบเงินต้นกำไรกับสรรพากรไทยตอนถอนเงินออก
        """)
        
    with col_f3:
        st.markdown("""
        **กองทุนลดหย่อนภาษี RMF S&P 500**
        *   **K-US500XRMF:** TER อยู่ที่ประมาณ **~0.54% - 0.60%** ต่อปี ไม่มีค่าธรรมเนียมการซื้อ
        *   **SCBRMS&P500:** TER อยู่ที่ประมาณ **~0.86%** ต่อปี ไม่มีค่าธรรมเนียมการซื้อ
        *   **สิทธิลดหย่อนที่ทับซ้อน:** ให้ผลตอบแทนทางภาษีคืนตามฐานภาษีของคุณ (5% ถึง 35%) และกำไรทั้งหมดได้รับการยกเว้นภาษีเมื่อถือครองครบเงื่อนไขของทางราชการจนถึงอายุ 55 ปี
        """)

    st.markdown("---")
    st.markdown("### 🧮 ตัวอย่างจำลองคำนวณการหักลดหย่อนภาษีรายปี (ปีที่ 1)")
    
    salary_yr1 = starting_salary * 12
    expense_ded1 = min(0.50 * salary_yr1, 100000)
    personal_all1 = 60000
    social_sec1 = 9000
    
    pvd_ded1 = min(salary_yr1 * pvd_rate, 500000)
    ssf_ded1 = min(ssf_contribution, 200000, salary_yr1 * 0.30)
    
    allowed_pvd1 = pvd_ded1
    allowed_ssf1 = min(ssf_ded1, max(0.0, 500000 - allowed_pvd1))
    
    base_rmf_contrib1 = salary_yr1 * dca_rate
    allowed_rmf1 = min(base_rmf_contrib1, max(0.0, 0.30 * salary_yr1), max(0.0, 500000 - allowed_pvd1 - allowed_ssf1))
    
    taxable_no_rmf1 = max(0.0, salary_yr1 - (expense_ded1 + personal_all1 + social_sec1 + allowed_pvd1 + allowed_ssf1))
    taxable_with_rmf1 = max(0.0, taxable_no_rmf1 - allowed_rmf1)
    
    tax_no_rmf1 = df_accum.iloc[0]['Tax_No_RMF']
    tax_with_rmf1 = df_accum.iloc[0]['Tax_With_RMF']
    tax_savings1 = df_accum.iloc[0]['Tax_Savings']
    
    col_calc1, col_calc2 = st.columns(2)
    
    with col_calc1:
        st.markdown(f"""
        **กรณีที่ไม่ลงทุนลดหย่อนภาษีผ่าน RMF**
        *   **รายได้เงินเดือนพึงประเมินรายปี:** ฿{salary_yr1:,.0f}
        *   **หักค่าใช้จ่ายเหมาจ่าย:** -฿{expense_ded1:,.0f}
        *   **หักค่าลดหย่อนส่วนบุคคล:** -฿{personal_all1:,.0f}
        *   **หักประกันสังคม:** -฿{social_sec1:,.0f}
        *   **หักกองทุนสำรองเลี้ยงชีพ (PVD):** -฿{allowed_pvd1:,.0f}
        *   **หักกองทุน SSF อื่นๆ:** -฿{allowed_ssf1:,.0f}
        *   **เงินได้สุทธิเพื่อนำไปคิดภาษี:** **฿{taxable_no_rmf1:,.0f}**
        *   **ยอดภาษีเงินได้ที่ต้องชำระรายปี:** **฿{tax_no_rmf1:,.0f}**
        """)
        
    with col_calc2:
        st.markdown(f"""
        **กรณีลงทุนตามแผน RMF**
        *   **รายได้เงินเดือนพึงประเมินรายปี:** ฿{salary_yr1:,.0f}
        *   **หักค่าใช้จ่ายและลดหย่อนขั้นต้น (ตามรายการซ้ายมือ):** -฿{expense_ded1 + personal_all1 + social_sec1 + allowed_pvd1 + allowed_ssf1:,.0f}
        *   **หักค่าลดหย่อนกองทุน RMF (จัดสรรตามสิทธิ):** -฿{allowed_rmf1:,.0f}
        *   **เงินได้สุทธิเพื่อนำไปคิดภาษี:** **฿{taxable_with_rmf1:,.0f}**
        *   **ยอดภาษีเงินได้ที่ต้องชำระรายปี:** **฿{tax_with_rmf1:,.0f}**
        """)
        
    st.info(f"💡 **ผลประโยชน์ทางภาษีในปีที่ 1:** เมื่อเปรียบเทียบกลยุทธ์แล้ว การลงทุนผ่าน RMF จะช่วยให้คุณประหยัดและได้รับเงินคืนภาษีสูงถึง **฿{tax_savings1:,.0f}** ในปีแรกของการเริ่มต้นลงทุน! ยอดเงินนี้จะถูกนำกลับเข้าพอร์ตลงทุนอัตโนมัติ (หากติ๊กเลือกการลงทุนคืนต่อ) เพื่อไปสร้างดอกเบี้ยทบต้นระยะยาว")
    
    st.write("")
    with st.expander("🔗 ลิงก์อ้างอิงข้อมูลผลิตภัณฑ์และประกาศข้อกฎหมาย"):
        st.markdown("""
        แหล่งข้อมูลและระเบียบข้อบังคับทางกฎหมายอย่างเป็นทางการที่นำมาอ้างอิงโครงสร้างค่าธรรมเนียมและสมมติฐานทางภาษีในแบบจำลองนี้:
        
        *   **กองทุนหลักสหรัฐฯ (Direct US ETFs):**
            *   [Vanguard VOO S&P 500 ETF](https://investor.vanguard.com/investment-products/etfs/profile/voo) (ข้อมูลค่าใช้จ่ายกองทุน 0.03% ต่อปี)
            *   [iShares IVV S&P 500 ETF](https://www.ishares.com/us/products/239726/ishares-core-sp-500-etf) (ข้อมูลค่าใช้จ่ายกองทุน 0.03% ต่อปี)
        *   **กองทุนรวมไทยและกองทุน RMF (เอกสาร Factsheet & บลจ.):**
            *   [บลจ.กสิกรไทย (KAsset) สารบบข้อมูลกองทุน](https://www.kasikornasset.com) (เพื่อค้นหารายละเอียดกองทุน **K-US500X-A** และ **K-US500XRMF**)
            *   [บลจ.ไทยพาณิชย์ (SCBAM) ข้อมูลกองทุน SCBS&P500](https://www.scbam.com/th/fund/foreign-investment-fund/fund-information/scbs-p500) (TER: ~1.10%, ค่าธรรมเนียมแรกเข้า: 0.50%)
            *   [บลจ.ไทยพาณิชย์ (SCBAM) ข้อมูลกองทุนลดหย่อน RMF SCBRMS&P500](https://www.scbam.com/th/fund/foreign-investment-fund/fund-information/scbrms-p500) (TER: ~0.86%, ค่าธรรมเนียมแรกเข้า: 0%)
        *   **ภาษีเงินได้บุคคลธรรมดาและระเบียบเกณฑ์เงินได้ต่างประเทศ (สรรพากรไทย):**
            *   [กรมสรรพากร (rd.go.th) กฎหมายภาษีอากร](https://www.rd.go.th) (สามารถค้นหาคำสั่งอธิบดีกรมสรรพากรที่ **ป.161/2566** และ **ป.162/2566** เรื่องหลักเกณฑ์ภาษีเงินได้ต่างประเทศ)
        *   **ฐานภาษีบุคคลธรรมดาและเงื่อนไขกองทุน RMF:**
            *   [กรมสรรพากร คู่มือภาษีเงินได้บุคคลธรรมดา](https://www.rd.go.th) (อ้างอิงมาตรา 48 สเกลบันไดภาษี 5-35% และมาตรา 47 เกณฑ์การลดหย่อน RMF 30% สูงสุด 500,000 บาท)
        *   **สิทธิยกเว้นภาษีเงินได้ผู้สูงอายุ (อายุ 65 ปีขึ้นไป):**
            *   [ประมวลรัษฎากร กฎกระทรวง ฉบับที่ 126](https://www.rd.go.th) (อ้างอิงข้อ 2(72) ของกฎกระทรวง ฉบับที่ 126 ในการยกเว้นเงินได้ก้อนแรก 190,000 บาทสำหรับผู้มีอายุตั้งแต่ 65 ปีบริบูรณ์)
        *   **อนุสัญญาภาษีซ้อนไทย-สหรัฐฯ (US-Thailand DTA):**
            *   [กรมสรรพากร อนุสัญญาภาษีซ้อน](https://www.rd.go.th) หรือ [สรรพากรสหรัฐฯ (IRS.gov)](https://www.irs.gov/businesses/international-businesses/thailand-tax-treaty-documents) (อ้างอิงข้อ 10 'Dividends' ที่ลดอัตราภาษีปันผลหัก ณ ที่จ่ายเหลือ 15% สำหรับผู้มีสัญชาติไทยที่กรอกแบบฟอร์ม W-8BEN)
        """)
