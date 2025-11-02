import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json

from database import get_db_session
from database.crud import QuestionCRUD

if not st.session_state.get("authenticated"):
    st.error("Please login")
    st.stop()

st.title("📈 Analytics Dashboard")

session = get_db_session()

try:
    df_attempts = pd.read_sql_query(
        """
        SELECT a.id, a.test_id, a.student_id, a.score, a.is_submitted, a.created_at, a.completed_at,
               t.title AS test_title,
               u.username AS student_name
        FROM attempts a
        JOIN tests t ON a.test_id = t.id
        JOIN users u ON a.student_id = u.id
        """,
        session.bind,
    )
except Exception as exc:  # noqa: BLE001
    st.error("Failed to load analytics data")
    session.close()
    st.stop()

if df_attempts.empty:
    st.info("No test attempts yet")
    session.close()
    st.stop()

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Attempts", len(df_attempts))
col2.metric("Unique Students", df_attempts["student_id"].nunique())
col3.metric("Average Score", f"{df_attempts['score'].mean():.1f}%")
col4.metric("Tests", df_attempts["test_id"].nunique())

# Tabs for different analytics views
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Overview",
    "🎯 Per-Question Analysis",
    "📈 Progress Tracking",
    "🔥 Topic Mastery",
    "📥 Export"
])

with tab1:
    st.subheader("Score Distribution")
    
    # Enhanced histogram with plotly
    fig_dist = px.histogram(
        df_attempts,
        x="score",
        nbins=20,
        title="Score Distribution Across All Attempts",
        labels={"score": "Score (%)", "count": "Number of Attempts"},
        color_discrete_sequence=["#1f77b4"]
    )
    fig_dist.update_layout(showlegend=False)
    st.plotly_chart(fig_dist, use_container_width=True)

    # Pre/Post comparison with visualization
    st.subheader("Pre/Post Improvement Analysis")
    
    # Select test to analyze
    tests = df_attempts[["test_id", "test_title"]].drop_duplicates().sort_values("test_title")
    test_titles = tests["test_title"].tolist()
    test_ids = tests["test_id"].tolist()
    selected = st.selectbox("Select a test", options=list(range(len(test_ids))), format_func=lambda i: test_titles[i])
    selected_test_id = test_ids[selected]
    
    df_sel = df_attempts[df_attempts["test_id"] == selected_test_id].copy()
    df_sel = df_sel.sort_values(["student_id", "created_at", "id"])
    
    # compute first and latest submitted attempt per student
    first_attempts = df_sel.groupby("student_id", as_index=False).first()[["student_id", "student_name", "score"]]
    first_attempts = first_attempts.rename(columns={"score": "pre_score"})
    latest_attempts = df_sel.groupby("student_id", as_index=False).last()[["student_id", "score"]]
    latest_attempts = latest_attempts.rename(columns={"score": "post_score"})
    merged = pd.merge(first_attempts, latest_attempts, on="student_id", how="left")
    merged["improvement"] = merged["post_score"] - merged["pre_score"]
    merged = merged.sort_values("improvement", ascending=False)
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Pre Avg", f"{merged['pre_score'].mean():.1f}%", help="Average first attempt score")
    c2.metric("Post Avg", f"{merged['post_score'].mean():.1f}%", help="Average latest attempt score")
    improvement_val = merged['improvement'].mean()
    c3.metric(
        "Avg Improvement",
        f"{improvement_val:.1f}%",
        delta=f"{improvement_val:.1f}%",
        help="Average improvement from first to latest attempt"
    )
    
    # Improvement waterfall chart
    fig_improvement = go.Figure()
    fig_improvement.add_trace(go.Bar(
        name='Pre Score',
        x=merged['student_name'],
        y=merged['pre_score'],
        marker_color='lightblue'
    ))
    fig_improvement.add_trace(go.Bar(
        name='Post Score',
        x=merged['student_name'],
        y=merged['post_score'],
        marker_color='darkblue'
    ))
    fig_improvement.update_layout(
        title="Pre vs Post Scores by Student",
        xaxis_title="Student",
        yaxis_title="Score (%)",
        barmode='group'
    )
    st.plotly_chart(fig_improvement, use_container_width=True)
    
    st.dataframe(
        merged[["student_name", "pre_score", "post_score", "improvement"]]
        .rename(columns={"student_name": "Student", "pre_score": "First Attempt", "post_score": "Latest Attempt", "improvement": "Improvement"}),
        use_container_width=True,
    )

    st.subheader("🏆 Top Performers (Latest attempts)")
    latest = df_attempts.sort_values(["student_id", "created_at", "id"]).groupby("student_id", as_index=False).last()
    top = latest.sort_values("score", ascending=False).head(10)[["student_name", "test_title", "score"]]
    
    # Leaderboard visualization
    fig_top = px.bar(
        top,
        x="score",
        y="student_name",
        orientation='h',
        title="Top 10 Students (Latest Attempts)",
        labels={"score": "Score (%)", "student_name": "Student"},
        color="score",
        color_continuous_scale="Viridis"
    )
    st.plotly_chart(fig_top, use_container_width=True)
    
    st.dataframe(top.rename(columns={"student_name": "Student", "test_title": "Test", "score": "Score"}), use_container_width=True)

