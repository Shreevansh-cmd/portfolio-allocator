import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from io import StringIO

from models.return_predictor import predict_returns
from utils.risk_profiler import get_risk_profile
from optimization.portfolio_optimizer import optimize_portfolio


# ================== Helper Function ==================
def calculate_portfolio_metrics(weights, returns):
    w = []
    r = []

    for asset in weights:
        w.append(weights[asset])
        r.append(returns[asset])

    w = pd.Series(w)
    r = pd.Series(r)

    expected_return = (w * r).sum()
    volatility = (w * (r - r.mean()) ** 2).sum() ** 0.5

    risk_free_rate = 0.04
    sharpe_ratio = (
        (expected_return - risk_free_rate) / volatility
        if volatility != 0 else 0
    )

    return expected_return, volatility, sharpe_ratio


# ================== PAGE CONFIG ==================
st.set_page_config(
    page_title="AI Portfolio Allocator",
    page_icon="AI",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ================== PREMIUM DARK THEME CSS ==================
st.markdown("""
<style>
    /* Global Styles */
    * {
        font-family: 'Inter', 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    
    /* Body and Main Container */
    .stApp {
        background: linear-gradient(135deg, #0a0f1c 0%, #1a1f35 50%, #0a0f1c 100%);
        color: #e2e8f0;
    }
    
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1400px;
        margin: 0 auto;
    }
    
    /* Glassmorphism Cards */
    .glass-card {
        background: rgba(30, 41, 59, 0.7);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border: 1px solid rgba(99, 102, 241, 0.2);
        border-radius: 20px;
        padding: 2rem;
        box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
        margin-bottom: 2rem;
        transition: all 0.3s ease;
    }
    
    .glass-card:hover {
        background: rgba(30, 41, 59, 0.8);
        border-color: rgba(99, 102, 241, 0.4);
        transform: translateY(-4px);
        box-shadow: 0 28px 80px rgba(59, 130, 246, 0.2);
    }
    
    .hero-card {
        background: linear-gradient(180deg, rgba(15, 23, 42, 0.95), rgba(15, 23, 42, 0.8));
        border: 1px solid rgba(99, 102, 241, 0.3);
        border-radius: 32px;
        padding: 3rem;
        box-shadow: 0 32px 100px rgba(15, 23, 42, 0.4);
        margin-bottom: 3rem;
        text-align: center;
    }
    
    .hero-title {
        font-size: 4rem;
        font-weight: 900;
        background: linear-gradient(135deg, #6366f1 0%, #22d3ee 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 1rem;
        letter-spacing: -0.04em;
        line-height: 1.05;
    }
    
    .hero-subtitle {
        color: #cbd5e1;
        font-size: 1.2rem;
        max-width: 800px;
        margin: 0 auto;
        line-height: 1.8;
    }
    
    .hero-badge {
        display: inline-flex;
        align-items: center;
        gap: 0.8rem;
        background: rgba(59, 130, 246, 0.15);
        border: 1px solid rgba(59, 130, 246, 0.3);
        color: #dbeafe;
        padding: 1rem 1.5rem;
        border-radius: 999px;
        font-weight: 700;
        margin-top: 2rem;
        font-size: 1.1rem;
    }
    
    /* Top Summary Bar */
    .summary-bar {
        display: flex;
        justify-content: space-around;
        align-items: center;
        background: rgba(30, 41, 59, 0.9);
        backdrop-filter: blur(20px);
        border: 1px solid rgba(99, 102, 241, 0.2);
        border-radius: 24px;
        padding: 2rem;
        margin-bottom: 3rem;
        box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
    }
    
    .summary-item {
        text-align: center;
        flex: 1;
        padding: 0 1rem;
    }
    
    .summary-icon {
        margin-bottom: 0.5rem;
    }

    .summary-icon svg {
        width: 56px;
        height: 56px;
        margin: 0 auto 0.75rem;
        display: block;
    }
    
    .summary-value {
        font-size: 2.5rem;
        font-weight: 900;
        margin-bottom: 0.25rem;
    }
    
    .summary-label {
        color: #94a3b8;
        font-size: 1rem;
        font-weight: 600;
    }
    
    /* Button Styles */
    .stButton > button {
        background: linear-gradient(135deg, #6366f1 0%, #22d3ee 100%);
        color: white;
        border: none;
        border-radius: 16px;
        padding: 1rem 2rem;
        font-weight: 700;
        font-size: 1.1rem;
        transition: all 0.3s ease;
        box-shadow: 0 8px 30px rgba(99, 102, 241, 0.3);
        width: 100%;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 12px 40px rgba(99, 102, 241, 0.5);
    }
    
    .download-btn {
        background: linear-gradient(135deg, #22c55e 0%, #16a34a 100%);
        margin-top: 1rem;
    }
    
    /* Sidebar Styles */
    .sidebar .sidebar-content {
        background: linear-gradient(180deg, rgba(30, 41, 59, 0.95) 0%, rgba(17, 24, 39, 0.95) 100%);
        border-right: 1px solid rgba(99, 102, 241, 0.2);
    }
    
    /* Input Styles */
    .stRadio > div {
        background: rgba(30, 41, 59, 0.6);
        border-radius: 12px;
        padding: 0.75rem;
        border: 1px solid rgba(99, 102, 241, 0.2);
    }
    
    .stSelectbox > div > div {
        background: rgba(30, 41, 59, 0.8);
        border: 1px solid rgba(99, 102, 241, 0.3);
        border-radius: 12px;
        color: #e2e8f0;
    }
    
    .stNumberInput > div > div > input {
        background: rgba(30, 41, 59, 0.8);
        border: 1px solid rgba(99, 102, 241, 0.3);
        border-radius: 12px;
        color: #e2e8f0;
    }
    
    /* Dataframe Styles */
    .stDataFrame {
        background: rgba(30, 41, 59, 0.8);
        border-radius: 16px;
        border: 1px solid rgba(99, 102, 241, 0.2);
        box-shadow: 0 8px 30px rgba(0, 0, 0, 0.2);
    }
    
    /* Info Box */
    .stAlert {
        background: rgba(34, 197, 94, 0.1);
        border: 1px solid rgba(34, 197, 94, 0.3);
        border-radius: 12px;
        color: #e2e8f0;
    }
    
    /* Subheader Styles */
    h1, h2, h3, h4 {
        color: #f1f5f9;
        font-weight: 700;
        margin-bottom: 1rem;
    }
    
    /* Spinner */
    .stSpinner > div > div {
        border-color: #6366f1;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 2rem;
        background: rgba(30, 41, 59, 0.8);
        border-radius: 16px;
        padding: 0.5rem;
        margin-bottom: 2rem;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: transparent;
        border-radius: 12px;
        color: #cbd5e1;
        font-weight: 600;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #6366f1 0%, #22d3ee 100%);
        color: white;
    }
    
    /* Section Dividers */
    .section-divider {
        border: none;
        height: 2px;
        background: linear-gradient(90deg, transparent, rgba(99, 102, 241, 0.5), transparent);
        margin: 3rem 0;
    }
    
    /* Responsive Grid */
    .responsive-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
        gap: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# ================== HERO SECTION ==================
st.markdown("""
<div class="hero-card">
    <div style="display:flex;align-items:center;gap:2rem;flex-wrap:wrap;justify-content:center;margin-bottom:2rem;">
        <div style="width:120px;height:120px;border-radius:24px;display:flex;align-items:center;justify-content:center;box-shadow:0 24px 60px rgba(0,0,0,0.3);">
            <svg width="96" height="96" viewBox="0 0 96 96" xmlns="http://www.w3.org/2000/svg" style="border-radius:24px;">
                <defs>
                    <linearGradient id="heroGradient" x1="0" y1="0" x2="1" y2="1">
                        <stop offset="0%" stop-color="rgb(99,102,241)"/>
                        <stop offset="100%" stop-color="rgb(34,211,238)"/>
                    </linearGradient>
                </defs>
                <rect x="0" y="0" width="96" height="96" rx="24" fill="url(#heroGradient)"/>
                <path d="M20 68 L38 44 L54 58 L76 30" stroke="white" stroke-width="8" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
                <circle cx="20" cy="68" r="6" fill="white"/>
                <circle cx="38" cy="44" r="6" fill="white"/>
                <circle cx="54" cy="58" r="6" fill="white"/>
                <circle cx="76" cy="30" r="6" fill="white"/>
            </svg>
        </div>
        <div>
            <div class="hero-title">AI Portfolio Allocator</div>
            <div class="hero-subtitle">Intelligent portfolio optimization powered by machine learning. Build diversified, risk-adjusted portfolios tailored to your goals.</div>
        </div>
    </div>
    <div class="hero-badge">
        <span>Advanced allocation engine</span>
    </div>
</div>
""", unsafe_allow_html=True)

# ================== SIDEBAR ==================
with st.sidebar:
    st.markdown("""
    <div style="text-align: center; margin-bottom: 2rem;">
        <div style="display:inline-flex;align-items:center;gap:0.75rem;padding:1rem 1.25rem;background:rgba(59,130,246,0.15);border-radius:999px;border:1px solid rgba(59,130,246,0.3);">
            <strong style="font-size:1.2rem;color:#eef2ff;">Configuration</strong>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("### Risk Profile")
    risk_level = st.radio(
        "Select your risk tolerance:",
        ["Low", "Medium", "High"],
        help="Low: Conservative, stable returns\nMedium: Balanced approach\nHigh: Aggressive growth"
    )

    risk_info = {
        "Low": "**Stable & Low Risk**\n- Preserve capital\n- Comfortable allocation",
        "Medium": "**Balanced Risk & Return**\n- Moderate growth\n- Diversified mix",
        "High": "**High Risk, High Return**\n- Aggressive growth\n- Higher potential volatility"
    }
    
    st.markdown(f"""
    <div class="glass-card" style="padding:1.5rem;margin-bottom:1.5rem;">
        <h4>Risk Profile</h4>
        <p>{risk_info[risk_level].replace(chr(10), '<br>')}</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### Investment Amount")
    investment_amount = st.number_input(
        "Total investment (₹):",
        value=100000,
        min_value=10000,
        step=10000,
        help="Minimum investment: ₹10,000"
    )

    st.markdown("### Market Scenario")
    market_scenario = st.selectbox(
        "Expected market conditions:",
        ["Normal", "Bull", "Bear"],
        help="Normal: Typical market conditions\nBull: Strong market growth\nBear: Market downturn"
    )
    
    scenario_descriptions = {
        "Normal": "Standard market environment with steady performance.",
        "Bull": "Positive momentum and strong growth expectations.",
        "Bear": "Defensive stance during market weakness.",
    }
    
    st.markdown(f"""
    <div class="glass-card" style="padding:1.5rem;margin-bottom:1.5rem;">
        <h4>Market Scenario</h4>
        <p>{scenario_descriptions[market_scenario]}</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    generate = st.button("Generate Portfolio", type="primary", use_container_width=True)
    
    st.markdown("""
    <div class="glass-card" style="background:rgba(59,130,246,0.08);border-color:rgba(59,130,246,0.2);padding:1.5rem;">
        <h4>Why this works</h4>
        <p>Smart allocation uses risk appetite, current market scenario, and historical returns to recommend a portfolio suited for your goals.</p>
    </div>
    """, unsafe_allow_html=True)


# ================== MAIN CONTENT ==================
if generate:
    with st.spinner("Optimizing your portfolio..."):
        risk_profile = get_risk_profile(risk_level)
        predicted_returns = predict_returns()

        scenario_multiplier = {
            "Bull": 1.15,
            "Normal": 1.0,
            "Bear": 0.85
        }

        multiplier = scenario_multiplier[market_scenario]

        adjusted_returns = {
            asset: ret * multiplier
            for asset, ret in predicted_returns.items()
        }

        final_portfolio = optimize_portfolio(adjusted_returns, risk_profile)

        portfolio_return, portfolio_volatility, sharpe_ratio = calculate_portfolio_metrics(
            final_portfolio, adjusted_returns
        )

    # ================== TOP SUMMARY BAR ==================
    st.markdown(f"""
    <div class="summary-bar">
        <div class="summary-item">
            <div class="summary-icon">
                <svg viewBox="0 0 64 64" xmlns="http://www.w3.org/2000/svg">
                    <circle cx="32" cy="32" r="30" fill="rgba(34,197,94,0.15)" />
                    <path d="M18 42 L28 32 L38 40 L46 28" fill="none" stroke="#22c55e" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/>
                    <circle cx="46" cy="28" r="4" fill="#22c55e"/>
                </svg>
            </div>
            <div class="summary-value" style="color: #22c55e;">{portfolio_return * 100:.2f}%</div>
            <div class="summary-label">Expected Return</div>
        </div>
        <div class="summary-item">
            <div class="summary-icon">
                <svg viewBox="0 0 64 64" xmlns="http://www.w3.org/2000/svg">
                    <circle cx="32" cy="32" r="30" fill="rgba(249,115,22,0.15)" />
                    <path d="M20 24 L32 16 L44 24 L44 38 C44 44 32 52 32 52 C32 52 20 44 20 38 Z" fill="#f97316" opacity="0.65"/>
                    <rect x="26" y="28" width="12" height="12" rx="2" fill="white" opacity="0.9"/>
                </svg>
            </div>
            <div class="summary-value" style="color: #f97316;">{portfolio_volatility * 100:.2f}%</div>
            <div class="summary-label">Risk (Volatility)</div>
        </div>
        <div class="summary-item">
            <div class="summary-icon">
                <svg viewBox="0 0 64 64" xmlns="http://www.w3.org/2000/svg">
                    <circle cx="32" cy="32" r="30" fill="rgba(167,139,250,0.15)" />
                    <path d="M18 38 A14 14 0 0 1 46 20" fill="none" stroke="#a78bfa" stroke-width="5" stroke-linecap="round"/>
                    <circle cx="42" cy="22" r="4" fill="#a78bfa"/>
                    <path d="M24 44 L32 34 L40 40" fill="none" stroke="#a78bfa" stroke-width="5" stroke-linecap="round"/>
                </svg>
            </div>
            <div class="summary-value" style="color: #a78bfa;">{sharpe_ratio:.2f}</div>
            <div class="summary-label">Sharpe Ratio</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ================== TABS ==================
    tab1, tab2 = st.tabs(["Dashboard", "Analytics"])

    with tab1:
        # ================== PORTFOLIO BREAKDOWN ==================
        st.markdown("### Portfolio Breakdown")
        
        df = pd.DataFrame({
            "Asset": list(final_portfolio.keys()),
            "Allocation (%)": [v * 100 for v in final_portfolio.values()],
            "Amount (₹)": [v * investment_amount for v in final_portfolio.values()]
        })

        col_left, col_right = st.columns([1.2, 1])

        with col_left:
            st.markdown("""
            <div class="glass-card" style="padding:1.5rem 1.5rem 1rem 1.5rem; margin-bottom:1rem;">
                <h4>Allocation Details</h4>
            </div>
            """, unsafe_allow_html=True)
            st.dataframe(
                df,
                use_container_width=True,
                column_config={
                    "Asset": st.column_config.TextColumn(width=120),
                    "Allocation (%)": st.column_config.NumberColumn(
                        format="%.2f%%",
                        width=120
                    ),
                    "Amount (₹)": st.column_config.NumberColumn(
                        format="₹%.0f",
                        width=120
                    ),
                }
            )
            
            # CSV Download
            csv = df.to_csv(index=False)
            st.download_button(
                label="Download Portfolio CSV",
                data=csv,
                file_name="portfolio_allocation.csv",
                mime="text/csv",
                key="download-csv",
                help="Download your portfolio allocation as CSV"
            )

        with col_right:
            st.markdown("""
            <div class="glass-card" style="padding:1.5rem 1.5rem 1rem 1.5rem; margin-bottom:1rem;">
                <h4>Visual Distribution</h4>
            </div>
            """, unsafe_allow_html=True)

            fig = px.pie(
                df,
                names="Asset",
                values="Allocation (%)",
                hole=0.5,
                color_discrete_sequence=px.colors.sequential.Viridis,
                title=""
            )
            
            fig.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#e2e8f0'),
                showlegend=True,
                margin=dict(l=0, r=0, t=0, b=0)
            )
            
            fig.update_traces(
                textposition='inside',
                textinfo='percent+label',
                hovertemplate='<b>%{label}</b><br>Allocation: %{percent}<br>Amount: ₹%{customdata:.0f}<extra></extra>',
                customdata=df["Amount (₹)"]
            )

            st.plotly_chart(fig, use_container_width=True)

        # ================== EXPECTED RETURNS ==================
        st.markdown("### Expected Returns by Asset")
        
        cols = st.columns(len(adjusted_returns))
        for i, (asset, ret) in enumerate(adjusted_returns.items()):
            with cols[i]:
                st.metric(
                    asset, 
                    f"{ret * 100:.2f}%",
                    help=f"Expected return for {asset} in {market_scenario} market conditions"
                )

        # ================== INSIGHTS ==================
        st.markdown("### Portfolio Insights")
        
        insights = []
        if risk_level == "High":
            insights.append("**High Growth Focus**: Your portfolio emphasizes equity for maximum returns, suitable for long-term investors.")
        elif risk_level == "Low":
            insights.append("**Capital Preservation**: Conservative allocation prioritizes stability and lower risk.")
        else:
            insights.append("**Balanced Approach**: Moderate risk with diversified assets for steady growth.")
        
        if market_scenario == "Bull":
            insights.append("**Bull Market Optimized**: Increased exposure to equities to capitalize on growth opportunities.")
        elif market_scenario == "Bear":
            insights.append("**Defensive Positioning**: Higher allocation to bonds and cash for stability during downturns.")
        
        for insight in insights:
            st.markdown(f"<div class='glass-card' style='margin-bottom:1rem;'><p style='margin:0;font-size:1rem;color:#e2e8f0;'>{insight}</p></div>", unsafe_allow_html=True)

    with tab2:
        # ================== ANALYTICS CHARTS ==================
        st.markdown("### Advanced Analytics")
        
        # Portfolio Growth Projection
        st.markdown("#### Portfolio Growth Projection")
        st.markdown("""
        <div class="glass-card" style="padding:1.5rem 1.5rem 1rem 1.5rem; margin-bottom:1rem;">
            <h4 style="margin:0;">Portfolio Growth Projection</h4>
        </div>
        """, unsafe_allow_html=True)
        
        years = list(range(1, 11))
        growth_values = []
        cumulative = 1
        for year in years:
            cumulative *= (1 + portfolio_return)
            growth_values.append(cumulative * investment_amount)
        
        fig_growth = go.Figure()
        fig_growth.add_trace(go.Scatter(
            x=years,
            y=growth_values,
            mode='lines+markers',
            name='Portfolio Value',
            line=dict(color='#22c55e', width=3),
            marker=dict(size=8, color='#22c55e')
        ))
        
        fig_growth.update_layout(
            title="Projected Portfolio Growth (10 Years)",
            xaxis_title="Years",
            yaxis_title="Portfolio Value (₹)",
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#e2e8f0'),
            xaxis=dict(showgrid=True, gridcolor='rgba(99,102,241,0.1)'),
            yaxis=dict(showgrid=True, gridcolor='rgba(99,102,241,0.1)')
        )
        
        st.plotly_chart(fig_growth, use_container_width=True)

        # Asset Comparison Bar Chart
        st.markdown("#### Asset Performance Comparison")
        st.markdown("""
        <div class="glass-card" style="padding:1.5rem 1.5rem 1rem 1.5rem; margin-bottom:1rem;">
            <h4 style="margin:0;">Asset Performance Comparison</h4>
        </div>
        """, unsafe_allow_html=True)
        
        assets = list(adjusted_returns.keys())
        returns = [adjusted_returns[asset] * 100 for asset in assets]
        allocations = [final_portfolio[asset] * 100 for asset in assets]
        
        fig_comparison = go.Figure()
        fig_comparison.add_trace(go.Bar(
            x=assets,
            y=returns,
            name='Expected Return (%)',
            marker_color='#6366f1'
        ))
        fig_comparison.add_trace(go.Bar(
            x=assets,
            y=allocations,
            name='Allocation (%)',
            marker_color='#22d3ee'
        ))
        
        fig_comparison.update_layout(
            title="Asset Returns vs Allocation",
            xaxis_title="Asset",
            yaxis_title="Percentage",
            barmode='group',
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#e2e8f0'),
            xaxis=dict(showgrid=False),
            yaxis=dict(showgrid=True, gridcolor='rgba(99,102,241,0.1)')
        )
        
        st.plotly_chart(fig_comparison, use_container_width=True)

    # ================== INVESTMENT GUIDELINES ==================
    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
    st.markdown("""
    <div class="glass-card" style="text-align: center;">
        <h4>Investment Guidelines</h4>
        <div class="responsive-grid">
            <div style="background: rgba(34, 197, 94, 0.1); border: 1px solid rgba(34, 197, 94, 0.3); border-radius: 12px; padding: 1.5rem;">
                <div style="font-size: 1rem; margin-bottom: 0.75rem; color: #22c55e; font-weight: 700;">Diversify</div>
                <span style="font-size: 0.9rem; color: #cbd5e1;">Spread investments across different asset classes</span>
            </div>
            <div style="background: rgba(59, 130, 246, 0.1); border: 1px solid rgba(59, 130, 246, 0.3); border-radius: 12px; padding: 1.5rem;">
                <div style="font-size: 1rem; margin-bottom: 0.75rem; color: #3b82f6; font-weight: 700;">Long-term</div>
                <span style="font-size: 0.9rem; color: #cbd5e1;">Invest with a long-term perspective</span>
            </div>
            <div style="background: rgba(249, 115, 22, 0.1); border: 1px solid rgba(249, 115, 22, 0.3); border-radius: 12px; padding: 1.5rem;">
                <div style="font-size: 1rem; margin-bottom: 0.75rem; color: #f97316; font-weight: 700;">Monitor</div>
                <span style="font-size: 0.9rem; color: #cbd5e1;">Regularly review and rebalance your portfolio</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

else:
    # Welcome Section
    st.markdown("""
    <div class="glass-card" style="text-align: center; padding: 4rem 2rem;">
        <div style="display:flex;justify-content:center;margin-bottom:1.5rem;">
            <svg width="120" height="120" viewBox="0 0 120 120" xmlns="http://www.w3.org/2000/svg" style="border-radius:28px;box-shadow:0 24px 60px rgba(0,0,0,0.2);">
                <defs>
                    <linearGradient id="welcomeGradient" x1="0" y1="0" x2="1" y2="1">
                        <stop offset="0%" stop-color="rgb(99,102,241)"/>
                        <stop offset="100%" stop-color="rgb(34,211,238)"/>
                    </linearGradient>
                </defs>
                <rect x="0" y="0" width="120" height="120" rx="28" fill="url(#welcomeGradient)"/>
                <path d="M36 60 L72 36 L72 52 L92 52 L92 68 L72 68 L72 84 Z" fill="white"/>
            </svg>
        </div>
        <h3 style="color: #eef2ff; margin: 1.5rem 0;">Ready to Optimize Your Portfolio?</h3>
        <p style="color: #cbd5e1; font-size: 1.2rem; margin: 0.75rem 0 2rem 0; max-width: 600px; margin-left: auto; margin-right: auto;">
            Configure your investment preferences in the sidebar and click "Generate Portfolio" to get AI-powered allocation recommendations.
        </p>
        <div style="background: rgba(59, 130, 246, 0.15); border: 1px solid rgba(59, 130, 246, 0.3); border-radius: 12px; padding: 1.5rem; display: inline-block;">
            <p style="margin: 0; color: #dbeafe; font-size: 1rem;">
                <strong>Tip:</strong> Choose your risk level, investment amount, and market scenario for personalized results.
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ================== FOOTER ==================
st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
st.markdown("""
<div style="text-align: center; padding: 1.5rem; color: #64748b; font-size: 0.9rem;">
    <p style="margin: 0;">
        <strong>AI Portfolio Allocator</strong> | Powered by Machine Learning & Historical Data Analysis<br>
        <span style="font-size: 0.8rem;">This is for educational purposes only. Past performance does not guarantee future results. Consult a financial advisor.</span>
    </p>
</div>
""", unsafe_allow_html=True)