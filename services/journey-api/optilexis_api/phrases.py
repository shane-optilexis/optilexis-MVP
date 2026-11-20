"""Curated demonstration phrases; not a machine-translation system."""
from .models import PhraseRequest, PhraseResponse

# Human review is required prior to customer release; these are demonstration strings.
PHRASES: dict[str, dict[str, str]] = {
    "hotel_checkin": {
        "en": "Hello, I have a reservation. May I check in?",
        "ja": "こんにちは。予約しています。チェックインできますか？",
        "fr": "Bonjour, j'ai une réservation. Puis-je m'enregistrer ?",
        "es": "Hola, tengo una reserva. ¿Puedo registrarme?",
        "de": "Guten Tag, ich habe eine Reservierung. Kann ich einchecken?",
        "zh": "您好，我有预订。请问可以办理入住吗？",
        "th": "สวัสดี ฉันจองห้องพักไว้แล้ว ขอเช็กอินได้ไหม",
    },
    "station_platform": {
        "en": "Which platform goes to my destination?",
        "ja": "目的地へ行く電車は何番ホームですか？",
        "fr": "Quel quai dessert ma destination ?",
        "es": "¿De qué andén sale el tren hacia mi destino?",
        "de": "Von welchem Gleis fährt der Zug zu meinem Ziel?",
        "zh": "去我目的地的列车在哪个站台？",
        "th": "รถไฟไปจุดหมายของฉันออกจากชานชาลาไหน",
    },
    "airport_terminal": {
        "en": "Could you tell me which terminal I need?",
        "ja": "利用するターミナルを教えていただけますか？",
        "fr": "Pouvez-vous me dire de quel terminal j'ai besoin ?",
        "es": "¿Puede decirme qué terminal necesito?",
        "de": "Können Sie mir sagen, welches Terminal ich brauche?",
        "zh": "请问我应该去哪个航站楼？",
        "th": "ช่วยบอกได้ไหมว่าฉันต้องไปอาคารผู้โดยสารไหน",
    },
    "parking_question": {
        "en": "May I park here, and are there any restrictions?",
        "ja": "ここに駐車できますか？制限はありますか？",
        "fr": "Puis-je me garer ici et y a-t-il des restrictions ?",
        "es": "¿Puedo aparcar aquí? ¿Hay alguna restricción?",
        "de": "Darf ich hier parken, und gibt es Einschränkungen?",
        "zh": "请问这里可以停车吗？有什么限制吗？",
        "th": "ฉันจอดรถที่นี่ได้ไหม และมีข้อจำกัดอะไรบ้าง",
    },
}


def phrase_for(request: PhraseRequest) -> PhraseResponse:
    phrases = PHRASES[request.phrase_key]
    return PhraseResponse(source_text=phrases["en"],
                          translated_text=phrases[request.language],
                          language=request.language)