with tab2:
    st.subheader("🎯 Per-Question Analysis")
    
    # Select test for question analysis
    test_select_q = st.selectbox("Select test for question breakdown", options=list(range(len(test_ids))), format_func=lambda i: test_titles[i], key="q_analysis")
    selected_test_q = test_ids[test_select_q]
    
    # Get all attempts for this test with answers
    df_test_attempts = df_attempts[df_attempts["test_id"] == selected_test_q].copy()
    
    if not df_test_attempts.empty:
        # Get questions for this test
        questions = QuestionCRUD.get_test_questions(session, selected_test_q)
        
        if questions:
            # Analyze each question
            question_stats = []
            for q in questions:
                correct_count = 0
                total_count = 0
                
                # Parse answers from attempts
                for _, attempt_row in df_test_attempts.iterrows():
                    attempt_obj = session.query(session.query(type(attempt_row)).statement.froms[0].entity_namespace['Attempt']).filter_by(id=attempt_row['id']).first()
                    if attempt_obj and attempt_obj.answers:
                        student_answer = attempt_obj.answers.get(str(q.id))
                        if student_answer is not None:
                            total_count += 1
                            if int(student_answer) == q.correct_answer:
                                correct_count += 1
                
                accuracy = (correct_count / total_count * 100) if total_count > 0 else 0
                question_stats.append({
                    "Question": f"Q{q.order + 1}",
                    "Text": q.question_text[:60] + "..." if len(q.question_text) > 60 else q.question_text,
                    "Topic": q.topic_tag,
                    "Difficulty": q.difficulty,
                    "Accuracy": accuracy,
                    "Attempts": total_count
                })
            
            df_q_stats = pd.DataFrame(question_stats)
            
            # Accuracy by question chart
            fig_q_acc = px.bar(
                df_q_stats,
                x="Question",
                y="Accuracy",
                color="Difficulty",
                title="Question Accuracy Rate",
                labels={"Accuracy": "Accuracy (%)"},
                color_discrete_map={"easy": "green", "medium": "orange", "hard": "red"}
            )
            st.plotly_chart(fig_q_acc, use_container_width=True)
            
            st.dataframe(df_q_stats, use_container_width=True)
            
            # Difficulty breakdown
            st.subheader("Difficulty Analysis")
            diff_stats = df_q_stats.groupby("Difficulty")["Accuracy"].mean().reset_index()
            fig_diff = px.pie(
                diff_stats,
                values="Accuracy",
                names="Difficulty",
                title="Average Accuracy by Difficulty",
                color="Difficulty",
                color_discrete_map={"easy": "green", "medium": "orange", "hard": "red"}
            )
            st.plotly_chart(fig_diff, use_container_width=True)
        else:
            st.info("No questions found for this test.")
    else:
        st.info("No attempts for this test yet.")

