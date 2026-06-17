# 🛡️ Seguridad

## ⚠️ NUNCA subir al repo:

| Archivo | Por qué |
|---|---|
| `kaggle.json` | Credenciales de Kaggle. Quien lo tenga puede acceder a tu cuenta |
| `~/.ssh/id_*` | Claves SSH privadas. Acceso a tus servers |
| `vast_ai_key*` | API key de Vast.ai. Acceso a tus instances y billing |
| `.env` con secretos | Variables de entorno con passwords/tokens |
| `*.pem`, `*.key` | Cualquier clave privada o certificado |

## 🔑 Si expusiste algo en el chat

**Rotar inmediatamente** desde el panel correspondiente:

- **Kaggle token:** https://www.kaggle.com/settings → API → "Create New Token" / "Revoke"
- **Vast.ai:** https://cloud.vast.ai/account/ → API Keys
- **GitHub PAT:** https://github.com/settings/tokens

## 📋 Reglas del equipo

1. **Antes de hacer `git add .`**, revisá qué se va a subir
2. **Si ves un token expuesto en un PR**, avisá inmediatamente
3. **No commitees archivos de其他人** sin su permiso
4. **Usá `.gitignore`** (ya está configurado para las cosas comunes)
5. **Si un secret llega al repo**, rotarlo y limpiar el history:
   ```bash
   # NO recomendado, mejor borrar el repo y empezar de nuevo
   # porque git history queda en GitHub
   ```

## 🔒 Para Vast.ai

Cuando generes una SSH key para la instance:
- **NUNCA** subas la privada (`id_ed25519` sin `.pub`)
- Solo subís la pública (`id_ed25519.pub`)
- Generá una key **específica** para este proyecto, no uses tu key principal

```bash
# Generar key específica para el proyecto
ssh-keygen -t ed25519 -N "" -f ~/.ssh/pokemon_tcg_arena
# Subís a Vast.ai: pokemon_tcg_arena.pub
# Queda en tu máquina: pokemon_tcg_arena (privada, NO subir)
```

## 📞 Contacto de seguridad

Si encontrás un problema de seguridad en el repo:
- Avisá a Zoni por Discord (DM)
- NO abras un issue público
