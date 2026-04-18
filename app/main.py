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

    chat = client.chat.completions.create(
        model="anthropic/claude-haiku-4.5",
        messages=[{"role": "user", "content": args.p}],
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
    if chat.choices[0].message.tool_calls[0]:
        if chat.choices[0].message.tool_calls[0].get("type") == "function":
            if chat.choices[0].message.tool_calls[0].get("type").get("function").get("name") == "Read":
                json_arg=chat.choices[0].message.tool_calls[0].get("type").get("function").get("arguments")
                import json
                arg_dict=json.loads(json_arg)
                path=arg_dict.get("file_path")
                with open(path,"r") as f:
                    data=f.read()
                    print(data)
    else:
        print(chat.choices[0].message.content)


if __name__ == "__main__":
    main()
