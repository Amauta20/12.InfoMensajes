# InfoMensajero

Un hub de escritorio para unificar mensajería y productividad, construido con Python y PySide6. Minimalista, seguro, ligero y 100% open source.

## 📖 Tabla de Contenidos

- [✨ Principios](#-principios)
- [🤔 ¿Por qué InfoMensajero?](#-por-qué-infomensajero)
- [🚀 Características](#-características)
- [🛠️ Stack Tecnológico](#️-stack-tecnológico)
- [🏁 Cómo Empezar](#-cómo-empezar)
  - [Prerrequisitos](#prerrequisitos)
  - [Instalación](#instalación)
  - [Ejecución](#ejecución)
- [⬇️ Descarga](#descarga)
- [💡 Cómo Usar](#-cómo-usar)
- [🗺️ Roadmap](#️-roadmap)
- [🤝 Contribuciones](#-contribuciones)
- [📄 Licencia](#-licencia)
- [📞 Contacto](#-contacto)

## ✨ Principios

*   **Privacidad Primero**: Todo es local. Nada se sube a la nube sin tu consentimiento explícito.
*   **Minimalista y Ligero**: Interfaz limpia y un consumo de recursos moderado.
*   **Seguro**: Cifrado local fuerte para tus credenciales y datos sensibles.
*   **Open Source**: Código abierto bajo licencia MIT.

## 🤔 ¿Por qué InfoMensajero?

En la era digital, la información y la comunicación están fragmentadas en múltiples plataformas. InfoMensajero nace de la necesidad de unificar estas experiencias en un solo lugar, ofreciendo un entorno privado, seguro y eficiente. Olvídate de alternar entre docenas de pestañas y aplicaciones; centraliza tu vida digital y recupera el control de tu productividad.

## 🚀 Características

*   **Servicios Embebidos**: Integra WhatsApp, Telegram, Slack, Gmail, etc., en pestañas con perfiles de sesión aislados.
*   **Sesión Persistente**: Inicia sesión una vez y la aplicación recordará tus sesiones.
*   **Herramientas de Productividad**
    *   **Notas Rápidas**: Captura ideas al instante.
    *   **Kanban Mejorado**: Organiza tareas en columnas (Por Hacer, En Curso, Hecho) con una interfaz de usuario mejorada.
    *   **Diagrama de Gantt Dinámico**: Visualiza tus tareas Kanban en un cronograma interactivo y profesional, con opciones de exportación a HTML.
    *   **Listas de Verificación (Checklist)**: Gestiona tus tareas pendientes con facilidad.
    *   **Recordatorios**: Establece recordatorios para no olvidar nada importante.
    *   **Lector RSS**: Mantente al día con tus fuentes de noticias favoritas.
    *   **Pomodoro**: Herramienta para mejorar la concentración y la productividad.
*   **Búsqueda Global**: Busca en todas tus notas y tarjetas kanban localmente con un índice FTS5.
*   **Bóveda Segura**: Almacena API keys y otras credenciales de forma segura usando criptografía estándar (scrypt + AES-GCM).


## 🛠️ Stack Tecnológico

*   **Lenguaje**: Python 3.10+
*   **Framework UI**: PySide6 (Qt for Python)
*   **Navegador Embebido**: QtWebEngine
*   **Base de Datos**: SQLite con FTS5 para búsqueda de texto completo.
*   **Criptografía**: `cryptography` para la bóveda de secretos.
*   **Empaquetado**: PyInstaller

## 🏁 Cómo Empezar

Sigue estos sencillos pasos para poner en marcha InfoMensajero en tu sistema:

### Prerrequisitos

Asegúrate de tener Python 3.10 o superior instalado en tu sistema. Puedes descargarlo desde [python.org](https://www.python.org/downloads/).

### Instalación

1.  **Clona el repositorio** a tu máquina local:
    ```bash
    git clone https://github.com/tu-usuario/InfoMensajero.git
    cd InfoMensajero
    ```

2.  **Crea y activa un entorno virtual** (recomendado) e instala las dependencias necesarias:
    ```bash
    # Para Windows
    python -m venv venv
    .\venv\Scripts\activate
    
    # Para macOS/Linux
    python3 -m venv venv
    source venv/bin/activate

    pip install -r requirements.txt
    ```

### Ejecución

Una vez instalado, puedes iniciar la aplicación:

```bash
python main.py
```

## ⬇️ Descarga

Puedes descargar el instalador para Windows desde el siguiente enlace:

https://cibertec.org/Descarga/InfoMensajero.exe

## 💡 Cómo Usar

Una vez iniciada la aplicación, verás una barra lateral a la izquierda. Desde allí podrás:
*   **Añadir y gestionar servicios web**: Haz clic en "Añadir Servicio" para integrar tus aplicaciones de mensajería o correo favoritas.
*   **Acceder a herramientas de productividad**: Navega entre Notas, Kanban, Gantt, Checklist, Recordatorios, Lector RSS y Bóveda.
*   **Realizar búsquedas globales**: Utiliza la barra de búsqueda superior para encontrar información en tus notas y tarjetas Kanban.

## 🗺️ Roadmap

Nuestro camino hacia una productividad sin fisuras:

*   **Fase 1 (MVP)**: Servicios embebidos, notas, kanban, búsqueda local y bóveda de seguridad.
*   **Fase 2 (Completada)**: Integración de IA (resumir, traducir), atajos avanzados y notificaciones silenciosas. **(¡Novedad! Indicador visual de mensajes no leídos para servicios web clave)**
*   **Fase 3**: Conectores OAuth para indexación de mensajes (Gmail, Outlook, Slack).
*   **Fase 4**: Multi-ventana, vistas divididas y reglas de concentración.

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Por favor, sigue los estándares de código del proyecto (formato con `black`, linting con `ruff`) y abre un Pull Request.

## 📄 Licencia

Este proyecto está bajo la **Licencia MIT**. Consulta el archivo `LICENSE` para más detalles.

## 📞 Contacto

Para preguntas o soporte, por favor abre un issue en el repositorio de GitHub.

---

¡Gracias por usar InfoMensajero! Esperamos que te ayude a simplificar tu vida digital y a potenciar tu productividad.
