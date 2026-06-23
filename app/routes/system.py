import os
import json
from datetime import datetime
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db

router = APIRouter(prefix="/system", tags=["system"])

# Arquivo para armazenar histórico de atualizações
UPDATES_FILE = "update_history.json"

def _load_updates_history() -> list:
    """Carrega o histórico de atualizações do arquivo JSON."""
    if os.path.exists(UPDATES_FILE):
        try:
            with open(UPDATES_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return []
    return []

def _save_updates_history(history: list) -> None:
    """Salva o histórico de atualizações no arquivo JSON."""
    try:
        with open(UPDATES_FILE, 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Erro ao salvar histórico de atualizações: {e}")

@router.get("/update-history")
def get_update_history():
    """Retorna o histórico de atualizações do sistema."""
    history = _load_updates_history()
    # Ordena por data decrescente (mais recentes primeiro)
    history.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
    return {
        "history": history,
        "total": len(history),
    }

@router.post("/restart")
def restart_system():
    """
    Endpoint para reiniciar o sistema.
    Registra a atualização e depois reinicia o servidor.
    """
    # Carrega histórico
    history = _load_updates_history()
    
    # Adiciona nova atualização
    new_update = {
        "version": "v1.0.0",
        "timestamp": datetime.now().isoformat(),
        "description": "Reinicialização do sistema",
    }
    history.insert(0, new_update)  # Adiciona no início (mais recente)
    
    # Salva histórico
    _save_updates_history(history)
    
    return {
        "message": "Sistema será reiniciado",
        "timestamp": new_update["timestamp"],
    }

@router.get("/status")
def system_status():
    """Retorna status do sistema."""
    history = _load_updates_history()
    last_update = history[0] if history else None
    
    return {
        "status": "online",
        "version": "v1.0.0",
        "last_update": last_update,
        "uptime": "online",
    }
