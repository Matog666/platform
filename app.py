import streamlit as st
import pandas as pd
import plotly.graph_objects as go
# from chatoil import run_oil_chatbot

# .\venv\Scripts\Activate

# --- App Settings ---
st.set_page_config(layout="wide", page_title="NextBarrel Terminal")

# Initialize session state for active tab
if 'active_tab' not in st.session_state:
    st.session_state.active_tab = "North Sea"

# Custom CSS for Bloomberg-style dark theme
st.markdown("""
<style>
    .stApp {
        background-color: #0a0a0a;
    }
    .stSelectbox label, .stDateInput label {
        color: #faa537 !important;
        font-weight: 400;
    }
    h1, h2, h3 {
        color: #faa537 !important;
        font-family: 'Courier New', monospace;
    }
    /* Hide the default tab selector */
    .stTabs [data-baseweb="tab-list"] {
        display: none !important;
    }
    /* Remove Plotly mode bar */
    .modebar{
        display: none !important;
    }
    /* Reduce top padding */
    .block-container {
        padding-top: 2rem !important;
    }
    /* Style sidebar buttons for tab navigation */
    .stButton > button {
        width: 100%;
    }
</style>
""", unsafe_allow_html=True)

#--- Load CSV data ---
try:
    df = pd.read_csv("Historical_prices.csv", index_col=0, parse_dates=True)
except FileNotFoundError:
    st.error("❌ Historical_prices.csv not found. Please upload the file.")
    st.stop()

# Get available products
available_stocks = df.select_dtypes(include="number").columns.tolist()

if not available_stocks:
    st.error("No numeric columns found in the CSV file.")
    st.stop()

# Tab Navigation in Sidebar
st.sidebar.image("logo.png", width=200)
# st.sidebar.markdown("---")

tab_names = [ "North Sea", "Americas", "Middle East", "WAF", "Refined Products", "Freight", "Charts-News"]

# Navigation buttons in 2-column layout
col_n1, col_n2 = st.sidebar.columns(2)

for idx, tab_name in enumerate(tab_names):
    target_col = col_n1 if idx % 2 == 0 else col_n2
    with target_col:
        if st.button(tab_name, key=f"tab_{tab_name}", use_container_width=True):
            st.session_state.active_tab = tab_name
            st.rerun()

st.sidebar.markdown("---")

# Sidebar: Timeframe buttons
col_t1, col_t2, col_t3 = st.sidebar.columns(3)
col_t4, col_t5 = st.sidebar.columns(2)

timeframe = None

with col_t1:
    if st.button("1W", use_container_width=True):
        timeframe = "1W"
with col_t2:
    if st.button("1M", use_container_width=True):
        timeframe = "1M"
with col_t3:
    if st.button("3M", use_container_width=True):
        timeframe = "3M"
with col_t4:
    if st.button("YTD", use_container_width=True):
        timeframe = "YTD"
with col_t5:
    if st.button("ALL", use_container_width=True):
        timeframe = "ALL"



# Apply timeframe filter
max_date = df.index.max()
if timeframe:
    if timeframe == "1W":
        start_date = (max_date - pd.Timedelta(weeks=1)).date()
    elif timeframe == "1M":
        start_date = (max_date - pd.Timedelta(days=30)).date()
    elif timeframe == "3M":
        start_date = (max_date - pd.Timedelta(days=90)).date()
    elif timeframe == "YTD":
        start_date = pd.Timestamp('2025-01-01').date()
    elif timeframe == "ALL":
        start_date = df.index.min().date()
    end_date = max_date.date()
else:
    # Default to 3 months if no timeframe selected
    start_date = (max_date - pd.Timedelta(days=90)).date()
    end_date = max_date.date()

# Filter data
df_filtered = df.loc[end_date:start_date]

if df_filtered.empty:
    st.warning("No data available for selected date range.")
    st.stop()


# --- Tabs ---
# --- Render active tab based on session state ---

# --- Tab 1: Charts + News ---
if st.session_state.active_tab == "Charts-News":
    # Product selector for Charts-News tab
    selected_stock = st.selectbox("Select Product", available_stocks, key="charts_product")
    
    # Calculate key metrics
    latest_price = df_filtered[selected_stock].iloc[0]
    prev_price = df_filtered[selected_stock].iloc[-1] if len(df_filtered) > 1 else latest_price
    price_change = latest_price - prev_price
    pct_change = (price_change / prev_price) * 100 if prev_price != 0 else 0
    
    # Display key metrics
    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    with col_m1:
        st.metric(f"{selected_stock} - Current Price", f"${latest_price:.2f}", f"{price_change:+.2f}")
    with col_m2:
        st.metric("% Change", f"{pct_change:+.2f}%")
    with col_m3:
        st.metric("High", f"${df_filtered[selected_stock].max():.2f}")
    with col_m4:
        st.metric("Low", f"${df_filtered[selected_stock].min():.2f}")
    
    col1, col2 = st.columns([2, 1])

    # Column 1: Bloomberg-style Chart
    with col1:
        st.subheader(f"{selected_stock} - PRICE CHART")
        
        # Create the figure
        fig = go.Figure()
        
        # Add area trace
        fig.add_trace(go.Scatter(
            x=df_filtered.index,
            y=df_filtered[selected_stock],
            mode='lines',
            name=selected_stock,
            line=dict(color='#faa537', width=2),
            fill='tozeroy',
            fillcolor='rgba(250, 165, 55, 0.2)',
            hovertemplate='<b>Date</b>: %{x|%Y-%m-%d}<br>' +
                          '<b>Price</b>: $%{y:.2f}<br>' +
                          '<extra></extra>'
        ))
        
        # Bloomberg Terminal styling
        fig.update_layout(
            plot_bgcolor='#0a0a0a',
            paper_bgcolor='#0a0a0a',
            font=dict(
                family='Courier New, monospace',
                size=12,
                color='#faa537'
            ),
            xaxis=dict(
                gridcolor='#1a1a1a',
                showgrid=True,
                zeroline=False,
                showline=True,
                linewidth=1,
                linecolor='#333333',
                mirror=True
            ),
            yaxis=dict(
                gridcolor='#1a1a1a',
                showgrid=True,
                zeroline=False,
                showline=True,
                linewidth=1,
                linecolor='#333333',
                mirror=True,
                tickprefix='$'
            ),
            hovermode='x unified',
            showlegend=False,
            height=500,
            margin=dict(l=60, r=30, t=30, b=50)
        )
        
        # Update axes for cleaner look
        fig.update_xaxes(
            showspikes=True,
            spikecolor='#faa537',
            spikesnap='cursor',
            spikemode='across',
            spikethickness=1
        )
        
        fig.update_yaxes(
            showspikes=True,
            spikecolor='#faa537',
            spikesnap='cursor',
            spikemode='across',
            spikethickness=1
        )
        
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
       
    # Column 2: News Feed
    with col2:
        st.subheader("LATEST OIL NEWS")
        try:
            with open("daily_news_feed.txt", "r", encoding="utf-8") as f:
                lines = [line.strip() for line in f.readlines() if line.strip()]

            news_html = """
            <div style="
                height: 500px;
                overflow-y: auto;
                border: 1px solid #333333;
                padding: 15px;
                background-color: #0f0f0f;
                color: #faa537;
                font-family: 'Courier New', monospace;
                font-size: 13px;
            ">
            <ul style="list-style-type: none; padding-left: 0;">
            """

            for line in lines:
                news_html += f"<li style='margin-bottom: 12px; border-bottom: 1px solid #1a1a1a; padding-bottom: 8px;'>▸ {line}</li>"

            news_html += "</ul></div>"
            st.markdown(news_html, unsafe_allow_html=True)

        except FileNotFoundError:
            st.warning("🟡 No news file found.")

