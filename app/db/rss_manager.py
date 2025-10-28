import sqlite3
import feedparser

class RssManager:
    def __init__(self, conn):
        self.conn = conn

    def add_feed(self, name, url):
        """Adds a new RSS feed to the database."""
        cursor = self.conn.cursor()
        try:
            cursor.execute("INSERT INTO rss_feeds (name, url) VALUES (?, ?)", (name, url))
            self.conn.commit()
            new_id = cursor.lastrowid
        except sqlite3.IntegrityError:
            new_id = None # Feed with this URL already exists
        return new_id

    def get_all_feeds(self):
        """Retrieves all RSS feeds from the database."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, name, url FROM rss_feeds ORDER BY name ASC")
        feeds = [dict(row) for row in cursor.fetchall()]
        return feeds

    def delete_feed(self, feed_id):
        """Deletes an RSS feed from the database."""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM rss_feeds WHERE id = ?", (feed_id,))
        self.conn.commit()

    @staticmethod
    def fetch_feed_items(feed_url):
        """Fetches and parses RSS feed items from a given URL."""
        try:
            feed = feedparser.parse(feed_url)
            
            if feed.bozo:
                print(f"Error parsing feed {feed_url}: {feed.bozo_exception}")
                return []

            if feed.status != 200:
                print(f"Error fetching feed {feed_url}: HTTP Status {feed.status}")
                return []

            items = []
            for entry in feed.entries:
                items.append({
                    'title': entry.title,
                    'link': entry.link,
                    'summary': entry.summary if hasattr(entry, 'summary') else 'No summary available.',
                    'published': entry.published if hasattr(entry, 'published') else 'N/A',
                })
            return items
        except Exception as e:
            print(f"An unexpected error occurred while fetching feed {feed_url}: {e}")
            return []