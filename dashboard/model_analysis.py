"""ML Model analysis page."""
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from typing import Dict, Any, List


def render_model_analysis(app_state: Dict[str, Any]) -> None:
    """Render ML model analysis and comparison."""
    st.title("🧠 Model Analysis")
    
    model_results = app_state.get('model_results', {})
    
    if not model_results:
        st.info(
            "Model analysis will appear after training. "
            f"Minimum {app_state.get('min_trades', 50)} closed trades required."
        )
        st.markdown("""
        **Current Status:**
        - Collecting crossover data and trade outcomes
        - Once sufficient trades are recorded, the ML pipeline will train automatically
        - Training uses chronological split to prevent look-ahead bias
        """)
        return
    
    # Dataset Info
    dataset_info = app_state.get('dataset_info', {})
    if dataset_info:
        st.subheader("📊 Dataset")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Samples", dataset_info.get('total', 0))
        with col2:
            st.metric("Train Size", dataset_info.get('train_size', 0))
        with col3:
            st.metric("Validation Size", dataset_info.get('val_size', 0))
        with col4:
            st.metric("Test Size", dataset_info.get('test_size', 0))
        
        # Class distribution
        pos_ratio = dataset_info.get('positive_ratio', 0.5)
        st.progress(pos_ratio, text=f"Class Distribution: {pos_ratio:.1%} profitable, {1-pos_ratio:.1%} losing")
    
    st.divider()
    
    # Model Comparison
    st.subheader("🏆 Strategy Comparison (Model Performance)")
    
    comparison_rows = []
    for name, result in model_results.items():
        if 'error' in result:
            continue
        test = result.get('test', {})
        val = result.get('validation', {})
        comparison_rows.append({
            'Algorithm': name.replace('_', ' ').title(),
            'Predictive Power (AUC)': f"{test.get('roc_auc', 0):.4f}",
            'Overall Accuracy': f"{test.get('accuracy', 0):.2%}",
            'True Profit Rate (Precision)': f"{test.get('precision', 0):.2%}",
            'Opportunity Capture (Recall)': f"{test.get('recall', 0):.2%}",
            'Confidence Threshold': f"{result.get('best_threshold', 0.5):.2f}",
        })
    
    if comparison_rows:
        df = pd.DataFrame(comparison_rows)
        st.dataframe(df, use_container_width=True, hide_index=True)
    
    best_model = app_state.get('best_model_name')
    if best_model:
        st.success(f"⭐ Active Production Model: **{best_model.replace('_', ' ').title()}**")
    
    st.divider()
    
    # Feature Importance
    st.subheader("🎯 What drives profitability? (Feature Importance)")
    
    feature_importance = app_state.get('feature_importance', {})
    if feature_importance:
        # Take top 15
        sorted_features = sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)[:15]
        names = [f[0].replace('_', ' ').title() for f in sorted_features]
        values = [f[1] for f in sorted_features]
        
        fig = go.Figure(go.Bar(
            x=values[::-1],
            y=names[::-1],
            orientation='h',
            marker=dict(
                color=values[::-1],
                colorscale=['#0F172A', '#3B82F6', '#06B6D4'],
                line=dict(color='#06B6D4', width=1)
            ),
        ))
        fig.update_layout(
            title="Top Predictors of a Profitable Trade",
            xaxis_title="Relative Impact on Prediction",
            height=450,
            template='plotly_dark',
            plot_bgcolor='#0B0E14',
            paper_bgcolor='#0B0E14',
            margin=dict(l=20, r=20, t=40, b=20)
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Feature importance will be displayed after model training.")
    
    # Confusion Matrix
    st.subheader("📊 Confusion Matrix")
    for name, result in model_results.items():
        if 'error' in result:
            continue
        test = result.get('test', {})
        cm = test.get('confusion_matrix')
        if cm and len(cm) == 2:
            st.markdown(f"**{name.replace('_', ' ').title()}**")
            fig = go.Figure(data=go.Heatmap(
                z=cm,
                x=['Predicted Losing', 'Predicted Profitable'],
                y=['Actual Losing', 'Actual Profitable'],
                text=[[str(v) for v in row] for row in cm],
                texttemplate="%{text}",
                colorscale='Blues',
                showscale=False,
            ))
            fig.update_layout(height=300, template='plotly_dark')
            st.plotly_chart(fig, use_container_width=True)
    
    # Threshold Analysis
    threshold_analysis = app_state.get('threshold_analysis', [])
    if threshold_analysis:
        st.subheader("🎯 Threshold Analysis")
        st.caption("Evaluated on validation data only (never on test data)")
        
        df = pd.DataFrame(threshold_analysis)
        df['threshold'] = df['threshold'].apply(lambda x: f"{x:.2f}")
        df['accepted_win_rate'] = df['accepted_win_rate'].apply(lambda x: f"{x:.1%}")
        df['f1'] = df['f1'].apply(lambda x: f"{x:.4f}")
        st.dataframe(df, use_container_width=True, hide_index=True)