# --- Tab 2: North Sea ---
if st.session_state.active_tab == "North Sea":
    st.subheader("NORTH SEA COMPLEX")
    
    # Row 1
    col1, col2 = st.columns(2)
    
    # Chart 1: Brent DFL
    with col1:
        st.markdown("**DATED TO FRONTLINE (DFL)**")
        fig_dfl = go.Figure()
        
        fig_dfl.add_trace(go.Scatter(
            x=df_filtered.index,
            y=df_filtered[' Dated to Frontline (DFL)'],
            mode='lines',
            line=dict(color='#faa537', width=2),
            fill='tozeroy',
            fillcolor='rgba(250, 165, 55, 0.2)',
            hovertemplate='<b>Date</b>: %{x|%Y-%m-%d}<br>' +
                          '<b>DFL</b>: $%{y:.2f}<br>' +
                          '<extra></extra>'
        ))
        
        fig_dfl.update_layout(
            plot_bgcolor='#0a0a0a',
            paper_bgcolor='#0a0a0a',
            font=dict(family='Courier New, monospace', size=10, color='#faa537'),
            xaxis=dict(gridcolor='#1a1a1a', showgrid=True, zeroline=False, showline=True, linewidth=1, linecolor='#333333'),
            yaxis=dict(gridcolor='#1a1a1a', showgrid=True, zeroline=False, showline=True, linewidth=1, linecolor='#333333', tickprefix="$"
),
            hovermode='x unified',
            showlegend=False,
            height=300,
            margin=dict(l=50, r=20, t=20, b=40)
        )
        
        st.plotly_chart(fig_dfl, use_container_width=True, config={'displayModeBar': False})
    
    # Chart 2: Brent/WTI Spread
    with col2:
        st.markdown("**BRENT/WTI SPREAD**")
        fig_brentwti = go.Figure()
        
        fig_brentwti.add_trace(go.Scatter(
            x=df_filtered.index,
            y=df_filtered['Brent/Ti'],
            mode='lines',
            line=dict(color='#faa537', width=2),
            fill='tozeroy',
            fillcolor='rgba(250, 165, 55, 0.2)',
            hovertemplate='<b>Date</b>: %{x|%Y-%m-%d}<br>' +
                          '<b>Brent/WTI</b>: $%{y:.2f}<br>' +
                          '<extra></extra>'
        ))
        
        fig_brentwti.update_layout(
            plot_bgcolor='#0a0a0a',
            paper_bgcolor='#0a0a0a',
            font=dict(family='Courier New, monospace', size=10, color='#faa537'),
            xaxis=dict(gridcolor='#1a1a1a', showgrid=True, zeroline=False, showline=True, linewidth=1, linecolor='#333333'),
            yaxis=dict(gridcolor='#1a1a1a', showgrid=True, zeroline=False, showline=True, linewidth=1, linecolor='#333333', tickprefix="$"
),
            hovermode='x unified',
            showlegend=False,
            height=300,
            margin=dict(l=50, r=20, t=20, b=40)
        )
        
        st.plotly_chart(fig_brentwti, use_container_width=True, config={'displayModeBar': False})
    
    # Row 2
    col3, col4 = st.columns(2)
    
    # Chart 3: Brent M1/M2 Spread
    with col3:
        st.markdown("**BRENT M1/M2 SPREAD**")
        fig_m1m2 = go.Figure()
        
        fig_m1m2.add_trace(go.Scatter(
            x=df_filtered.index,
            y=df_filtered['Brent M1/M2 spread'],
            mode='lines',
            line=dict(color='#faa537', width=2),
            fill='tozeroy',
            fillcolor='rgba(250, 165, 55, 0.2)',
            hovertemplate='<b>Date</b>: %{x|%Y-%m-%d}<br>' +
                          '<b>M1/M2</b>: $%{y:.2f}<br>' +
                          '<extra></extra>'
        ))
        
        fig_m1m2.update_layout(
            plot_bgcolor='#0a0a0a',
            paper_bgcolor='#0a0a0a',
            font=dict(family='Courier New, monospace', size=10, color='#faa537'),
            xaxis=dict(gridcolor='#1a1a1a', showgrid=True, zeroline=False, showline=True, linewidth=1, linecolor='#333333'),
            yaxis=dict(gridcolor='#1a1a1a', showgrid=True, zeroline=False, showline=True, linewidth=1, linecolor='#333333', tickprefix="$"
),
            hovermode='x unified',
            showlegend=False,
            height=300,
            margin=dict(l=50, r=20, t=20, b=40)
        )
        
        st.plotly_chart(fig_m1m2, use_container_width=True, config={'displayModeBar': False})
    
    # Chart 4: Weekly CFDs Curve
    with col4:
        st.markdown("**WEEKLY CFDs CURVE**")
        fig_cfd = go.Figure()
        
        # Get the latest (most recent) values for each CFD week
        latest_data = df_filtered.iloc[0]
        
        cfd_weeks = [
            'North Sea Dated CFD week 1',
            'North Sea Dated CFD week 2',
            'North Sea Dated CFD week 3',
            'North Sea Dated CFD week 4',
            'North Sea Dated CFD week 5'
        ]
        
        cfd_values = [latest_data[week] for week in cfd_weeks if pd.notna(latest_data[week])]
        cfd_labels = [f'W{i+1}' for i in range(len(cfd_values))]
        
        fig_cfd.add_trace(go.Scatter(
            x=cfd_labels,
            y=cfd_values,
            mode='lines+markers',
            line=dict(color='#faa537', width=2),
            marker=dict(size=8, color='#faa537'),
            hovertemplate='<b>%{x}</b><br>' +
                          '<b>Price</b>: $%{y:.2f}<br>' +
                          '<extra></extra>'
        ))
        
        fig_cfd.update_layout(
            plot_bgcolor='#0a0a0a',
            paper_bgcolor='#0a0a0a',
            font=dict(family='Courier New, monospace', size=10, color='#faa537'),
            xaxis=dict(
                gridcolor='#1a1a1a', 
                showgrid=True, 
                zeroline=False, 
                showline=True, 
                linewidth=1, 
                linecolor='#333333',
                title='Week'
            ),
            yaxis=dict(
                gridcolor='#1a1a1a', 
                showgrid=True, 
                zeroline=False, 
                showline=True, 
                linewidth=1, 
                linecolor='#333333', 
                tickprefix="$"
,
                title='Price'
            ),
            hovermode='closest',
            showlegend=False,
            height=300,
            margin=dict(l=50, r=20, t=20, b=40)
        )
        
        st.plotly_chart(fig_cfd, use_container_width=True, config={'displayModeBar': False})

