from urlextract import URLExtract
from wordcloud import WordCloud
import pandas as pd
from collections import Counter
import emoji
import re

extract = URLExtract()

def fetch_stats(selected_user, df):
    if selected_user != 'Overall':
        df = df[df['user'] == selected_user]

    num_messages = df.shape[0]
    words = []
    for message in df['message']:
        if isinstance(message, str):
            words.extend(message.split())

    num_media_messages = df[df['message'] == '<Media omitted>\n'].shape[0]

    links = []
    for message in df['message']:
        if isinstance(message, str):
            links.extend(extract.find_urls(message))

    return num_messages, len(words), num_media_messages, len(links)

def most_busy_users(df):
    x = df['user'].value_counts().head()
    df_percent = round((df['user'].value_counts() / df.shape[0]) * 100, 2).reset_index()
    df_percent.columns = ['name', 'percent']
    return x, df_percent

def create_wordcloud(selected_user, df):
    try:
        # Read stop words with error handling
        try:
            with open('stop_hinglish.txt', 'r', encoding='utf-8') as f:
                stop_words = set(f.read().splitlines())
        except FileNotFoundError:
            print("stop_hinglish.txt not found. Using minimal stop words.")
            stop_words = set(['the', 'and', 'to', 'of', 'i', 'a', 'you', 'is', 'in', 'it'])

        if selected_user != 'Overall':
            df = df[df['user'] == selected_user]

        # Filter out notifications and media messages
        temp = df[(df['user'] != 'group_notification') & 
                (~df['message'].str.contains('<Media omitted>', na=False))]
        
        # Remove empty messages
        temp = temp[temp['message'].str.strip().astype(bool)]

        if temp.empty:
            return None

        # Custom cleaning function
        def clean_message(message):
            if not isinstance(message, str):
                return ""
            # Remove URLs
            message = re.sub(r'http\S+|www\S+|https\S+', '', message, flags=re.MULTILINE)
            # Remove special characters except spaces and letters
            message = re.sub(r'[^\w\s]', '', message)
            # Remove numbers
            message = re.sub(r'\d+', '', message)
            # Convert to lowercase and split
            words = message.lower().split()
            # Remove stopwords and short words (length < 3)
            return ' '.join([word for word in words if word not in stop_words and len(word) > 2])

        # Apply cleaning
        cleaned_messages = temp['message'].apply(clean_message)
        
        # Combine all messages
        text = ' '.join(cleaned_messages)
        
        if not text.strip():
            return None

        # Generate wordcloud
        wc = WordCloud(width=800, height=400, 
                      background_color='white',
                      max_words=200,
                      stopwords=stop_words,
                      min_font_size=10)
        wordcloud = wc.generate(text)
        return wordcloud
    except Exception as e:
        print(f"WordCloud generation error: {e}")
        return None

def most_common_words(selected_user, df):
    try:
        # Read stop words
        try:
            with open('stop_hinglish.txt', 'r', encoding='utf-8') as f:
                stop_words = set(f.read().splitlines())
        except FileNotFoundError:
            stop_words = set(['the', 'and', 'to', 'of', 'i', 'a', 'you', 'is', 'in', 'it'])

        if selected_user != 'Overall':
            df = df[df['user'] == selected_user]

        # Filter data
        temp = df[(df['user'] != 'group_notification') & 
                (~df['message'].str.contains('<Media omitted>', na=False))]
        
        # Remove empty messages
        temp = temp[temp['message'].str.strip().astype(bool)]

        if temp.empty:
            return pd.DataFrame()

        # Extract words
        words = []
        for message in temp['message']:
            if isinstance(message, str):
                # Clean message
                message = re.sub(r'[^\w\s]', '', message.lower())
                # Add words not in stopwords and with length > 2
                words.extend([word for word in message.split() 
                             if word not in stop_words and len(word) > 2])

        if not words:
            return pd.DataFrame()

        # Get most common words
        common_words = Counter(words).most_common(20)
        return pd.DataFrame(common_words, columns=['Word', 'Count'])
    except Exception as e:
        print(f"Common words error: {e}")
        return pd.DataFrame()

def emoji_helper(selected_user, df):
    if selected_user != 'Overall':
        df = df[df['user'] == selected_user]

    emojis = []
    for message in df['message']:
        if isinstance(message, str):
            emojis.extend([c for c in message if c in emoji.EMOJI_DATA])

    if emojis:
        emoji_df = pd.DataFrame(Counter(emojis).most_common(len(Counter(emojis))))
        return emoji_df
    return pd.DataFrame()

def monthly_timeline(selected_user, df):
    if selected_user != 'Overall':
        df = df[df['user'] == selected_user]

    timeline = df.groupby(['year', 'month_num', 'month']).count()['message'].reset_index()
    timeline['time'] = timeline['month'] + "-" + timeline['year'].astype(str)
    return timeline

def daily_timeline(selected_user, df):
    if selected_user != 'Overall':
        df = df[df['user'] == selected_user]

    return df.groupby('only_date').count()['message'].reset_index()

def week_activity_map(selected_user, df):
    if selected_user != 'Overall':
        df = df[df['user'] == selected_user]

    return df['day_name'].value_counts()

def month_activity_map(selected_user, df):
    if selected_user != 'Overall':
        df = df[df['user'] == selected_user]

    return df['month'].value_counts()

def activity_heatmap(selected_user, df):
    if selected_user != 'Overall':
        df = df[df['user'] == selected_user]

    user_heatmap = df.pivot_table(index='day_name', columns='period', values='message', aggfunc='count').fillna(0)
    return user_heatmap
