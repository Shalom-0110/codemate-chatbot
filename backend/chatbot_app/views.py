import os, json, time
from pathlib import Path
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
from dotenv import load_dotenv
from loguru import logger
from google import genai
from google.genai import types

load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY") or os.getenv("GOOGLE_GENERATIVE_AI_API_KEY")
MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

LOG_DIR = Path(__file__).resolve().parent.parent / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
logger.remove()
logger.add(str(LOG_DIR / "chatbot.log"), rotation="5 MB", retention="7 days")

client = genai.Client(api_key=API_KEY) if API_KEY else genai.Client()


def welcome(request):
    return render(request, "chatbot_app/welcome.html")

@csrf_exempt
def index(request):
    return render(request, "chatbot_app/index.html")

@csrf_exempt
def ask(request):
    if request.method != "POST":
        return JsonResponse({"result": "Use POST"}, status=405)

    try:
        payload = json.loads(request.body.decode("utf-8") or "{}")
    except Exception:
        return JsonResponse({"result": "Invalid JSON"}, status=400)

    question = (payload.get("question") or "").strip()
    if not question:
        return JsonResponse({"result": "Please enter a question."}, status=400)

    logger.info("ask(): question=%s", question)

    system_instruction = (
        "You are an expert Python teacher. Answer the user's programming question in clear Markdown. "
        "Use a short title heading, a concise explanation in bullet points, and include small runnable code examples "
        "in triple-backtick fenced code blocks labeled with the language (e.g. ```python). "
        "Keep the answer focused and readable; avoid excessive prose. If asked for multiple examples, provide up to 2. "
    )

    config = types.GenerateContentConfig(
        system_instruction=system_instruction,
        thinking_config=types.ThinkingConfig(thinking_budget=0), 
        temperature=0.1,
        max_output_tokens=600
    )

    try:
        start = time.time()
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=[question],
            config=config
        )
        elapsed_ms = int((time.time() - start) * 1000)
    except Exception as e:
        logger.exception("GenAI error: %s", e)
        return JsonResponse({"result": f"Error contacting model: {str(e)}"}, status=502)

    answer_md = getattr(response, "text", None)
    if not answer_md:
        try:
            if hasattr(response, "candidates"):
                cand = response.candidates[0]
                content = getattr(cand, "content", None) or cand.get("content", None)
                if content:
                    parts = content.get("parts") if isinstance(content, dict) else None
                    if parts:
                        answer_md = "\n".join(p.get("text", "") if isinstance(p, dict) else str(p) for p in parts)
        except Exception:
            answer_md = str(response)

    if not answer_md:
        answer_md = str(response)

    logger.info("ask(): generated ({} ms) chars=%d", elapsed_ms, len(answer_md))
    return JsonResponse({"result": answer_md, "source": "google-genai", "meta": {"time_ms": elapsed_ms}})