# --- Tab 3: US ---
if st.session_state.active_tab == "Americas":
    st.subheader("US OIL")
    
    # Row 1
    col1, col2 = st.columns(2)
    
    # Chart 1: WTI M1/M2
    with col1:
        st.markdown("**WTI M1/M2 SPREAD**")
        fig_wti_m1m2 = go.Figure()
        
        fig_wti_m1m2.add_trace(go.Scatter(
            x=df_filtered.index,
            y=df_filtered['WTI M1/M2'],
            mode='lines',
            line=dict(color='#faa537', width=2),
            fill='tozeroy',
            fillcolor='rgba(250, 165, 55, 0.2)',
            hovertemplate='<b>Date</b>: %{x|%Y-%m-%d}<br>' +
                          '<b>WTI M1/M2</b>: $%{y:.2f}<br>' +
                          '<extra></extra>'
        ))
        
        fig_wti_m1m2.update_layout(
            plot_bgcolor='#0a0a0a',
            paper_bgcolor='#0a0a0a',
            font=dict(family='Courier New, monospace', size=10, color='#faa537'),
            xaxis=dict(gridcolor='#1a1a1a', showgrid=True, zeroline=False, showline=True, linewidth=1, linecolor='#333333'),
            yaxis=dict(gridcolor='#1a1a1a', showgrid=True, zeroline=False, showline=True, linewidth=1, linecolor='#333333', tickprefix="$"),
            hovermode='x unified',
            showlegend=False,
            height=300,
            margin=dict(l=50, r=20, t=20, b=40)
        )
        
        st.plotly_chart(fig_wti_m1m2, use_container_width=True, config={'displayModeBar': False})
    
    # Chart 2: Houston MEH vs WTI
    with col2:
        st.markdown("**HOUSTON MEH vs WTI**")
        fig_houston = go.Figure()
        
        fig_houston.add_trace(go.Scatter(
            x=df_filtered.index,
            y=df_filtered['Houston MEH vs WTI'],
            mode='lines',
            line=dict(color='#faa537', width=2),
            fill='tozeroy',
            fillcolor='rgba(250, 165, 55, 0.2)',
            hovertemplate='<b>Date</b>: %{x|%Y-%m-%d}<br>' +
                          '<b>Houston MEH</b>: $%{y:.2f}<br>' +
                          '<extra></extra>'
        ))
        
        fig_houston.update_layout(
            plot_bgcolor='#0a0a0a',
            paper_bgcolor='#0a0a0a',
            font=dict(family='Courier New, monospace', size=10, color='#faa537'),
            xaxis=dict(gridcolor='#1a1a1a', showgrid=True, zeroline=False, showline=True, linewidth=1, linecolor='#333333'),
            yaxis=dict(gridcolor='#1a1a1a', showgrid=True, zeroline=False, showline=True, linewidth=1, linecolor='#333333', tickprefix="$"),
            hovermode='x unified',
            showlegend=False,
            height=300,
            margin=dict(l=50, r=20, t=20, b=40)
        )
        
        st.plotly_chart(fig_houston, use_container_width=True, config={'displayModeBar': False})
    
    # Row 2
    col3, col4 = st.columns(2)
    
    # Chart 3: WCS Hardisty vs WTI and Mars vs WTI (multiline)
    with col3:
        st.markdown("**SOURS vs WTI**")
        fig_crudes = go.Figure()
        
        # WCS Hardisty vs WTI
        fig_crudes.add_trace(go.Scatter(
            x=df_filtered.index,
            y=df_filtered['WCS Hardisty vs WTI'],
            mode='lines',
            name='WCS Hardisty',
            line=dict(color='#faa537', width=2),
            hovertemplate='<b>Date</b>: %{x|%Y-%m-%d}<br>' +
                          '<b>WCS Hardisty</b>: $%{y:.2f}<br>' +
                          '<extra></extra>'
        ))
        
        # Mars vs WTI
        fig_crudes.add_trace(go.Scatter(
            x=df_filtered.index,
            y=df_filtered['Mars vs WTI 1st Line'],
            mode='lines',
            name='Mars',
            line=dict(color='#00d9ff', width=2),
            hovertemplate='<b>Date</b>: %{x|%Y-%m-%d}<br>' +
                          '<b>Mars</b>: $%{y:.2f}<br>' +
                          '<extra></extra>'
        ))
        
        fig_crudes.update_layout(
            plot_bgcolor='#0a0a0a',
            paper_bgcolor='#0a0a0a',
            font=dict(family='Courier New, monospace', size=10, color='#faa537'),
            xaxis=dict(gridcolor='#1a1a1a', showgrid=True, zeroline=False, showline=True, linewidth=1, linecolor='#333333'),
            yaxis=dict(gridcolor='#1a1a1a', showgrid=True, zeroline=False, showline=True, linewidth=1, linecolor='#333333', tickprefix="$"),
            hovermode='x unified',
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1,
                bgcolor='rgba(0,0,0,0)',
                font=dict(color='#faa537')
            ),
            height=300,
            margin=dict(l=50, r=20, t=40, b=40)
        )
        
        st.plotly_chart(fig_crudes, use_container_width=True, config={'displayModeBar': False})
    
    # Chart 4: Refinery Utilization (multiline with dotted US average)
    with col4:
        st.markdown("**REFINERY UTILIZATION**")
        fig_refinery = go.Figure()
        
        # PADD 1
        fig_refinery.add_trace(go.Scatter(
            x=df_filtered.index,
            y=df_filtered['Refinery runs East Coast (PADD 1)'],
            mode='lines',
            name='PADD 1',
            line=dict(color='#faa537', width=2),
            hovertemplate='<b>Date</b>: %{x|%Y-%m-%d}<br>' +
                          '<b>PADD 1</b>: %{y:.1f}%<br>' +
                          '<extra></extra>'
        ))
        
        # PADD 3
        fig_refinery.add_trace(go.Scatter(
            x=df_filtered.index,
            y=df_filtered['Refinery runs Gulf Coast (PADD 3)'],
            mode='lines',
            name='PADD 3',
            line=dict(color='#00d9ff', width=2),
            hovertemplate='<b>Date</b>: %{x|%Y-%m-%d}<br>' +
                          '<b>PADD 3</b>: %{y:.1f}%<br>' +
                          '<extra></extra>'
        ))
        
        # US Average (dotted line)
        fig_refinery.add_trace(go.Scatter(
            x=df_filtered.index,
            y=df_filtered['U.S. Average Utilization'],
            mode='lines',
            name='US Average',
            line=dict(color='#ff6b6b', width=2, dash='dot'),
            hovertemplate='<b>Date</b>: %{x|%Y-%m-%d}<br>' +
                          '<b>US Avg</b>: %{y:.1f}%<br>' +
                          '<extra></extra>'
        ))
        
        fig_refinery.update_layout(
            plot_bgcolor='#0a0a0a',
            paper_bgcolor='#0a0a0a',
            font=dict(family='Courier New, monospace', size=10, color='#faa537'),
            xaxis=dict(gridcolor='#1a1a1a', showgrid=True, zeroline=False, showline=True, linewidth=1, linecolor='#333333'),
            yaxis=dict(
                gridcolor='#1a1a1a', 
                showgrid=True, 
                zeroline=False, 
                showline=True, 
                linewidth=1, 
                linecolor='#333333',
                ticksuffix='%'
            ),
            hovermode='x unified',
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1,
                bgcolor='rgba(0,0,0,0)',
                font=dict(color='#faa537')
            ),
            height=300,
            margin=dict(l=50, r=20, t=40, b=40)
        )
        
        st.plotly_chart(fig_refinery, use_container_width=True, config={'displayModeBar': False})

