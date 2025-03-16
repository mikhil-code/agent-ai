import json
import os
from datetime import datetime, timedelta
from typing import Dict, Optional

class SchemaCache:
    def __init__(self, cache_file: str = 'schema_cache.json'):
        self.cache_file = cache_file
        self.cache_ttl = timedelta(hours=24)  # Cache valid for 24 hours

    def get_cached_schema(self) -> Optional[Dict]:
        if not os.path.exists(self.cache_file):
            return None

        try:
            with open(self.cache_file, 'r') as f:
                cache_data = json.load(f)
                
            cached_time = datetime.fromisoformat(cache_data['timestamp'])
            if datetime.now() - cached_time > self.cache_ttl:
                return None
                
            return cache_data['schema']
        except Exception:
            return None

    def save_schema(self, schema_info: Dict):
        cache_data = {
            'timestamp': datetime.now().isoformat(),
            'schema': schema_info
        }
        
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2, default=str)
        except Exception as e:
            print(f"Failed to cache schema: {str(e)}")
