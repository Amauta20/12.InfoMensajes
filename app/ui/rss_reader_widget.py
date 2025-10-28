from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QPushButton, QInputDialog, QMessageBox, QListWidgetItem, QLabel, QSplitter
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QDesktopServices
from app.db.rss_manager import RssManager
from app.db import database
from app.ui.rss_article_item_widget import RssArticleItemWidget

class RssReaderWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.conn = database.get_db_connection()
        self.manager = RssManager(self.conn)
        self.current_feed_url = None

        self.layout = QHBoxLayout(self)
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.layout.addWidget(self.splitter)

        # Left side: RSS feed list
        self.feed_list_widget = QWidget()
        self.feed_list_layout = QVBoxLayout(self.feed_list_widget)
        self.feed_list = QListWidget()
        self.feed_list.itemClicked.connect(self.on_feed_selected)
        self.feed_list_layout.addWidget(self.feed_list)

        self.feed_buttons_layout = QHBoxLayout()
        self.add_feed_button = QPushButton("Añadir Feed")
        self.add_feed_button.clicked.connect(self.add_feed)
        self.delete_feed_button = QPushButton("Eliminar Feed")
        self.delete_feed_button.clicked.connect(self.delete_feed)
        self.feed_buttons_layout.addWidget(self.add_feed_button)
        self.feed_buttons_layout.addWidget(self.delete_feed_button)
        self.feed_list_layout.addLayout(self.feed_buttons_layout)

        # Right side: Article list
        self.article_list_widget = QWidget()
        self.article_list_layout = QVBoxLayout(self.article_list_widget)
        self.article_list_label = QLabel("Artículos")
        self.article_list_layout.addWidget(self.article_list_label)
        self.article_list = QListWidget()
        self.article_list.itemDoubleClicked.connect(self.open_article_link)
        self.article_list_layout.addWidget(self.article_list)

        self.splitter.addWidget(self.feed_list_widget)
        self.splitter.addWidget(self.article_list_widget)

        self.load_feeds()

    def load_feeds(self):
        self.feed_list.clear()
        feeds = self.manager.get_all_feeds()
        for feed in feeds:
            item = QListWidgetItem(feed['name'])
            item.setData(Qt.ItemDataRole.UserRole, feed['id'])
            item.setData(Qt.ItemDataRole.UserRole + 1, feed['url'])
            self.feed_list.addItem(item)

    def on_feed_selected(self, item):
        self.current_feed_url = item.data(Qt.ItemDataRole.UserRole + 1)
        self.article_list_label.setText(f"Artículos de: {item.text()}")
        self.load_articles()

    def load_articles(self):
        self.article_list.clear()
        if self.current_feed_url:
            articles = self.manager.fetch_feed_items(self.current_feed_url)
            for article in articles:
                item_widget = RssArticleItemWidget(
                    article['title'],
                    article['published'],
                    article['summary'][:400] + '...' if len(article['summary']) > 400 else article['summary']
                )
                list_item = QListWidgetItem()
                list_item.setSizeHint(item_widget.sizeHint())
                self.article_list.addItem(list_item)
                self.article_list.setItemWidget(list_item, item_widget)
                list_item.setData(Qt.ItemDataRole.UserRole, article['link'])

    def add_feed(self):
        name, ok = QInputDialog.getText(self, 'Añadir Feed RSS', 'Nombre del Feed:')
        if not ok or not name: return

        url, ok = QInputDialog.getText(self, 'Añadir Feed RSS', 'URL del Feed:')
        if ok and url:
            self.manager.add_feed(name, url)
            self.load_feeds()

    def delete_feed(self):
        selected_item = self.feed_list.currentItem()
        if selected_item:
            feed_id = selected_item.data(Qt.ItemDataRole.UserRole)
            reply = QMessageBox.question(self, 'Eliminar Feed', '¿Estás seguro de que quieres eliminar este feed?')
            if reply == QMessageBox.Yes:
                self.manager.delete_feed(feed_id)
                self.load_feeds()
                self.article_list.clear()

    def open_article_link(self, item):
        link = item.data(Qt.ItemDataRole.UserRole)
        if link:
            QDesktopServices.openUrl(QUrl(link))