# --- Tab 4: Middle East ---
if st.session_state.active_tab == "Middle East":
    st.subheader("MIDDLE EAST OIL MARKETS")
    
    # Row 1
    col1, col2 = st.columns(2)
    
    # Chart 1: Dubai-Brent EFS
    with col1:
        st.markdown("**DUBAI-BRENT EFS**")
        fig_efs = go.Figure()
        
        fig_efs.add_trace(go.Scatter(
            x=df_filtered.index,
            y=df_filtered['Dubai-Brent EFS'],
            mode='lines',
            line=dict(color='#faa537', width=2),
            fill='tozeroy',
            fillcolor='rgba(250, 165, 55, 0.2)',
            hovertemplate='<b>Date</b>: %{x|%Y-%m-%d}<br>' +
                          '<b>EFS</b>: $%{y:.2f}<br>' +
                          '<extra></extra>'
        ))
        
        fig_efs.update_layout(
            plot_bgcolor='#0a0a0a',
            paper_bgcolor='#0a0a0a',
            font=dict(family='Courier New, monospace', size=10, color='#faa537'),
            xaxis=dict(gridcolor='#1a1a1a', showgrid=True, zeroline=False, showline=True, linewidth=1, linecolor='#333333'),
            yaxis=dict(gridcolor='#1a1a1a', showgrid=True, zeroline=False, showline=True, linewidth=1, linecolor='#333333', tickprefix="$"),
            hovermode='x unified',
            showlegend=False,
            height=300,
            margin=dict(l=50, r=20, t=20, b=40)
        )
        
        st.plotly_chart(fig_efs, use_container_width=True, config={'displayModeBar': False})
    
    # Chart 2: DubaiM1/M2
    with col2:
        st.markdown("**DUBAI M1/M2 SPREAD**")
        fig_dubai_m1m2 = go.Figure()
        
        fig_dubai_m1m2.add_trace(go.Scatter(
            x=df_filtered.index,
            y=df_filtered['DubaiM1/M2'],
            mode='lines',
            line=dict(color='#faa537', width=2),
            fill='tozeroy',
            fillcolor='rgba(250, 165, 55, 0.2)',
            hovertemplate='<b>Date</b>: %{x|%Y-%m-%d}<br>' +
                          '<b>Dubai M1/M2</b>: $%{y:.2f}<br>' +
                          '<extra></extra>'
        ))
        
        fig_dubai_m1m2.update_layout(
            plot_bgcolor='#0a0a0a',
            paper_bgcolor='#0a0a0a',
            font=dict(family='Courier New, monospace', size=10, color='#faa537'),
            xaxis=dict(gridcolor='#1a1a1a', showgrid=True, zeroline=False, showline=True, linewidth=1, linecolor='#333333'),
            yaxis=dict(gridcolor='#1a1a1a', showgrid=True, zeroline=False, showline=True, linewidth=1, linecolor='#333333', tickprefix="$"),
            hovermode='x unified',
            showlegend=False,
            height=300,
            margin=dict(l=50, r=20, t=20, b=40)
        )
        
        st.plotly_chart(fig_dubai_m1m2, use_container_width=True, config={'displayModeBar': False})
    
    # Row 2
    col3, col4 = st.columns(2)
    
    # Chart 3: Dubai Physical Premium
    with col3:
        st.markdown("**DUBAI PHYSICAL PREMIUM**")
        fig_premium = go.Figure()
        
        fig_premium.add_trace(go.Scatter(
            x=df_filtered.index,
            y=df_filtered['Dubai Physical Premium'],
            mode='lines',
            line=dict(color='#faa537', width=2),
            fill='tozeroy',
            fillcolor='rgba(250, 165, 55, 0.2)',
            hovertemplate='<b>Date</b>: %{x|%Y-%m-%d}<br>' +
                          '<b>Premium</b>: $%{y:.2f}<br>' +
                          '<extra></extra>'
        ))
        
        fig_premium.update_layout(
            plot_bgcolor='#0a0a0a',
            paper_bgcolor='#0a0a0a',
            font=dict(family='Courier New, monospace', size=10, color='#faa537'),
            xaxis=dict(gridcolor='#1a1a1a', showgrid=True, zeroline=False, showline=True, linewidth=1, linecolor='#333333'),
            yaxis=dict(gridcolor='#1a1a1a', showgrid=True, zeroline=False, showline=True, linewidth=1, linecolor='#333333', tickprefix="$"),
            hovermode='x unified',
            showlegend=False,
            height=300,
            margin=dict(l=50, r=20, t=40, b=40)
        )
        
        st.plotly_chart(fig_premium, use_container_width=True, config={'displayModeBar': False})
    
    # Chart 4: Murban diff to Dubai swaps
    with col4:
        st.markdown("**MURBAN DIFF TO DUBAI SWAPS**")
        fig_murban = go.Figure()
        
        fig_murban.add_trace(go.Scatter(
            x=df_filtered.index,
            y=df_filtered['Murban diff to Dubai swaps'],
            mode='lines',
            line=dict(color='#faa537', width=2),
            fill='tozeroy',
            fillcolor='rgba(250, 165, 55, 0.2)',
            hovertemplate='<b>Date</b>: %{x|%Y-%m-%d}<br>' +
                          '<b>Murban Diff</b>: $%{y:.2f}<br>' +
                          '<extra></extra>'
        ))
        
        fig_murban.update_layout(
            plot_bgcolor='#0a0a0a',
            paper_bgcolor='#0a0a0a',
            font=dict(family='Courier New, monospace', size=10, color='#faa537'),
            xaxis=dict(gridcolor='#1a1a1a', showgrid=True, zeroline=False, showline=True, linewidth=1, linecolor='#333333'),
            yaxis=dict(gridcolor='#1a1a1a', showgrid=True, zeroline=False, showline=True, linewidth=1, linecolor='#333333', tickprefix="$"),
            hovermode='x unified',
            showlegend=False,
            height=300,
            margin=dict(l=50, r=20, t=40, b=40)
        )
        
        st.plotly_chart(fig_murban, use_container_width=True, config={'displayModeBar': False})

