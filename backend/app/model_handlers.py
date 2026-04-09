import os
import json
import time
import requests
import streamlit as st
from openai import AzureOpenAI
# from cerebras.cloud.sdk import Cerebras  # Comentado porque no está instalado ni se usa
import openai
import boto3
from dotenv import load_dotenv

# Cargar variables de entorno desde el archivo .env
load_dotenv()

# Configuración de variables de entorno
CEREBRAS_API_KEY = os.getenv("CEREBRAS_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
DEEPSEEK_AZURE_ENDPOINT = os.getenv("DEEPSEEK_AZURE_ENDPOINT")
DEEPSEEK_AZURE_API_KEY = os.getenv("DEEPSEEK_AZURE_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
O3MINI_ENDPOINT = os.getenv("O3MINI_ENDPOINT")
O3MINI_API_KEY = os.getenv("O3MINI_API_KEY")
GPT4O_NEW_ENDPOINT = os.getenv("GPT4O_NEW_ENDPOINT")
GPT4O_NEW_API_KEY = os.getenv("GPT4O_NEW_API_KEY")
PHI4_AZURE_ENDPOINT = os.getenv("PHI4_AZURE_ENDPOINT")
PHI4_AZURE_API_KEY = os.getenv("PHI4_AZURE_API_KEY")
BEDROCK_REGION = os.getenv("BEDROCK_REGION")
BEDROCK_CLAUDE_MODEL_ID = os.getenv("BEDROCK_CLAUDE_MODEL_ID")
BEDROCK_NOVA_PRO_MODEL_ID = os.getenv("BEDROCK_NOVA_PRO_MODEL_ID")

# Definición de modelos estáticos para otros proveedores
CEREBRAS_MODEL = "llama3.3-70b"
GROQ_MODEL = "qwen-qwq-32b"
DEEPSEEK_MODEL = "DeepSeek-R1-0528"
PHI4_MODEL = os.getenv("PHI4_MODEL", "Phi-4")
GOOGLE_MODEL_2_0 = "gemini-2.0-flash-thinking-exp-01-21"  # Gemini 2.0
GOOGLE_MODEL_2_5 = "gemini-2.5-pro-exp-03-25"  # Gemini 2.5


def _build_azure_openai_client(api_key, endpoint, api_version):
    """Construye un cliente AzureOpenAI."""
    return AzureOpenAI(
        api_key=api_key,
        azure_endpoint=endpoint,
        api_version=api_version,
    )


def _init_groq():
    client = openai.OpenAI(
        base_url="https://api.groq.com/openai/v1",
        api_key=GROQ_API_KEY,
    )
    return client, GROQ_MODEL, "https://api.groq.com/openai/v1"


def _init_deepseek():
    endpoint = (
        "https://fgnfoundrylabo3874907599.services.ai.azure.com"
        "/models/chat/completions?api-version=2024-05-01-preview"
    )
    client = _build_azure_openai_client(
        api_key=DEEPSEEK_AZURE_API_KEY,
        endpoint=endpoint,
        api_version="2024-05-01-preview",
    )
    return client, DEEPSEEK_MODEL, endpoint


def _init_google(model):
    base_url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{model}:generateContent"
    )
    if not GOOGLE_API_KEY:
        raise ValueError("GOOGLE_API_KEY no está configurada en el archivo .env")
    return None, model, base_url


def _init_bedrock(model_env_var, env_label):
    client = boto3.client("bedrock-runtime", region_name=BEDROCK_REGION)
    model_id = os.getenv(model_env_var)
    if not model_id:
        raise ValueError(f"{env_label} no está definido en el archivo .env")
    return client, model_id, None


def _init_o3_mini():
    client = _build_azure_openai_client(
        api_key=O3MINI_API_KEY,
        endpoint=O3MINI_ENDPOINT,
        api_version="2025-01-01-preview",
    )
    return client, "o3-mini", O3MINI_ENDPOINT


def _init_o4_mini():
    endpoint = os.getenv("O4MINI_ENDPOINT")
    client = _build_azure_openai_client(
        api_key=os.getenv("O4MINI_API_KEY"),
        endpoint=endpoint,
        api_version="2025-01-01-preview",
    )
    return client, "o4-minirag", endpoint


def _init_gpt_4o_new():
    client = _build_azure_openai_client(
        api_key=GPT4O_NEW_API_KEY,
        endpoint=GPT4O_NEW_ENDPOINT,
        api_version="2025-01-01-preview",
    )
    return client, "gpt-4o", GPT4O_NEW_ENDPOINT


def _init_phi4():
    base_url = (
        f"{PHI4_AZURE_ENDPOINT}"
        "models/chat/completions?api-version=2024-05-01-preview"
    )
    return None, PHI4_MODEL, base_url


def _init_gpt_41():
    endpoint = os.getenv("GPT41_ENDPOINT")
    client = _build_azure_openai_client(
        api_key=os.getenv("GPT41_API_KEY"),
        endpoint=endpoint,
        api_version="2025-01-01-preview",
    )
    return client, "gpt-4.1", endpoint


def _init_gpt_41_mini():
    endpoint = os.getenv("GPT41MINI_ENDPOINT")
    api_version = os.getenv("GPT41MINI_API_VERSION", "2025-01-01-preview")
    model = os.getenv("GPT41MINI_MODEL_NAME", "gpt-4.1-mini")

    client = _build_azure_openai_client(
        api_key=os.getenv("GPT41MINI_API_KEY"),
        endpoint=endpoint,
        api_version=api_version,
    )
    return client, model, endpoint


def _init_cerebras():
    raise NotImplementedError("Cerebras no está disponible en este entorno.")


PROVIDER_INITIALIZERS = {
    "Cerebras (llama3.3-70b)": _init_cerebras,
    "Groq (qwen-qwq-32b)": _init_groq,
    "DeepSeek (DeepSeek-R1)": _init_deepseek,
    "Azure OpenAI (o3-mini)": _init_o3_mini,
    "Azure OpenAI (o4-mini)": _init_o4_mini,
    "Google (Gemini-2.0-Flash)": lambda: _init_google(GOOGLE_MODEL_2_0),
    "Google (Gemini-2.5-Pro)": lambda: _init_google(GOOGLE_MODEL_2_5),
    "GPT-4o (New)": _init_gpt_4o_new,
    "Bedrock (Claude 3.7 Sonnet)": lambda: _init_bedrock(
        "BEDROCK_CLAUDE_MODEL_ID",
        "BEDROCK_CLAUDE_MODEL_ID",
    ),
    "Bedrock (Nova Pro)": lambda: _init_bedrock(
        "BEDROCK_NOVA_PRO_MODEL_ID",
        "BEDROCK_NOVA_PRO_MODEL_ID",
    ),
    "Azure OpenAI (Phi 4)": _init_phi4,
    "GPT-4.1": _init_gpt_41,
    "Azure OpenAI (gpt-4.1-mini)": _init_gpt_41_mini,
}


def initialize_client(provider):
    """Inicializa el cliente y modelo según el proveedor."""
    try:
        initializer = PROVIDER_INITIALIZERS.get(provider)
        if initializer is None:
            raise ValueError(f"Proveedor no soportado: {provider}")
        return initializer()
    except Exception as e:
        st.error(f"Error al inicializar {provider}: {str(e)}")
        return None, None, None


def _invoke_google(base_url, system_prompt, user_prompt, max_tokens):
    """Invoca los modelos de Google Gemini via REST."""
    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": GOOGLE_API_KEY,
    }
    data = {
        "contents": [{"parts": [{"text": system_prompt + "\n\n" + user_prompt}]}],
        "generationConfig": {
            "temperature": 0.01,
            "maxOutputTokens": max_tokens,
        },
    }

    response = requests.post(base_url, headers=headers, json=data)

    if response.status_code == 200:
        try:
            return response.json()["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError) as e:
            error_msg = f"Error al procesar la respuesta de Gemini: {str(e)}"
            st.error(error_msg)
            raise Exception(error_msg) from e

    if response.status_code == 429:
        st.error("Error: Límite de solicitudes excedido para Gemini API.")
        raise Exception("Rate limit exceeded")

    if response.status_code == 403:
        st.error("Error: Permiso denegado. Verifica tu GOOGLE_API_KEY.")
        raise Exception("Permission denied")

    error_msg = f"Error en Gemini API: {response.status_code} - {response.text}"
    st.error(error_msg)
    raise Exception(error_msg)


def _invoke_bedrock_claude(client, model, system_prompt, user_prompt, max_tokens):
    """Invoca Claude en AWS Bedrock."""
    native_request = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": max_tokens,
        "temperature": 0.01,
        "system": system_prompt,
        "messages": [{"role": "user", "content": user_prompt}],
    }
    response = client.invoke_model(modelId=model, body=json.dumps(native_request))
    model_response = json.loads(response["body"].read())
    return model_response["content"][0]["text"]


