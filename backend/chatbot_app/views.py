from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from loguru import logger
import subprocess
import json

logger.add("logs/howdoi.log", rotation="1 MB")  

def index(request):
    return render(request, 'chatbot_app/index.html')

@csrf_exempt
def ask(request):
    if request.method != 'POST':
        logger.warning(f"Invalid request method: {request.method}")
        return JsonResponse({'result': 'Invalid request.'}, status=405)

    try:
        data = json.loads(request.body)
        question = data.get('question', '').strip()
        if not question:
            logger.info("Empty question received.")
            return JsonResponse({'result': 'Question cannot be empty.'}, status=400)

        logger.info(f"Received question: {question}")

        cmd = ['howdoi', '--num', '1', '--color', '0'] + question.split()
        result = subprocess.check_output(cmd, stderr=subprocess.STDOUT, timeout=8)
        answer = result.decode('utf-8').strip()

        if not answer:
            answer = "Sorry, couldn't find help for that topic."
            logger.warning(f"No answer found for: {question}")

        logger.info(f"Answer returned for question: {question}")
        return JsonResponse({'result': answer})

    except subprocess.CalledProcessError as e:
        error_msg = e.output.decode('utf-8', errors='replace')
        logger.error(f"CalledProcessError for question '{question}': {error_msg}")
        return JsonResponse({'result': f'Error: {error_msg}'}, status=500)

    except subprocess.TimeoutExpired:
        logger.error(f"TimeoutExpired for question: {question}")
        return JsonResponse({'result': 'Timeout. Try a shorter query.'}, status=504)

    except Exception as e:
        logger.exception(f"Unexpected error for question: {question}")
        return JsonResponse({'result': f'Unexpected error: {str(e)}'}, status=500)
