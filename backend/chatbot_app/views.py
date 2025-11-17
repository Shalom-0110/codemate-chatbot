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

def safe_generate(model, contents, config, client, retries=3):
    for i in range(retries):
        try:
            return client.models.generate_content(
                model=model,
                contents=contents,
                config=config
            )
        except Exception as e:
            msg = str(e)
            if "503" in msg or "unavailable" in msg.lower():
                time.sleep(1.2 * (i + 1))
                continue
            raise e

    fallback = "gemini-2.0-flash"
    if model != fallback:
        return client.models.generate_content(
            model=fallback,
            contents=contents,
            config=config
        )

    raise Exception("Model unreachable after retries + fallback")


def welcome(request):
    return render(request, "chatbot_app/welcome.html")

@csrf_exempt
def chat(request):
    return render(request, "chatbot_app/chat.html")

@csrf_exempt
def ask(request):
    if request.method != "POST":
        return JsonResponse({"result": "Use POST"}, status=405)
    question = ""
    attachment = None
    try:
        ct = request.META.get("CONTENT_TYPE", "") or ""
        if "multipart/form-data" in ct:
            question = (request.POST.get("question") or "").strip()
            attachment = request.FILES.get("attachment")
        else:
            payload = json.loads(request.body.decode("utf-8") or "{}")
            question = (payload.get("question") or "").strip()
    except Exception:
        return JsonResponse({"result": "Invalid request"}, status=400)

    if not question and not attachment:
        return JsonResponse({"result": "Please enter a question or attach a supported file."}, status=400)

    logger.info("ask(): question=%s attachment=%s", question, getattr(attachment, "name", None))

    # Attachment handling
    extracted_text = None
    if attachment:
        name = attachment.name.lower()
        MAX_BYTES = 5 * 1024 * 1024  # this is the attachment size limit 5MB
        if attachment.size > MAX_BYTES:
            return JsonResponse({"result": "Attachment too large (max 5MB)."}, status=400)

        # PDF
        if name.endswith('.pdf'):
            try:
                from PyPDF2 import PdfReader
                attachment.seek(0)
                reader = PdfReader(attachment)

                pages = []
                page_limit = min(2, len(reader.pages))  # rn considering only 2 min pages cus im using free model, dont ask for more haha
                for i in range(page_limit):
                    try:
                        p = reader.pages[i]
                        pages.append(p.extract_text() or "")
                    except Exception:
                        pages.append("")
                extracted_text = "\n".join(pages).strip()
            except Exception as e:
                logger.exception("PDF extract failed: %s", e)
                extracted_text = None

        elif name.endswith(('.txt', '.md')):
            try:
                attachment.seek(0)
                raw = attachment.read()
                extracted_text = raw.decode('utf-8', errors='ignore')
            except Exception:
                extracted_text = None

        else:
            return JsonResponse({"result": "Unsupported file type. Use PDF or .txt/.md for now."}, status=400)

    system_instruction = (
        "You are an expert Python teacher. Answer the user's programming question in clear Markdown. "
        "Use a short title heading, a concise explanation in bullet points, and include small runnable code examples "
        "in triple-backtick fenced code blocks labeled with the language (e.g. ```python). "
        "Keep the answer focused and readable; avoid excessive prose. If asked for multiple examples, provide up to 2. "
    )

    contents = []
    if extracted_text:
        EXCERPT_CHARS = 3000
        excerpt = extracted_text[:EXCERPT_CHARS]
        contents.append(f"Attachment content (truncated):\n{excerpt}\n--- end of attachment excerpt ---")

    if question:
        contents.append(question)
    else:
        contents.append("Please analyze the attached content and respond.")

    config = types.GenerateContentConfig(
        system_instruction=system_instruction,
        thinking_config=types.ThinkingConfig(thinking_budget=0),
        temperature=0.1,
        max_output_tokens=600
    )

    try:
        start = time.time()
        response = safe_generate(MODEL_NAME, contents, config, client)
        elapsed_ms = int((time.time() - start) * 1000)
    except Exception as e:
        logger.exception("GenAI error: %s", e)
        return JsonResponse({"result": f"Error contacting model: {str(e)}"}, status=502)

    answer_md = getattr(response, "text", None)
    if not answer_md:
        try:
            if hasattr(response, "candidates") and response.candidates:
                cand = response.candidates[0]
                content = getattr(cand, "content", None) or (cand.get("content") if isinstance(cand, dict) else None)
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
