# main.py - FastAPI Backend
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI
import os
from typing import Optional

# Charger le fichier .env SEULEMENT en développement local
try:
    from dotenv import load_dotenv
    load_dotenv()  # Fonctionne en local, ignoré en production
except ImportError:
    pass  # dotenv pas nécessaire en production

# Configuration OpenAI - fonctionne partout
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY environment variable is required")

client = OpenAI(api_key=api_key)

app = FastAPI(title="AI Translator API", version="1.0.0")

# CORS middleware pour permettre les requêtes depuis Streamlit Cloud
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En production, spécifiez les domaines autorisés
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Modèles de données
class TranslationRequest(BaseModel):
    text: str
    source_language: str
    target_language: str
    model: Optional[str] = "gpt-3.5-turbo"

class TranslationResponse(BaseModel):
    original_text: str
    translated_text: str
    source_language: str
    target_language: str

# Langues supportées
SUPPORTED_LANGUAGES = {
    "fr": "French",
    "en": "English",
    "es": "Spanish",
    "de": "German",
    "it": "Italian",
    "pt": "Portuguese",
    "ru": "Russian",
    "ja": "Japanese",
    "ko": "Korean",
    "zh": "Chinese",
    "ar": "Arabic",
    "hi": "Hindi"
}

@app.get("/")
async def root():
    return {"message": "AI Translator API is running!", "status": "healthy"}

@app.get("/languages")
async def get_supported_languages():
    """Retourne la liste des langues supportées"""
    return {"languages": SUPPORTED_LANGUAGES}

@app.post("/translate", response_model=TranslationResponse)
async def translate_text(request: TranslationRequest):
    """Traduit un texte d'une langue source vers une langue cible"""
    
    try:
        # Vérifier la clé API
        if not api_key:
            raise HTTPException(status_code=500, detail="OpenAI API key not configured")
        
        # Validation des langues
        if request.source_language not in SUPPORTED_LANGUAGES:
            raise HTTPException(status_code=400, detail=f"Source language '{request.source_language}' not supported")
        
        if request.target_language not in SUPPORTED_LANGUAGES:
            raise HTTPException(status_code=400, detail=f"Target language '{request.target_language}' not supported")
        
        # Validation du texte
        if not request.text.strip():
            raise HTTPException(status_code=400, detail="Text cannot be empty")
        
        if len(request.text) > 5000:
            raise HTTPException(status_code=400, detail="Text too long (max 5000 characters)")
        
        # Prompt pour OpenAI
        source_lang = SUPPORTED_LANGUAGES[request.source_language]
        target_lang = SUPPORTED_LANGUAGES[request.target_language]
        
        prompt = f"""
        Translate the following text from {source_lang} to {target_lang}.
        Provide only the translation without any additional explanation or formatting.
        
        Text to translate: {request.text}
        """
        
        # Appel à OpenAI
        response = client.chat.completions.create(
            model=request.model,
            messages=[
                {"role": "system", "content": "You are a professional translator. Provide accurate and natural translations."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=1000
        )
        
        translated_text = response.choices[0].message.content.strip()
        
        return TranslationResponse(
            original_text=request.text,
            translated_text=translated_text,
            source_language=request.source_language,
            target_language=request.target_language
        )
        
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"Translation failed: {str(e)}")

@app.get("/health")
async def health_check():
    """Point de contrôle de santé de l'API"""
    return {"status": "healthy", "service": "AI Translator API"}

# Point d'entrée pour démarrer le serveur - adapté pour Render
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)