def _invoke_bedrock_nova(client, model, system_prompt, user_prompt):
    """Invoca Nova Pro en AWS Bedrock."""
    messages = [
        {
            "role": "user",
            "content": [{"text": system_prompt + "\n\n" + user_prompt}],
        }
    ]
    request_body = {
        "messages": messages,
        "inferenceConfig": {
            "max_new_tokens": 4096,
            "temperature": 0.01,
            "top_p": 0.99,
            "top_k": 20,
        },
    }
    response = client.invoke_model(modelId=model, body=json.dumps(request_body))
    model_response = json.loads(response["body"].read())
    return model_response["output"]["message"]["content"][0]["text"]


def _invoke_phi4(base_url, model, system_prompt, user_prompt, max_tokens):
    """Invoca Phi-4 en Azure via REST."""
    headers = {
        "Content-Type": "application/json",
        "api-key": PHI4_AZURE_API_KEY,
        "x-ms-model-mesh-model-name": model,
    }
    data = {
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "max_tokens": max_tokens,
        "temperature": 0.01,
    }
    response = requests.post(base_url, headers=headers, json=data)
    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]
    raise Exception(f"Error en Phi-4 API: {response.status_code} - {response.text}")


def _invoke_openai_stream(client, params):
    """Invoca un modelo OpenAI-compatible en modo streaming (no synthesis)."""
    full_response = ""
    completion = client.chat.completions.create(**params)
    for partial in completion:
        if not partial.choices or not partial.choices[0].delta.content:
            continue
        chunk_message = partial.choices[0].delta.content
        full_response += chunk_message
        time.sleep(0.05)
    return full_response