# --- Tab 5: WAF (West Africa) ---
if st.session_state.active_tab == "WAF":
    st.subheader("WEST AFRICA OIL")
    
    # Row 1
    col1, col2 = st.columns(2)
    
    # Chart 1: Bonny vs Dated Brent
    with col1:
        st.markdown("**BONNY LIGHT vs DATED BRENT**")
        fig_bonny = go.Figure()
        
        # Calculate Bonny vs Dated Brent differential
        bonny_diff = df_filtered['Bonny Light FOB'] - df_filtered['Dated Brent']
        
        fig_bonny.add_trace(go.Scatter(
            x=df_filtered.index,
            y=bonny_diff,
            mode='lines',
            line=dict(color='#faa537', width=2),
            fill='tozeroy',
            fillcolor='rgba(250, 165, 55, 0.2)',
            hovertemplate='<b>Date</b>: %{x|%Y-%m-%d}<br>' +
                          '<b>Bonny Diff</b>: $%{y:.2f}<br>' +
                          '<extra></extra>'
        ))
        
        fig_bonny.update_layout(
            plot_bgcolor='#0a0a0a',
            paper_bgcolor='#0a0a0a',
            font=dict(family='Courier New, monospace', size=10, color='#faa537'),
            xaxis=dict(gridcolor='#1a1a1a', showgrid=True, zeroline=False, showline=True, linewidth=1, linecolor='#333333'),
            yaxis=dict(gridcolor='#1a1a1a', showgrid=True, zeroline=False, showline=True, linewidth=1, linecolor='#333333', tickprefix="$"),
            hovermode='x unified',
            showlegend=False,
            height=300,
            margin=dict(l=50, r=20, t=20, b=40)
        )
        
        st.plotly_chart(fig_bonny, use_container_width=True, config={'displayModeBar': False})
    
    # Chart 2: Djeno vs Dated Brent
    with col2:
        st.markdown("**DJENGO vs DATED BRENT**")
        fig_djeno = go.Figure()
        
        # Calculate Djeno vs Dated Brent differential
        djeno_diff = df_filtered['Djeno FOB'] - df_filtered['Dated Brent']
        
        fig_djeno.add_trace(go.Scatter(
            x=df_filtered.index,
            y=djeno_diff,
            mode='lines',
            line=dict(color='#faa537', width=2),
            fill='tozeroy',
            fillcolor='rgba(250, 165, 55, 0.2)',
            hovertemplate='<b>Date</b>: %{x|%Y-%m-%d}<br>' +
                          '<b>Djeno Diff</b>: $%{y:.2f}<br>' +
                          '<extra></extra>'
        ))
        
        fig_djeno.update_layout(
            plot_bgcolor='#0a0a0a',
            paper_bgcolor='#0a0a0a',
            font=dict(family='Courier New, monospace', size=10, color='#faa537'),
            xaxis=dict(gridcolor='#1a1a1a', showgrid=True, zeroline=False, showline=True, linewidth=1, linecolor='#333333'),
            yaxis=dict(gridcolor='#1a1a1a', showgrid=True, zeroline=False, showline=True, linewidth=1, linecolor='#333333', tickprefix="$"),
            hovermode='x unified',
            showlegend=False,
            height=300,
            margin=dict(l=50, r=20, t=20, b=40)
        )
        
        st.plotly_chart(fig_djeno, use_container_width=True, config={'displayModeBar': False})
    
    # Row 2
    col3, col4 = st.columns(2)
    
    # Chart 3: Tanker dirty west Africa to China ($/bbl)
    with col3:
        st.markdown("**FREIGHT WAF-CHINA (VLCC)**")
        fig_freight_china = go.Figure()
        
        # Convert from $/mt to $/bbl
        freight_china_bbl = df_filtered['Tanker dirty west Africa to China 260kt $/mt '] / 7.45
        
        fig_freight_china.add_trace(go.Scatter(
            x=df_filtered.index,
            y=freight_china_bbl,
            mode='lines',
            line=dict(color='#faa537', width=2),
            fill='tozeroy',
            fillcolor='rgba(250, 165, 55, 0.2)',
            hovertemplate='<b>Date</b>: %{x|%Y-%m-%d}<br>' +
                          '<b>Freight</b>: $%{y:.2f}/bbl<br>' +
                          '<extra></extra>'
        ))
        
        fig_freight_china.update_layout(
            plot_bgcolor='#0a0a0a',
            paper_bgcolor='#0a0a0a',
            font=dict(family='Courier New, monospace', size=10, color='#faa537'),
            xaxis=dict(gridcolor='#1a1a1a', showgrid=True, zeroline=False, showline=True, linewidth=1, linecolor='#333333'),
            yaxis=dict(gridcolor='#1a1a1a', showgrid=True, zeroline=False, showline=True, linewidth=1, linecolor='#333333', tickprefix="$", ticksuffix="/bbl"),
            hovermode='x unified',
            showlegend=False,
            height=300,
            margin=dict(l=50, r=20, t=40, b=40)
        )
        
        st.plotly_chart(fig_freight_china, use_container_width=True, config={'displayModeBar': False})
    
    # Chart 4: Tanker dirty west Africa to UKCM ($/bbl)
    with col4:
        st.markdown("**FREIGHT WAF-UKC (SUEZ)**")
        fig_freight_ukcm = go.Figure()
        
        # Convert from $/mt to $/bbl
        freight_ukcm_bbl = df_filtered['Tanker dirty west Africa to UKCM 130kt $/mt '] / 7.45
        
        fig_freight_ukcm.add_trace(go.Scatter(
            x=df_filtered.index,
            y=freight_ukcm_bbl,
            mode='lines',
            line=dict(color='#faa537', width=2),
            fill='tozeroy',
            fillcolor='rgba(250, 165, 55, 0.2)',
            hovertemplate='<b>Date</b>: %{x|%Y-%m-%d}<br>' +
                          '<b>Freight</b>: $%{y:.2f}/bbl<br>' +
                          '<extra></extra>'
        ))
        
        fig_freight_ukcm.update_layout(
            plot_bgcolor='#0a0a0a',
            paper_bgcolor='#0a0a0a',
            font=dict(family='Courier New, monospace', size=10, color='#faa537'),
            xaxis=dict(gridcolor='#1a1a1a', showgrid=True, zeroline=False, showline=True, linewidth=1, linecolor='#333333'),
            yaxis=dict(gridcolor='#1a1a1a', showgrid=True, zeroline=False, showline=True, linewidth=1, linecolor='#333333', tickprefix="$", ticksuffix="/bbl"),
            hovermode='x unified',
            showlegend=False,
            height=300,
            margin=dict(l=50, r=20, t=40, b=40)
        )
        
        st.plotly_chart(fig_freight_ukcm, use_container_width=True, config={'displayModeBar': False})

