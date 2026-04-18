import argparse
import os
import subprocess
import sys
from pathlib import Path

from openai import OpenAI
from openai.types.chat import ChatCompletionFunctionToolParam

API_KEY = os.getenv("OPENROUTER_API_KEY",default='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')
BASE_URL = os.getenv("OPENROUTER_BASE_URL", default="https://openrouter.ai/api/v1")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("-p", required=True)
    args = p.parse_args()

    if not API_KEY:
        raise RuntimeError("OPENROUTER_API_KEY is not set")

    client = OpenAI(api_key=API_KEY, base_url=BASE_URL)
    stop=False
    message = [{"role": "user", "content": args.p}]
    while not stop:
        chat = client.chat.completions.create(
            model="anthropic/claude-haiku-4.5",
            messages=message,
            tools=[
                {
                    "type":"function",
                    "function":{
                        "name":"Read",
                        "description": "Read and return the contents of a file",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "file_path": {
                                    "type": "string",
                                    "description": "The path to the file to read"
                                }
                            },
                            "required": ["file_path"]
                    }
                }},
                {
                    "type": "function",
                    "function": {
                        "name": "Write",
                        "description": "Write content to a file",
                        "parameters": {
                            "type": "object",
                            "required": ["file_path", "content"],
                            "properties": {
                                "file_path": {
                                    "type": "string",
                                    "description": "The path of the file to write to"
                                },
                                "content": {
                                    "type": "string",
                                    "description": "The content to write to the file"
                                }
                            }
                        }
                    }
                },
                {
                    "type": "function",
                    "function": {
                        "name": "Bash",
                        "description": "Execute a shell command",
                        "parameters": {
                            "type": "object",
                            "required": ["command"],
                            "properties": {
                                "command": {
                                    "type": "string",
                                    "description": "The command to execute"
                                }
                            }
                        }
                    }
                }

            ]
        )

        if not chat.choices or len(chat.choices) == 0:
            raise RuntimeError("no choices in response")

        # You can use print statements as follows for debugging, they'll be visible when running tests.
        print("Logs from your program will appear here!", file=sys.stderr)
        assistant_message = {
            "role": "assistant",
            "content": chat.choices[0].message.content,
            "tool_calls": chat.choices[0].message.tool_calls,
        }
        message.append(assistant_message)

        # TODO: Uncomment the following line to pass the first stage
        if chat.choices[0].message.tool_calls:
            tool_calls = chat.choices[0].message.tool_calls
            if tool_calls:
                # tool_call = tool_calls[0]
                for tool_call in tool_calls:
                    if tool_call.type == "function":
                        if tool_call.function.name == "Read":
                            import json
                            json_arg = tool_call.function.arguments
                            arg_dict=json.loads(json_arg)
                            path=arg_dict.get("file_path")
                            with open(path,"r") as f:
                                data=f.read()
                                tool_ms={
                                    'role': 'tool',
                                    'tool_call_id': tool_call.id,
                                    'content': data
                                }
                                message.append(tool_ms)
                        if tool_call.function.name == "Write":
                            import json
                            json_arg = tool_call.function.arguments
                            arg_dict=json.loads(json_arg)
                            path=arg_dict.get("file_path")
                            content=arg_dict.get("content")
                            with open(path,"w") as f:
                                f.write(content)
                                tool_ms={
                                    'role': 'tool',
                                    'tool_call_id': tool_call.id,
                                    'content': "Successfully wrote to file"
                                }
                                message.append(tool_ms)
                        if tool_call.function.name == "Bash":
                            import json
                            json_arg = tool_call.function.arguments
                            arg_dict=json.loads(json_arg)
                            cmd=arg_dict.get("command")
                            path=Path(__file__).parent.resolve()
                            result=subprocess.run(cmd, shell=True,cwd=path,capture_output=True)
                            if result.returncode != 0:
                                tool_ms = {
                                    'role': 'tool',
                                    'tool_call_id': tool_call.id,
                                    'content': f"command failed with exit code {result.returncode} and error message {result.stderr}"
                                }
                                message.append(tool_ms)
                            else:
                                tool_ms={
                                    'role': 'tool',
                                    'tool_call_id': tool_call.id,
                                    'content': result.stderr.decode("utf-8")
                                }
                                message.append(tool_ms)
        else:
            print(chat.choices[0].message.content)
            stop=True


if __name__ == "__main__":
    main()
