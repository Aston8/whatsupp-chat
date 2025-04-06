import re
import pandas as pd
from datetime import datetime
import unicodedata

def preprocess(data):
    pattern = r'\d{1,2}/\d{1,2}/\d{2,4},\s\d{1,2}:\d{2}\s*[AP]M\s*-\s*|\d{1,2}/\d{1,2}/\d{2,4},\s\d{1,2}:\d{2}\s*-\s*'

    messages = re.split(pattern, data)[1:]
    dates = re.findall(pattern, data)

    if len(messages) != len(dates):
        raise ValueError(f"Mismatch between messages ({len(messages)}) and dates ({len(dates)})")

    df = pd.DataFrame({'user_message': messages, 'message_date': dates})
    
    def parse_date(date_str):
        try:
            date_str = unicodedata.normalize("NFKD", date_str.strip())
            date_str = date_str.replace('\u202f', ' ').replace('\xa0', ' ')
            date_str = re.sub(r'\s+', ' ', date_str).strip('-').strip()
            
            if 'AM' in date_str or 'PM' in date_str:
                for fmt in [
                    '%m/%d/%y, %I:%M %p',
                    '%d/%m/%y, %I:%M %p',
                    '%m/%d/%Y, %I:%M %p',
                    '%d/%m/%Y, %I:%M %p'
                ]:
                    try:
                        return datetime.strptime(date_str, fmt)
                    except ValueError:
                        continue
            
            for fmt in [
                '%m/%d/%y, %H:%M',
                '%d/%m/%y, %H:%M',
                '%m/%d/%Y, %H:%M',
                '%d/%m/%Y, %H:%M'
            ]:
                try:
                    return datetime.strptime(date_str, fmt)
                except ValueError:
                    continue
            
            raise ValueError(f"No matching format found for: {date_str}")
        except Exception as e:
            raise ValueError(f"Failed to parse date: {date_str}. Error: {str(e)}")

    try:
        df['message_date'] = df['message_date'].apply(parse_date)
    except Exception as e:
        sample_errors = "\n".join(df['message_date'].head(5).tolist())
        raise ValueError(f"Date parsing failed. First few dates:\n{sample_errors}\n\nError: {str(e)}")

    df.rename(columns={'message_date': 'date'}, inplace=True)

    users = []
    processed_messages = []
    for message in df['user_message']:
        message = str(message).strip()
        entry = re.split(r'([^:]+):\s', message, maxsplit=1)
        if len(entry) > 2:
            users.append(entry[1].strip())
            processed_messages.append(entry[2].strip())
        else:
            users.append('group_notification')
            processed_messages.append(message)

    df['user'] = users
    df['message'] = processed_messages
    df.drop(columns=['user_message'], inplace=True)

    df['only_date'] = df['date'].dt.date
    df['year'] = df['date'].dt.year
    df['month_num'] = df['date'].dt.month
    df['month'] = df['date'].dt.month_name()
    df['day'] = df['date'].dt.day
    df['day_name'] = df['date'].dt.day_name()
    df['hour'] = df['date'].dt.hour
    df['minute'] = df['date'].dt.minute

    df['period'] = df['hour'].apply(
        lambda hour: f"{hour}-{hour+1}" if hour < 23 else "23-00"
    )

    return df