# --- Tab 6: Refined Products ---
if st.session_state.active_tab == "Refined Products":
    st.subheader("REFINED PRODUCTS CRACKS")
    
    # Row 1
    col1, col2 = st.columns(2)
    
    # Chart 1: Distillates Cracks
    with col1:
        st.markdown("**DISTILLATES CRACKS**")
        fig_distillates = go.Figure()
        
        # Calculate cracks
        nwe_gasoil = df_filtered['Gasoil Ice NWE M1 $/bbl'] - df_filtered['Ice Brent M1']
        sing_10ppm = df_filtered['Gasoil swap Singapore M1'] - df_filtered['Dubai M1']
        ulsd = df_filtered['Diesel ULSD 62 fob USGC waterborne $/bbl'] - df_filtered['Nymex WTI futures M1']
        
        # NWE Gasoil
        fig_distillates.add_trace(go.Scatter(
            x=df_filtered.index,
            y=nwe_gasoil,
            mode='lines',
            name='NWE Gasoil',
            line=dict(color='#faa537', width=2),
            hovertemplate='<b>Date</b>: %{x|%Y-%m-%d}<br>' +
                          '<b>NWE Gasoil</b>: $%{y:.2f}<br>' +
                          '<extra></extra>'
        ))
        
        # Sing 10ppm
        fig_distillates.add_trace(go.Scatter(
            x=df_filtered.index,
            y=sing_10ppm,
            mode='lines',
            name='Sing 10ppm',
            line=dict(color='#00d9ff', width=2),
            hovertemplate='<b>Date</b>: %{x|%Y-%m-%d}<br>' +
                          '<b>Sing 10ppm</b>: $%{y:.2f}<br>' +
                          '<extra></extra>'
        ))
        
        # ULSD
        fig_distillates.add_trace(go.Scatter(
            x=df_filtered.index,
            y=ulsd,
            mode='lines',
            name='ULSD',
            line=dict(color='#ff6b6b', width=2),
            hovertemplate='<b>Date</b>: %{x|%Y-%m-%d}<br>' +
                          '<b>USGC ULSD</b>: $%{y:.2f}<br>' +
                          '<extra></extra>'
        ))
        
        fig_distillates.update_layout(
            plot_bgcolor='#0a0a0a',
            paper_bgcolor='#0a0a0a',
            font=dict(family='Courier New, monospace', size=10, color='#faa537'),
            xaxis=dict(gridcolor='#1a1a1a', showgrid=True, zeroline=False, showline=True, linewidth=1, linecolor='#333333'),
            yaxis=dict(gridcolor='#1a1a1a', showgrid=True, zeroline=False, showline=True, linewidth=1, linecolor='#333333', tickprefix="$"),
            hovermode='x unified',
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1,
                bgcolor='rgba(0,0,0,0)',
                font=dict(color='#faa537')
            ),
            height=300,
            margin=dict(l=50, r=20, t=40, b=40)
        )
        
        st.plotly_chart(fig_distillates, use_container_width=True, config={'displayModeBar': False})
    
    # Chart 2: Gasoline Cracks
    with col2:
        st.markdown("**GASOLINE CRACKS**")
        fig_gasoline = go.Figure()
        
        # Calculate cracks
        nwe_gasoline = df_filtered['Gasoline Eurobob oxy NWE barge $/bbl'] - df_filtered['Ice Brent M1']
        sing_92 = df_filtered['Gasoline 92r Singapore'] - df_filtered['Dubai M1']
        usgc_gasoline = df_filtered['Gasoline 87 conv USGC waterborne $/bbl'] - df_filtered['Nymex WTI futures M1']
        
        # NWE Gasoline
        fig_gasoline.add_trace(go.Scatter(
            x=df_filtered.index,
            y=nwe_gasoline,
            mode='lines',
            name='NWE Gasoline',
            line=dict(color='#faa537', width=2),
            hovertemplate='<b>Date</b>: %{x|%Y-%m-%d}<br>' +
                          '<b>NWE Gasoline</b>: $%{y:.2f}<br>' +
                          '<extra></extra>'
        ))
        
        # Sing 92
        fig_gasoline.add_trace(go.Scatter(
            x=df_filtered.index,
            y=sing_92,
            mode='lines',
            name='Sing 92',
            line=dict(color='#00d9ff', width=2),
            hovertemplate='<b>Date</b>: %{x|%Y-%m-%d}<br>' +
                          '<b>Sing 92</b>: $%{y:.2f}<br>' +
                          '<extra></extra>'
        ))
        
        # USGC Gasoline
        fig_gasoline.add_trace(go.Scatter(
            x=df_filtered.index,
            y=usgc_gasoline,
            mode='lines',
            name='USGC Gasoline',
            line=dict(color='#ff6b6b', width=2),
            hovertemplate='<b>Date</b>: %{x|%Y-%m-%d}<br>' +
                          '<b>USGC Gasoline</b>: $%{y:.2f}<br>' +
                          '<extra></extra>'
        ))
        
        fig_gasoline.update_layout(
            plot_bgcolor='#0a0a0a',
            paper_bgcolor='#0a0a0a',
            font=dict(family='Courier New, monospace', size=10, color='#faa537'),
            xaxis=dict(gridcolor='#1a1a1a', showgrid=True, zeroline=False, showline=True, linewidth=1, linecolor='#333333'),
            yaxis=dict(gridcolor='#1a1a1a', showgrid=True, zeroline=False, showline=True, linewidth=1, linecolor='#333333', tickprefix="$"),
            hovermode='x unified',
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1,
                bgcolor='rgba(0,0,0,0)',
                font=dict(color='#faa537')
            ),
            height=300,
            margin=dict(l=50, r=20, t=40, b=40)
        )
        
        st.plotly_chart(fig_gasoline, use_container_width=True, config={'displayModeBar': False})
    
    # Row 2
    col3, col4 = st.columns(2)
    
    # Chart 3: Jet Cracks
    with col3:
        st.markdown("**JET FUEL CRACKS**")
        fig_jet = go.Figure()
        
        # Calculate cracks
        nwe_jet = df_filtered['Jet/kerosine NWE barge $/bbl'] - df_filtered['Ice Brent M1']
        sing_jet = df_filtered['Jet/kerosine Singapore'] - df_filtered['Dubai M1']
        usgc_jet = df_filtered['Jet fuel USGC waterborne fob $/bbl'] - df_filtered['Nymex WTI futures M1']
        
        # NWE Jet
        fig_jet.add_trace(go.Scatter(
            x=df_filtered.index,
            y=nwe_jet,
            mode='lines',
            name='NWE Jet',
            line=dict(color='#faa537', width=2),
            hovertemplate='<b>Date</b>: %{x|%Y-%m-%d}<br>' +
                          '<b>NWE Jet</b>: $%{y:.2f}<br>' +
                          '<extra></extra>'
        ))
        
        # Sing Jet
        fig_jet.add_trace(go.Scatter(
            x=df_filtered.index,
            y=sing_jet,
            mode='lines',
            name='Sing Jet',
            line=dict(color='#00d9ff', width=2),
            hovertemplate='<b>Date</b>: %{x|%Y-%m-%d}<br>' +
                          '<b>Sing Jet/Kero</b>: $%{y:.2f}<br>' +
                          '<extra></extra>'
        ))
        
        # USGC Jet
        fig_jet.add_trace(go.Scatter(
            x=df_filtered.index,
            y=usgc_jet,
            mode='lines',
            name='USGC Jet',
            line=dict(color='#ff6b6b', width=2),
            hovertemplate='<b>Date</b>: %{x|%Y-%m-%d}<br>' +
                          '<b>USGC Jet</b>: $%{y:.2f}<br>' +
                          '<extra></extra>'
        ))
        
        fig_jet.update_layout(
            plot_bgcolor='#0a0a0a',
            paper_bgcolor='#0a0a0a',
            font=dict(family='Courier New, monospace', size=10, color='#faa537'),
            xaxis=dict(gridcolor='#1a1a1a', showgrid=True, zeroline=False, showline=True, linewidth=1, linecolor='#333333'),
            yaxis=dict(gridcolor='#1a1a1a', showgrid=True, zeroline=False, showline=True, linewidth=1, linecolor='#333333', tickprefix="$"),
            hovermode='x unified',
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1,
                bgcolor='rgba(0,0,0,0)',
                font=dict(color='#faa537')
            ),
            height=300,
            margin=dict(l=50, r=20, t=40, b=40)
        )
        
        st.plotly_chart(fig_jet, use_container_width=True, config={'displayModeBar': False})
    
    # Chart 4: Asia Fuel Oil Crack
    with col4:
        st.markdown("**ASIA FUEL OIL CRACK**")
        fig_fueloil = go.Figure()
        
        # Calculate crack: (Fuel Oil $/mt / 6.35) - Dubai M1
        asia_fo_crack = (df_filtered['Fuel Oil 3.5% Sing 380 $/mt'] / 6.35) - df_filtered['Dubai M1']
        
        fig_fueloil.add_trace(go.Scatter(
            x=df_filtered.index,
            y=asia_fo_crack,
            mode='lines',
            line=dict(color='#faa537', width=2),
            fill='tozeroy',
            fillcolor='rgba(250, 165, 55, 0.2)',
            hovertemplate='<b>Date</b>: %{x|%Y-%m-%d}<br>' +
                          '<b>HSFO Crack</b>: $%{y:.2f}<br>' +
                          '<extra></extra>'
        ))
        
        fig_fueloil.update_layout(
            plot_bgcolor='#0a0a0a',
            paper_bgcolor='#0a0a0a',
            font=dict(family='Courier New, monospace', size=10, color='#faa537'),
            xaxis=dict(gridcolor='#1a1a1a', showgrid=True, zeroline=False, showline=True, linewidth=1, linecolor='#333333'),
            yaxis=dict(gridcolor='#1a1a1a', showgrid=True, zeroline=False, showline=True, linewidth=1, linecolor='#333333', tickprefix="$"),
            hovermode='x unified',
            showlegend=False,
            height=300,
            margin=dict(l=50, r=20, t=40, b=40)
        )
        
        st.plotly_chart(fig_fueloil, use_container_width=True, config={'displayModeBar': False})

