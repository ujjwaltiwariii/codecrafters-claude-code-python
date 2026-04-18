import argparse
import os
import sys

from openai import OpenAI

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
                }}
            ]
        )

        if not chat.choices or len(chat.choices) == 0:
            raise RuntimeError("no choices in response")

        # You can use print statements as follows for debugging, they'll be visible when running tests.
        print("Logs from your program will appear here!", file=sys.stderr)

        # TODO: Uncomment the following line to pass the first stage
        if chat.choices[0].message.tool_calls:
            tool_calls = chat.choices[0].message.tool_calls
            if tool_calls:
                tool_call = tool_calls[0]
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
                                'tool_use_id': tool_call.id,
                                'content': data
                            }
                            message.append(tool_ms)
        else:
            print(chat.choices[0].message.content)
            stop=True


if __name__ == "__main__":
    main()
