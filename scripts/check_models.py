# -*- coding: utf-8 -*-
import os
import httpx
from dotenv import load_dotenv

load_dotenv("C:/Users/rerun/opendcmart/projects/project_buki/.env")
key = os.getenv("GEMINI_API_KEY")

models = [
    "gemini-2.5-flash",
    "gemini-2.5-pro",
    "gemini-2.5-flash-lite",
    "gemini-3.6-flash",
    "gemini-3.5-flash",
    "gemini-flash-latest",
    "gemini-flash-lite-latest",
    "gemini-pro-latest",
    "gemma-4-26b-a4b-it",
    "gemma-4-31b-it"
]

for m in models:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent?key={key}"
    payload = {"contents": [{"parts": [{"text": "Hello"}]}]}
    r = httpx.post(url, json=payload, timeout=10.0)
    print(f"Model {m:25s}: Status {r.status_code}")
    if r.status_code != 200:
        print(f"   Reason: {r.text[:120]}")