# --- Tab 7: Freight ---
if st.session_state.active_tab == "Freight":
    st.subheader("TANKER RATES")
    
    # Get freight columns (columns 55-79, which are indices 54-78)
    all_columns = df.select_dtypes(include="number").columns.tolist()
    
    # Filter for freight columns based on column names containing "Tanker" or "Naphtha" or "TC14"
    freight_columns = [col for col in all_columns if 'Tanker' in col or 'TCE' in col in col]
    
    # Selectbox for freight route selection
    selected_freight = st.selectbox("Select Freight Route", freight_columns, key="freight_selector")
    
    
    fig_freight = go.Figure()
    
    fig_freight.add_trace(go.Scatter(
        x=df_filtered.index,
        y=df_filtered[selected_freight],
        mode='lines',
        name=selected_freight,
        line=dict(color='#faa537', width=2),
        fill='tozeroy',
        fillcolor='rgba(250, 165, 55, 0.2)',
        hovertemplate='<b>Date</b>: %{x|%Y-%m-%d}<br>' +
                      '<b>Rate</b>: %{y:.2f}<br>' +
                      '<extra></extra>'
    ))
    
    fig_freight.update_layout(
        plot_bgcolor='#0a0a0a',
        paper_bgcolor='#0a0a0a',
        font=dict(
            family='Courier New, monospace',
            size=12,
            color='#faa537'
        ),
        xaxis=dict(
            gridcolor='#1a1a1a',
            showgrid=True,
            zeroline=False,
            showline=True,
            linewidth=1,
            linecolor='#333333',
            mirror=True
        ),
        yaxis=dict(
            gridcolor='#1a1a1a',
            showgrid=True,
            zeroline=False,
            showline=True,
            linewidth=1,
            linecolor='#333333',
            mirror=True
        ),
        hovermode='x unified',
        showlegend=False,
        height=600,
        margin=dict(l=60, r=30, t=30, b=50)
    )
    
    # Update axes for cleaner look
    fig_freight.update_xaxes(
        showspikes=True,
        spikecolor='#faa537',
        spikesnap='cursor',
        spikemode='across',
        spikethickness=1
    )
    
    fig_freight.update_yaxes(
        showspikes=True,
        spikecolor='#faa537',
        spikesnap='cursor',
        spikemode='across',
        spikethickness=1
    )
    
    st.plotly_chart(fig_freight, use_container_width=True, config={'displayModeBar': False})
    
    # Display statistics
    col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
    
    latest_rate = df_filtered[selected_freight].iloc[0]
    prev_rate = df_filtered[selected_freight].iloc[-1] if len(df_filtered) > 1 else latest_rate
    rate_change = latest_rate - prev_rate
    pct_change = (rate_change / prev_rate) * 100 if prev_rate != 0 else 0
    
    with col_stat1:
        st.metric("Current Rate", f"{latest_rate:.2f}", f"{rate_change:+.2f}")
    with col_stat2:
        st.metric("% Change", f"{pct_change:+.2f}%")
    with col_stat3:
        st.metric("High", f"{df_filtered[selected_freight].max():.2f}")
    with col_stat4:
        st.metric("Low", f"{df_filtered[selected_freight].min():.2f}")
# if st.session_state.active_tab == "OilGPT":
#     run_oil_chatbot()