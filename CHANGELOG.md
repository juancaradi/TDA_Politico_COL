# Changelog

Todos los cambios notables en el proyecto "Sismógrafo Político TDA" serán documentados en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
y este proyecto se adhiere a [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-01-06

### Added
- **Arquitectura**: Estructura modular inicial (`src/`, `data/`, `logs/`).
- **Core**: Archivo de configuración `settings.py` y orquestador `main.py`.
- **Scraping**: Implementación base con `undetected-chromedriver` y rotación de espejos Nitter.
- **Queries**: Diccionario semántico para Colombia (`queries/colombia.py`) y lógica de construcción de queries.
- **Docs**: README.md con instrucciones de instalación y metodología.

### Fixed
- **Dependencias**: Solucionado error crítico `ModuleNotFoundError: No module named 'distutils'` en entornos Python 3.12+ agregando `setuptools`.