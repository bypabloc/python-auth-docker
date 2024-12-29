from __future__ import annotations

from datetime import datetime
from inspect import currentframe as inspect_currentframe
from json import dumps as json_dumps
from logging import getLogger as logging_getLogger
from os import path as os_path

from coloredlogs import install as coloredlogs_install
from django.conf import settings

__version__ = "1.0.0"

# Configuraciones de colores
GRAY = "\033[90m"
RED = "\033[91m"
RED_BOLD = "\033[1m\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
PURPLE = "\033[95m"
CYAN = "\033[96m"
WHITE = "\033[97m"
END = "\033[0m"
BOLD = "\033[1m"
UNDERLINE = "\033[4m"

LEVEL = {
    "SPAM": GRAY,
    "ERROR": RED,
    "CRITICAL": RED_BOLD,
    "SUCCESS": GREEN,
    "DEBUG": CYAN,
    "WARNING": YELLOW,
    "VERBOSE": BLUE,
    "NOTICE": PURPLE,
    "HEADER": CYAN,
    "INFO": WHITE,
}


class Logger:
    """Logger de proyecto con métodos info, warn, error, critical, debug y block.

    Attributes:
    ----------
    name : str
        Nombre de aplicación o módulo para tracking del log
    local_logger : str
        Instancia de loggin, librería externa

    :Authors:
        - Pablo Contreras

    :Last Modification:
        2024-08-30
    """

    name = None
    local_logger = None
    _is_checking_config = False

    def __init__(
        self,
        name: str = "easy_pay",
        *args: list,
        **kwargs: dict,
    ):
        """Inicializador logger que configura el objeto.

        Parameters
        ----------
        name : str
            Nombre de aplicación o módulo para tracking del log

        :Authors:
            - Pablo Contreras

        :Last Modification:
            - 2024-08-30
        """
        self.name = name
        self.local_logger = logging_getLogger(self.name)
        coloredlogs_install(level="DEBUG", logger=self.local_logger)

    def _log(
        self,
        level: str,
        message: str,
        extra: dict | None = None,
    ) -> None:
        """Método interno para manejar el logging con extra.

        Parameters
        ----------
        level : str
            Nivel de log (info, warn, error, critical, debug)
        message : str
            Mensaje principal del log
        extra : dict, optional
            Información adicional para incluir en el log
        """
        if not extra:
            extra = {}

        log_message = str(message)
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        color = LEVEL.get(level.upper(), WHITE)

        frame = inspect_currentframe().f_back.f_back
        filename = frame.f_code.co_filename
        lineno = frame.f_lineno

        try:
            relative_path = os_path.relpath(filename, settings.BASE_DIR)
        except ValueError:
            relative_path = filename

        file_info = f"{relative_path}#{lineno}"

        environment = settings.ENVIRONMENT

        if environment == "local":
            formatted_message = (
                f"{GREEN}[{current_time}]{END} {BLUE}[{file_info}]{END} "
                f"{color}[{level.upper()}] - {log_message} |{END} |"
            )
            extra_json = json_dumps(extra, indent=2, default=str)
            print(formatted_message, extra_json, flush=True)
        else:
            extra_json = json_dumps(extra, default=str)
            formatted_message = (
                f"|[{current_time}] [{file_info}] [{level.upper()}] - "
                f"{log_message} | {extra_json} |"
            )
            print(formatted_message, flush=True)

    def info(
        self,
        message: str,
        extra: dict | None = None,
    ) -> None:
        """Log con nivel informativo.

        Parameters
        ----------
        message : str
            Mensaje a imprimir

        :Authors:
            - Pablo Contreras

        :Last Modification:
            2024-08-30
        """
        self._log("INFO", message, extra)

    def warning(
        self,
        message: str,
        extra: dict | None = None,
    ) -> None:
        """Log con nivel de advertencia.

        Parameters
        ----------
        message : str
            Mensaje a imprimir

        :Authors:
            - Pablo Contreras

        :Last Modification:
            2024-08-30
        """
        self._log("WARNING", message, extra)

    def error(
        self,
        message: str,
        extra: dict | None = None,
    ) -> None:
        """Log para impresión de errores.

        Parameters
        ----------
        message : str
            Mensaje a imprimir

        :Authors:
            - Pablo Contreras

        :Last Modification:
            2024-08-30
        """
        self._log("ERROR", message, extra)

    def critical(
        self,
        message: str,
        extra: dict | None = None,
    ) -> None:
        """Log para impresiones de errores críticos de sistema.

        Parameters
        ----------
        message : str
            Mensaje a imprimir

        :Authors:
            - Pablo Contreras

        :Last Modification:
            2024-08-30
        """
        self._log("CRITICAL", message, extra)

    def debug(
        self,
        message: str,
        extra: dict | None = None,
    ) -> None:
        """Impresiones simples para depuración.

        Parameters
        ----------
        message : str
            Mensaje a imprimir

        :Authors:
            - Pablo Contreras

        :Last Modification:
            2024-08-30
        """
        if settings.DEBUG or not settings.PRODUCTIVE_ENVIRONMENT:
            self._log("DEBUG", message, extra)


logger = Logger()
