import streamlit as st
import preprocessor, helper
import matplotlib.pyplot as plt
import seaborn as sns

# Set page config
st.set_page_config(page_title="WhatsApp Chat Analyzer", layout="wide")

# Title
st.title("WhatsApp Chat Analyzer")

# File upload section
st.sidebar.header("Upload Your Chat File")
uploaded_file = st.sidebar.file_uploader("Choose a WhatsApp chat file")

if uploaded_file is not None:
    try:
        bytes_data = uploaded_file.getvalue()
        data = bytes_data.decode("utf-8")

        with st.spinner("Processing chat..."):
            df = preprocessor.preprocess(data)

        user_list = df['user'].unique().tolist()
        if 'group_notification' in user_list:
            user_list.remove('group_notification')
        user_list.sort()
        user_list.insert(0, "Overall")

        selected_user = st.sidebar.selectbox("Analyze messages by", user_list)

        if st.sidebar.button("Start Analysis"):
            # Statistics section
            st.markdown("## Top Statistics")
            num_messages, words, num_media_messages, num_links = helper.fetch_stats(selected_user, df)

            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Messages", num_messages)
            with col2:
                st.metric("Words", words)
            with col3:
                st.metric("Media Shared", num_media_messages)
            with col4:
                st.metric("Links Shared", num_links)

            # Timeline section
            st.markdown("## Message Timeline")

            col1, col2 = st.columns(2)
            with col1:
                st.subheader("Monthly Timeline")
                timeline = helper.monthly_timeline(selected_user, df)
                if not timeline.empty:
                    fig, ax = plt.subplots()
                    ax.plot(timeline['time'], timeline['message'], color='#6366f1')
                    ax.set_xlabel("Month")
                    ax.set_ylabel("Messages")
                    plt.xticks(rotation='vertical')
                    st.pyplot(fig)

            with col2:
                st.subheader("Daily Timeline")
                daily_timeline = helper.daily_timeline(selected_user, df)
                if not daily_timeline.empty:
                    fig, ax = plt.subplots()
                    ax.plot(daily_timeline['only_date'], daily_timeline['message'], color='#10b981')
                    ax.set_xlabel("Date")
                    ax.set_ylabel("Messages")
                    plt.xticks(rotation='vertical')
                    st.pyplot(fig)

            # Activity section
            st.markdown("## Weekly and Monthly Activity")

            col1, col2 = st.columns(2)
            with col1:
                st.subheader("Most Active Days")
                busy_day = helper.week_activity_map(selected_user, df)
                if not busy_day.empty:
                    fig, ax = plt.subplots()
                    sns.barplot(x=busy_day.index, y=busy_day.values, palette='magma', ax=ax)
                    ax.set_ylabel("Messages")
                    ax.set_xlabel("Day")
                    st.pyplot(fig)

            with col2:
                st.subheader("Most Active Months")
                busy_month = helper.month_activity_map(selected_user, df)
                if not busy_month.empty:
                    fig, ax = plt.subplots()
                    sns.barplot(x=busy_month.index, y=busy_month.values, palette='coolwarm', ax=ax)
                    ax.set_ylabel("Messages")
                    ax.set_xlabel("Month")
                    st.pyplot(fig)

            # Heatmap
            st.markdown("## Weekly Activity Heatmap")
            user_heatmap = helper.activity_heatmap(selected_user, df)
            if not user_heatmap.empty:
                days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                for day in days:
                    if day not in user_heatmap.index:
                        user_heatmap.loc[day] = 0
                user_heatmap = user_heatmap.loc[days]

                periods = [f"{hour}-{hour+1}" for hour in range(24)]
                for period in periods:
                    if period not in user_heatmap.columns:
                        user_heatmap[period] = 0
                user_heatmap = user_heatmap[periods]

                fig, ax = plt.subplots(figsize=(14, 5))
                sns.heatmap(user_heatmap, cmap="YlGnBu", ax=ax)
                ax.set_xlabel("Hour")
                ax.set_ylabel("Day")
                ax.set_title("Messages by Time and Day")
                st.pyplot(fig)

            # Most Active Users
            if selected_user == 'Overall':
                st.markdown("## Most Active Users")
                x, new_df = helper.most_busy_users(df)
                col1, col2 = st.columns([1, 1])
                with col1:
                    fig, ax = plt.subplots()
                    sns.barplot(x=x.values, y=x.index, palette="Reds_r", ax=ax)
                    ax.set_xlabel("Message Count")
                    st.pyplot(fig)
                with col2:
                    st.dataframe(new_df)

            # Word Cloud
            st.markdown("## Word Cloud")
            df_wc = helper.create_wordcloud(selected_user, df)
            if df_wc is not None:
                fig, ax = plt.subplots(figsize=(10, 5))
                ax.imshow(df_wc, interpolation='bilinear')
                ax.axis("off")
                st.pyplot(fig)

            # Emoji Analysis
            st.markdown("## Emoji Analysis")
            emoji_df = helper.emoji_helper(selected_user, df)
            if not emoji_df.empty:
                col1, col2 = st.columns(2)
                with col1:
                    st.dataframe(emoji_df.head(10))
                with col2:
                    fig, ax = plt.subplots()
                    ax.pie(emoji_df[1].head(), labels=emoji_df[0].head(), autopct="%0.2f")
                    st.pyplot(fig)

    except Exception as e:
        st.error(f"Error: {str(e)}")
        st.error("Please upload a valid WhatsApp exported chat file.")