def _invoke_openai_synthesis_stream(client, params):
    """Retorna un generador de streaming para síntesis final."""
    print("[invoke_model] Retornando GENERADOR de streaming (synthesis_stream=True)")

    def streaming_text():
        full_text = ""
        for partial in client.chat.completions.create(**params):
            if not partial.choices or not partial.choices[0].delta.content:
                continue
            chunk_message = partial.choices[0].delta.content
            full_text += chunk_message
            yield chunk_message

        # Al final del stream, forzar salto de línea para asegurar cierre de sección
        if not full_text.endswith("\n"):  # Evita doble salto
            yield "\n"

    return streaming_text()


def invoke_model(
    client,
    model,
    base_url,
    system_prompt,
    user_prompt,
    provider,
    max_tokens=1500,
    stream=True,
    synthesis_stream=False,
):
    """Invoca el modelo con los parámetros dados y soporta streaming solo para la síntesis final."""
    full_response = ""

    try:
        if provider in ["Google (Gemini-2.0-Flash)", "Google (Gemini-2.5-Pro)"]:
            return _invoke_google(base_url, system_prompt, user_prompt, max_tokens)

        if provider == "Bedrock (Claude 3.7 Sonnet)":
            return _invoke_bedrock_claude(
                client,
                model,
                system_prompt,
                user_prompt,
                max_tokens,
            )

        if provider == "Bedrock (Nova Pro)":
            return _invoke_bedrock_nova(client, model, system_prompt, user_prompt)

        if provider == "Azure OpenAI (Phi 4)":
            return _invoke_phi4(
                base_url,
                model,
                system_prompt,
                user_prompt,
                max_tokens,
            )

        params = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }

        if (
            "Azure OpenAI" in provider
            or "GPT-4o" in provider
            or "DeepSeek" in provider
        ):
            params["max_completion_tokens"] = max_tokens
            params["stream"] = stream
        else:
            params["max_tokens"] = max_tokens
            params["stream"] = stream
            params["temperature"] = 0.01

        if synthesis_stream and params["stream"]:
            return _invoke_openai_synthesis_stream(client, params)

        if params["stream"]:
            print(
                "[invoke_model] Retornando respuesta completa "
                "(modo stream, pero no synthesis_stream)"
            )
            return _invoke_openai_stream(client, params)

        print("[invoke_model] Retornando respuesta completa (modo no streaming)")
        completion = client.chat.completions.create(**params)
        full_response = completion.choices[0].message.content
        return full_response

    except Exception as e:
        st.error(f"Error al invocar {provider}: {e}")
        return f"Error: {str(e)}"
