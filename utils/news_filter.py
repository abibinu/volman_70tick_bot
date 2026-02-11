from datetime import datetime, timedelta
import logging

class NewsFilter:
    def __init__(self, buffer_minutes=15):
        self.buffer_minutes = buffer_minutes
        self.news_events = []

    def is_news_active(self, current_time=None):
        if current_time is None:
            current_time = datetime.now()
        for event_time in self.news_events:
            start_block = event_time - timedelta(minutes=self.buffer_minutes)
            end_block = event_time + timedelta(minutes=self.buffer_minutes)
            if start_block <= current_time <= end_block:
                return True
        return False

    def add_event(self, event_time):
        self.news_events.append(event_time)
