#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import requests
from typing import List
from pilot.configs.config import Config
from pilot.conversation import ROLE_ASSISTANT, ROLE_USER
from pilot.scene.base_message import ModelMessage, ModelMessageRoleType

CFG = Config()


def proxyllm_generate_stream(model, tokenizer, params, device, context_len=2048):
    history = []

    prompt = params["prompt"]
    stop = params.get("stop", "###")

    headers = {
        "Authorization": "Bearer " + CFG.proxy_api_key,
        "Token": CFG.proxy_api_key,
    }

    messages: List[ModelMessage] = params["messages"]
    # Add history conversation
    for message in messages:
        if message.role == ModelMessageRoleType.HUMAN:
            history.append({"role": "user", "content": message.content})
        elif message.role == ModelMessageRoleType.SYSTEM:
            history.append({"role": "system", "content": message.content})
        elif message.role == ModelMessageRoleType.AI:
            history.append({"role": "assistant", "content": message.content})
        else:
            pass

    # Move the last user's information to the end
    temp_his = history[::-1]
    last_user_input = None
    for m in temp_his:
        if m["role"] == "user":
            last_user_input = m
            break
    if last_user_input:
        history.remove(last_user_input)
        history.append(last_user_input)

    payloads = {
        "model": "gpt-3.5-turbo",  # just for test, remove this later
        "messages": history,
        "temperature": params.get("temperature"),
        "max_tokens": params.get("max_new_tokens"),
        "stream": True,
    }

    res = requests.post(
        CFG.proxy_server_url, headers=headers, json=payloads, stream=True
    )

    text = ""
    for line in res.iter_lines():
        if line:
            if not line.startswith(b"data: "):
                error_message = line.decode("utf-8")
                yield error_message
            else:
                json_data = line.split(b": ", 1)[1]
                decoded_line = json_data.decode("utf-8")
                if decoded_line.lower() != "[DONE]".lower():
                    obj = json.loads(json_data)
                    if obj["choices"][0]["delta"].get("content") is not None:
                        content = obj["choices"][0]["delta"]["content"]
                        text += content
                yield text
