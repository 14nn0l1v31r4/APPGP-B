from datetime import datetime
from zoneinfo import ZoneInfo


LOCAL_TIMEZONE = ZoneInfo("America/Sao_Paulo")
LEGACY_FORMATS = ("%d/%m/%Y %H:%M", "%d/%m/%Y")


def normalizar_data_hora(valor: str | datetime) -> datetime:
    if isinstance(valor, datetime):
        data = valor
    else:
        texto = valor.strip()
        try:
            data = datetime.fromisoformat(texto.replace("Z", "+00:00"))
        except ValueError:
            for formato in LEGACY_FORMATS:
                try:
                    data = datetime.strptime(texto, formato)
                    break
                except ValueError:
                    continue
            else:
                raise ValueError("Formato de data/hora inválido")

    if data.tzinfo is None:
        data = data.replace(tzinfo=LOCAL_TIMEZONE)

    return data
