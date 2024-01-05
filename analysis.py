import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import plotly.graph_objects as go
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.sentiment import SentimentIntensityAnalyzer
import nltk
nltk.download()
def preprocess_text_data(text_data):
    stopwords_set = set(stopwords.words('english'))
    text_data.loc[:, 'text'] = text_data['text'].apply(lambda words: ' '.join(word.lower() for word in word_tokenize(words) if word.lower() not in stopwords_set))
    text_data.loc[:, 'title'] = text_data['title'].apply(lambda words: ' '.join(word.lower() for word in word_tokenize(words) if word.lower() not in stopwords_set))

    sia = SentimentIntensityAnalyzer()
    text_data['Sentiment'] = text_data['text'].apply(lambda text: sia.polarity_scores(text)['compound'])
    text_data = text_data.sort_values(by='timestamp')

    text_data['timestamp'] = pd.to_datetime(text_data['timestamp'])
    text_data['Hastext'] = text_data['text'].apply(lambda x: 0 if x.strip() == '' else 1)


    daily_sentiment = text_data.groupby(text_data['timestamp'].dt.date)['Sentiment'].mean().reset_index()
    daily_sentiment['timestamp'] = pd.to_datetime(daily_sentiment['timestamp'])
    daily_sentiment = daily_sentiment.rename(columns={"timestamp": "Date"})
    # Categorize sentiment as positive, negative, or neutral
    daily_sentiment['SentimentCategory'] = pd.cut(text_data['Sentiment'], bins=[-1, -0.2, 0.2, 1], labels=['Negative', 'Neutral', 'Positive'])

    return daily_sentiment

def merge_sentiment_and_price(daily_sentiment, price_df):
    merged_df = pd.merge(daily_sentiment, price_df, on='Date', how='inner')
    return merged_df

def plot_sentiment_price(merged_df):
    fig = px.line(merged_df, x='Date', y=['Sentiment', 'close'], labels={'value': 'Value', 'variable': 'Metric'}, title='Sentiment and Price Over Days')
    return fig

def plot_posts_per_day(posts_per_day_data):
    fig = px.bar(posts_per_day_data, x='timestamp', y='Hastext', labels={'timestamp': 'Date', 'Hastext': 'Number of Posts'}, title='Number of Posts per Day')
    return fig

def plot_sentiment_distribution(sentiment_distribution_data):
    if isinstance(sentiment_distribution_data, list):
        # If sentiment_distribution_data is a list, assume it contains labels and values
        labels = [item['SentimentCategory'] for item in sentiment_distribution_data]
        values = [item['count'] for item in sentiment_distribution_data]
    elif isinstance(sentiment_distribution_data, dict):
        # If sentiment_distribution_data is a dictionary, extract keys and values
        labels = list(sentiment_distribution_data.keys())
        values = list(sentiment_distribution_data.values())
    else:
        raise ValueError("Unsupported data type for sentiment_distribution_data")

    fig = px.pie(names=labels, values=values, title='Sentiment Distribution', color_discrete_sequence=['green', 'gray', 'red'])
    return fig

def plot_top_posts_sentiment(top_posts):
    print(f'top posts  = {type(top_posts)}')
    colors = ['red' if sentiment['Sentiment'] < 0 else 'green' for sentiment in top_posts]

    fig = px.scatter(top_posts, x='upvotes', y='Sentiment', size='upvotes', color=colors, opacity=0.7,
                     labels={'upvotes': 'Upvotes', 'Sentiment': 'Sentiment'}, title='Top 5 Posts of the Past Day: Upvotes vs. Sentiment')

    return fig

def get_plots(daily_sentiment, price_df, filtered_posts, sentiment_distribution_data, top_posts):
    # Plot Sentiment and Price
    sentiment_price_plot = plot_sentiment_price(merge_sentiment_and_price(daily_sentiment, price_df))

    # Plot Posts Per Day
    posts_per_day_plot = plot_posts_per_day(filtered_posts)

    # Plot Sentiment Distribution
    sentiment_distribution_plot = plot_sentiment_distribution(sentiment_distribution_data)

    # Plot Top 5 Posts Sentiment
    top_posts_plot = plot_top_posts_sentiment(top_posts)

    return sentiment_price_plot, posts_per_day_plot, sentiment_distribution_plot, top_posts_plot
