from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
import pickle
import os
from googleapiclient.discovery import build
from typing import List, Dict

class YouTubeService:
    def __init__(self):
        self.api_key = os.getenv('YOUTUBE_API_KEY')
        self.credentials = None
        self.oauth_scopes = ['https://www.googleapis.com/auth/youtube.force-ssl']
        
    def authenticate(self):
        creds = None
        # Load saved credentials if they exist
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)
                
        # If no valid credentials available, let user log in
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'client_secrets.json', self.oauth_scopes)
                creds = flow.run_local_server(port=8080)
            # Save credentials for future use
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)
        
        self.credentials = creds
        return creds

    def get_youtube_service(self, require_auth=False):
        if require_auth:
            if not self.credentials:
                self.authenticate()
            return build('youtube', 'v3', credentials=self.credentials)
        return build('youtube', 'v3', developerKey=self.api_key)

    def extract_video_id(self, url: str) -> str:
        if 'v=' in url:
            return url.split('v=')[1].split('&')[0]
        elif 'youtu.be/' in url:
            return url.split('youtu.be/')[1].split('?')[0]
        raise ValueError("Invalid YouTube URL")

    def get_comments(self, video_id: str, max_results: int = 100) -> List[Dict]:
        comments = []
        try:
            youtube = self.get_youtube_service()
            request = youtube.commentThreads().list(
                part="snippet",
                videoId=video_id,
                maxResults=max_results
            )
            while request and len(comments) < max_results:
                response = request.execute()
                for item in response['items']:
                    comment = item['snippet']['topLevelComment']['snippet']
                    comments.append({
                        'comment_id': item['id'],
                        'text': comment['textDisplay'],
                        'author': comment['authorDisplayName'],
                        'likes': comment['likeCount'],
                        'timestamp': comment['publishedAt']
                    })
                request = youtube.commentThreads().list_next(request, response)
            
            return comments
        except Exception as e:
            raise Exception(f"Error fetching comments: {str(e)}")

    def reply_to_comment(self, comment_id: str, reply_text: str) -> Dict:
        try:
            # Use authenticated service for replying
            youtube = self.get_youtube_service(require_auth=True)
            response = youtube.comments().insert(
                part="snippet",
                body={
                    "snippet": {
                        "parentId": comment_id,
                        "textOriginal": reply_text
                    }
                }
            ).execute()
            
            return {
                'reply_id': response['id'],
                'text': response['snippet']['textOriginal'],
                'author': response['snippet']['authorDisplayName'],
                'timestamp': response['snippet']['publishedAt']
            }
        except Exception as e:
            raise Exception(f"Error posting reply: {str(e)}")
