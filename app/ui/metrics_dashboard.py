from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QProgressBar, QScrollArea, QPushButton, QFrame)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPainter, QColor, QBrush
import datetime

class DailyUsageWidget(QWidget):
    def __init__(self, metrics_manager, parent=None):
        super().__init__(parent)
        self.metrics_manager = metrics_manager
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(10)

        self.title = QLabel("Desglose Diario (Hoy)")
        self.title.setStyleSheet("font-weight: bold; font-size: 14px; color: #f0f0f0;")
        self.layout.addWidget(self.title)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("background-color: #2e2e2e; border: none;")
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.scroll_area.setWidget(self.content_widget)
        self.layout.addWidget(self.scroll_area)

    def refresh(self):
        # Clear existing items
        for i in reversed(range(self.content_layout.count())): 
            self.content_layout.itemAt(i).widget().setParent(None)

        data = self.metrics_manager.get_usage_report()
        if not data:
            lbl = QLabel("No hay actividad registrada hoy.")
            lbl.setStyleSheet("color: #bdc3c7; font-style: italic;")
            self.content_layout.addWidget(lbl)
            return

        total_ms = sum(item['milliseconds'] for item in data)
        
        for item in data:
            name = item['service_name']
            ms = item['milliseconds']
            percentage = int((ms / total_ms) * 100) if total_ms > 0 else 0
            
            # Format time
            seconds = int(ms / 1000)
            m, s = divmod(seconds, 60)
            h, m = divmod(m, 60)
            time_str = f"{h}h {m}m" if h > 0 else f"{m}m"

            # Row Layout
            row = QWidget()
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(0, 0, 0, 0)
            
            lbl_name = QLabel(f"{name} ({time_str})")
            lbl_name.setFixedWidth(150)
            lbl_name.setStyleSheet("color: #f0f0f0;")
            
            progress = QProgressBar()
            progress.setRange(0, 100)
            progress.setValue(percentage)
            progress.setTextVisible(True)
            progress.setFormat(f"{percentage}%")
            progress.setStyleSheet("""
                QProgressBar {
                    border: 1px solid #555;
                    border-radius: 3px;
                    text-align: center;
                    color: white;
                    background-color: #3a3a3a;
                }
                QProgressBar::chunk {
                    background-color: #3498db;
                }
            """)
            
            row_layout.addWidget(lbl_name)
            row_layout.addWidget(progress)
            self.content_layout.addWidget(row)

class WeeklyTrendWidget(QWidget):
    def __init__(self, metrics_manager, parent=None):
        super().__init__(parent)
        self.metrics_manager = metrics_manager
        self.setMinimumHeight(150)
        self.data = {}

    def refresh(self):
        self.data = self.metrics_manager.get_weekly_usage()
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Background
        painter.fillRect(self.rect(), QColor("#2e2e2e"))
        
        if not self.data:
            painter.setPen(QColor("#bdc3c7"))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "No hay datos semanales")
            return

        # Draw Bars
        margin = 20
        width = self.width() - 2 * margin
        height = self.height() - 2 * margin
        
        days = sorted(self.data.keys())
        max_val = max(self.data.values()) if self.data.values() else 1
        
        bar_width = width / len(days) if days else width
        
        painter.setBrush(QBrush(QColor("#2ecc71")))
        painter.setPen(Qt.PenStyle.NoPen)

        for i, day in enumerate(days):
            val = self.data[day]
            bar_height = (val / max_val) * (height - 20) # Leave space for text
            
            x = margin + i * bar_width + 5
            y = margin + height - bar_height - 20
            
            # Draw Bar
            painter.drawRect(int(x), int(y), int(bar_width - 10), int(bar_height))
            
            # Draw Day Label
            date_obj = datetime.date.fromisoformat(day)
            day_label = date_obj.strftime("%a") # Mon, Tue...
            
            painter.setPen(QColor("#f0f0f0"))
            painter.drawText(int(x), int(margin + height - 5), int(bar_width - 10), 20, 
                             Qt.AlignmentFlag.AlignCenter, day_label)
            painter.setPen(Qt.PenStyle.NoPen) # Reset pen for next bar

class MetricsDashboard(QWidget):
    def __init__(self, metrics_manager, parent=None):
        super().__init__(parent)
        self.metrics_manager = metrics_manager
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(20, 20, 20, 20)
        self.layout.setSpacing(20)

        # Header
        header_layout = QHBoxLayout()
        title = QLabel("Tablero de Métricas")
        title.setStyleSheet("font-weight: bold; font-size: 20px; color: #f0f0f0;")
        
        btn_refresh = QPushButton("Actualizar")
        btn_refresh.clicked.connect(self.refresh_all)
        btn_refresh.setStyleSheet("""
            QPushButton {
                background-color: #555; color: #f0f0f0; border: 1px solid #666; padding: 5px 15px; border-radius: 4px;
            }
            QPushButton:hover { background-color: #666; }
        """)

        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(btn_refresh)
        self.layout.addLayout(header_layout)

        # Weekly Trend
        self.weekly_widget = WeeklyTrendWidget(self.metrics_manager)
        self.layout.addWidget(QLabel("Tendencia Semanal", styleSheet="font-weight: bold; color: #f0f0f0;"))
        self.layout.addWidget(self.weekly_widget)

        # Daily Usage
        self.daily_widget = DailyUsageWidget(self.metrics_manager)
        self.layout.addWidget(self.daily_widget)

        # Initial Refresh
        self.refresh_all()

    def refresh_all(self):
        self.weekly_widget.refresh()
        self.daily_widget.refresh()
