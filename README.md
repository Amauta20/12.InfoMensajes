# InfoMensajero

Un hub de escritorio para unificar mensajería y productividad, construido con Python y PySide6. Minimalista, seguro, ligero y 100% open source.

## ✨ Principios

*   **Privacidad Primero**: Todo es local. Nada se sube a la nube sin tu consentimiento explícito.
*   **Minimalista y Ligero**: Interfaz limpia y un consumo de recursos moderado.
*   **Seguro**: Cifrado local fuerte para tus credenciales y datos sensibles.
*   **Open Source**: Código abierto bajo licencia MIT.

## 🚀 Características (MVP)

*   **Servicios Embebidos**: Integra WhatsApp, Telegram, Slack, Gmail, etc., en pestañas con perfiles de sesión aislados.
*   **Sesión Persistente**: Inicia sesión una vez y la aplicación recordará tus sesiones.
*   **Herramientas de Productividad**:
    *   **Notas Rápidas**: Captura ideas al instante.
    *   **Kanban Mejorado**: Organiza tareas en columnas (Por Hacer, En Curso, Hecho) con una interfaz de usuario mejorada.
    *   **Diagrama de Gantt Dinámico**: Visualiza tus tareas Kanban en un cronograma interactivo y profesional, con opciones de exportación a HTML.
*   **Búsqueda Global**: Busca en todas tus notas y tarjetas kanban localmente con un índice FTS5.
*   **Bóveda Segura**: Almacena API keys y otras credenciales de forma segura usando criptografía estándar (scrypt + AES-GCM).

## 🛠️ Stack Tecnológico

*   **Lenguaje**: Python 3.10+
*   **Framework UI**: PySide6 (Qt for Python)
*   **Navegador Embebido**: QtWebEngine
*   **Base de Datos**: SQLite con FTS5 para búsqueda de texto completo.
*   **Criptografía**: `cryptography` para la bóveda de secretos.
*   **Empaquetado**: PyInstaller

## 🏁 Cómo Empezar (Placeholder)

### Prerrequisitos

Asegúrate de tener Python 3.10 o superior instalado.

### Instalación

1.  Clona el repositorio:
    ```bash
    git clone https://github.com/tu-usuario/InfoMensajero.git
    cd InfoMensajero
    ```

2.  Crea un entorno virtual e instala las dependencias:
    ```bash
    # Windows
    python -m venv venv
    .\venv\Scripts\activate
    
    # macOS/Linux
    python3 -m venv venv
    source venv/bin/activate

    pip install -r requirements.txt
    ```

### Ejecución

```bash
python main.py
```

## 🗺️ Roadmap

*   **Fase 1 (MVP)**: Servicios embebidos, notas, kanban, búsqueda local y bóveda de seguridad.
*   **Fase 2**: Integración de IA (resumir, traducir), atajos avanzados y notificaciones silenciosas.
*   **Fase 3**: Conectores OAuth para indexación de mensajes (Gmail, Outlook, Slack).
*   **Fase 4**: Multi-ventana, vistas divididas y reglas de concentración.

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Por favor, sigue los estándares de código del proyecto (formato con `black`, linting con `ruff`) y abre un Pull Request.

## 📄 Licencia

Este proyecto está bajo la **Licencia MIT**.