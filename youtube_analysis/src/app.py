import streamlit as st
import plotly.express as px
import pandas as pd
from services.youtube import YouTubeService
from services.sentiment import SentimentAnalyzer
import os
from dotenv import load_dotenv
from streamlit.runtime.scriptrunner import StopException
import time

load_dotenv()

def handle_reply(youtube_service, comment_id, reply_text):
    try:
        reply = youtube_service.reply_to_comment(comment_id, reply_text)
        st.session_state.replies[comment_id] = reply
        return True
    except Exception as e:
        st.error(f"Failed to post reply: {str(e)}")
        return False

def main():
    st.title("YouTube Comments Sentiment Analysis")
    
    # Initialize session states
    if 'replies' not in st.session_state:
        st.session_state.replies = {}
    if 'analyzed_comments' not in st.session_state:
        st.session_state.analyzed_comments = None
    
    # Initialize services
    youtube_service = YouTubeService()
    sentiment_analyzer = SentimentAnalyzer()

    # URL input
    url = st.text_input("Enter YouTube Video URL")
    
    if url:
        try:
            # Only fetch and analyze if we don't have results or URL changed
            if 'current_url' not in st.session_state or st.session_state.current_url != url:
                with st.spinner("Fetching comments..."):
                    video_id = youtube_service.extract_video_id(url)
                    comments = youtube_service.get_comments(video_id)
                
                with st.spinner("Analyzing sentiments..."):
                    analyzed_comments = sentiment_analyzer.batch_analyze(comments)
                    st.session_state.analyzed_comments = analyzed_comments
                    st.session_state.current_url = url
            
            df = pd.DataFrame(st.session_state.analyzed_comments)
                
            # Display results
            st.subheader("Sentiment Distribution")
            fig = px.pie(df, names='sentiment', title='Comment Sentiments')
            st.plotly_chart(fig)
            
            # Display comments with reply option
            st.subheader("Comments")
            sentiment_filter = st.selectbox("Filter by sentiment", 
                                         ['All', 'POSITIVE', 'NEGATIVE', 'NEUTRAL'])
            
            filtered_df = df if sentiment_filter == 'All' \
                else df[df['sentiment'] == sentiment_filter]
            
            # Display comments in expandable containers
            for _, comment in filtered_df.iterrows():
                with st.expander(f"{comment['text'][:100]}..."):
                    st.write(f"**Author:** {comment['author']}")
                    st.write(f"**Sentiment:** {comment['sentiment']}")
                    st.write(f"**Likes:** {comment['likes']}")
                    
                    # Reply section using form
                    if comment['comment_id'] not in st.session_state.replies:
                        with st.form(key=f"reply_form_{comment['comment_id']}"):
                            reply_text = st.text_area("Write a reply:", key=f"reply_{comment['comment_id']}")
                            submit = st.form_submit_button("Post Reply")
                            if submit and reply_text:
                                if handle_reply(youtube_service, comment['comment_id'], reply_text):
                                    st.success("Reply posted successfully!")
                    else:
                        st.write("**Your Reply:**")
                        reply = st.session_state.replies[comment['comment_id']]
                        st.write(reply['text'])
            
            # Export results
            csv = filtered_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                "Download Results",
                csv,
                "youtube_comments_analysis.csv",
                "text/csv",
                key='download-csv'
            )
            
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main()
