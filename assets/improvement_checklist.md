# Mejora y Checklist de Desarrollo – InfoMensajes Power

## 📋 Checklist de Mejoras (orden de prioridad)

| ✅ | Área | Mejora propuesta | Acción concreta | Estado |
|---|------|------------------|----------------|--------|
| 1 | **Configuración Qt** | Centralizar variables de entorno y flags de QtWebEngine | - Función `setup_qt_environment()` en `main.py` (ya implementada).<br>- Documentar uso en README. | ✅ Hecho |
| 2 | **Actualización de scripts** | Ejecutar `update_service_scripts` en hilo de fondo | - Importar `threading` y lanzar `Thread` (ya implementado).<br>- Añadir logs INFO. | ✅ Hecho |
| 3 | **Base de datos** | Mejorar concurrencia y robustez | - Activar `PRAGMA journal_mode=WAL` y `foreign_keys=ON` en `database.py`.<br>- Cachear conexión en `DIContainer`. | ✅ Hecho |
| 4 | **Recursos estáticos** | Empaquetar HTML/CSS/Imágenes con `QResource` | - Crear archivo `.qrc` y compilar con `pyrcc6`.<br>- Modificar `HelpWidget` para cargar recurso interno. | ⬜ Pendiente |
| 5 | **Temas y estilos** | Cambiar tema dinámicamente (dark / light) | - Mover hoja de estilos a `assets/styles.qss`.<br>- Añadir menú “Tema” en Configuración. | ⬜ Pendiente |
| 6 | **Modularidad UI** | Widgets independientes y registro lazy‑loading | - Crear paquete `app/ui/tools/` con widgets por herramienta.<br>- Registrar en `DIContainer`. | ⬜ Pendiente |
| 7 | **Manejo de errores** | Unificar gestión de excepciones y logging | - Clase `AppErrorHandler` con diálogos y `RotatingFileHandler`.
- Uso de `logging` en todo el proyecto. | ⬜ Pendiente |
| 8 | **Rendimiento QtWebEngine** | Desactivar WebGL y limitar caché | - Flags `--disable-webgl` y `--disk-cache-size=0` en `setup_qt_environment()`. | ⬜ Pendiente |
| 9 | **Testing y CI** | Pruebas unitarias y pipeline GitHub Actions | - Tests para `DIContainer`, `ServiceManager`, `HelpWidget`.
- Workflow que ejecuta `pytest` y verifica arranque sin errores GPU. | ⬜ Pendiente |
|10| **Documentación automática** | Generar `help_manual.html` a partir de docstrings | - Usar **Sphinx** o **MkDocs** con tema oscuro.
- Script `make docs` para generar manual. | ⬜ Pendiente |
|11| **Seguridad Bóveda** | Cambio de contraseña maestra y cifrado fuerte | - UI para cambiar clave.
- Usar `cryptography` con `AES‑GCM`. | ⬜ Pendiente |
|12| **Optimización IA** | Cachear respuestas y timeout configurable | - Implementar `LRUCache` en `AIManager`.
- Añadir timeout en llamadas al modelo local. | ⬜ Pendiente |

## 📅 Cronograma Tentativo (sprints de 1 semana)
| Semana | Tareas principales |
|--------|-------------------|
| 1 | Consolidar configuración Qt y actualización en hilo (ítems 1‑2). |
| 2 | Mejoras en DB y recursos estáticos (ítems 3‑4). |
| 3 | Temas dinámicos y modularidad UI (ítems 5‑6). |
| 4 | Manejo de errores y rendimiento WebEngine (ítems 7‑8). |
| 5 | Tests unitarios y CI (ítem 9). |
| 6 | Generación automática de manual (ítem 10). |
| 7 | Refuerzo de seguridad en la bóveda (ítem 11). |
| 8 | Optimización del motor IA (ítem 12). |
| 9‑10 | Pulido final, QA y corrección de bugs. |

## ✅ Métricas de Éxito
- Tiempo de arranque < 3 s.
- Uso de CPU al abrir “Ayuda” < 15 %.
- Fallos de GPU en logs = 0.
- Cobertura de pruebas ≥ 80 %.
- Tiempo medio de respuesta IA ≤ 2 s.
- Satisfacción usuario ≥ 4.5/5.

---
*Este checklist está pensado para ser actualizado a medida que se completen los ítems. Cada fila puede marcarse con ✅ (hecho) o ⬜ (pendiente).*