with tab3:
    st.subheader("📈 Progress Tracking Over Time")
    
    # Time series of scores
    df_time = df_attempts.copy()
    df_time['date'] = pd.to_datetime(df_time['created_at']).dt.date
    
    # Average score over time
    daily_avg = df_time.groupby('date')['score'].mean().reset_index()
    fig_time = px.line(
        daily_avg,
        x='date',
        y='score',
        title='Average Score Trend Over Time',
        labels={'date': 'Date', 'score': 'Average Score (%)'},
        markers=True
    )
    st.plotly_chart(fig_time, use_container_width=True)
    
    # Student journey
    st.subheader("Individual Student Journey")
    students = df_attempts['student_name'].unique()
    selected_student = st.selectbox("Select student", students)
    
    df_student = df_attempts[df_attempts['student_name'] == selected_student].sort_values('created_at')
    
    if not df_student.empty:
        fig_journey = px.line(
            df_student,
            x='created_at',
            y='score',
            title=f"{selected_student}'s Score Journey",
            labels={'created_at': 'Date', 'score': 'Score (%)'},
            markers=True
        )
        st.plotly_chart(fig_journey, use_container_width=True)
        
        # Student stats
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Attempts", len(df_student))
        col2.metric("Average Score", f"{df_student['score'].mean():.1f}%")
        col3.metric("Best Score", f"{df_student['score'].max():.1f}%")
        col4.metric("Latest Score", f"{df_student.iloc[-1]['score']:.1f}%")
        
        st.dataframe(
            df_student[['test_title', 'score', 'created_at']].rename(
                columns={'test_title': 'Test', 'score': 'Score (%)', 'created_at': 'Date'}
            ),
            use_container_width=True
        )

with tab4:
    st.subheader("🔥 Topic Mastery Heatmap")
    
    # Get all questions and their topics
    all_questions = []
    for test_id in test_ids:
        qs = QuestionCRUD.get_test_questions(session, test_id)
        all_questions.extend(qs)
    
    if all_questions:
        # Build topic performance matrix
        topic_performance = {}
        
        for student_name in df_attempts['student_name'].unique():
            student_attempts = df_attempts[df_attempts['student_name'] == student_name]
            topic_scores = {}
            
            for _, attempt_row in student_attempts.iterrows():
                # Get questions for this test
                test_questions = [q for q in all_questions if q.test_id == attempt_row['test_id']]
                
                for q in test_questions:
                    topic = q.topic_tag
                    if topic not in topic_scores:
                        topic_scores[topic] = []
                    
                    # Simplified: use overall score as proxy (in real scenario, parse answers)
                    topic_scores[topic].append(attempt_row['score'])
            
            # Average by topic
            for topic, scores in topic_scores.items():
                if topic not in topic_performance:
                    topic_performance[topic] = {}
                topic_performance[topic][student_name] = sum(scores) / len(scores)
        
        # Create heatmap dataframe
        if topic_performance:
            df_heatmap = pd.DataFrame(topic_performance).T
            
            fig_heatmap = px.imshow(
                df_heatmap,
                labels=dict(x="Student", y="Topic", color="Score (%)"),
                title="Topic Mastery Heatmap",
                color_continuous_scale="RdYlGn",
                aspect="auto"
            )
            st.plotly_chart(fig_heatmap, use_container_width=True)
            
            # Topic summary
            st.subheader("Topic Performance Summary")
            topic_avg = df_heatmap.mean(axis=1).sort_values(ascending=False)
            st.bar_chart(topic_avg)
        else:
            st.info("Not enough data for topic analysis.")
    else:
        st.info("No questions available for topic analysis.")

with tab5:
    st.subheader("📥 Export Analytics Data")
    
    st.write("Download analytics data in various formats:")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Export all attempts as CSV
        csv_attempts = df_attempts.to_csv(index=False)
        st.download_button(
            label="📊 Download All Attempts (CSV)",
            data=csv_attempts,
            file_name=f"test_attempts_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
        
        # Export student summary
        student_summary = df_attempts.groupby('student_name').agg({
            'score': ['mean', 'max', 'min', 'count']
        }).reset_index()
        student_summary.columns = ['Student', 'Avg Score', 'Best Score', 'Worst Score', 'Total Attempts']
        csv_summary = student_summary.to_csv(index=False)
        st.download_button(
            label="👥 Download Student Summary (CSV)",
            data=csv_summary,
            file_name=f"student_summary_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
    
    with col2:
        # Export test summary
        test_summary = df_attempts.groupby('test_title').agg({
            'score': ['mean', 'max', 'min', 'count']
        }).reset_index()
        test_summary.columns = ['Test', 'Avg Score', 'Best Score', 'Worst Score', 'Total Attempts']
        csv_test = test_summary.to_csv(index=False)
        st.download_button(
            label="📝 Download Test Summary (CSV)",
            data=csv_test,
            file_name=f"test_summary_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
        
        # Export improvement data
        if not merged.empty:
            csv_improvement = merged.to_csv(index=False)
            st.download_button(
                label="📈 Download Improvement Data (CSV)",
                data=csv_improvement,
                file_name=f"improvement_data_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
    
    st.info("💡 Tip: Open CSV files in Excel or Google Sheets for further analysis.")

session.close()
