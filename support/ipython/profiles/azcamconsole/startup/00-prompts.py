import os
import sys
from IPython.terminal.prompts import Prompts, Token

# get IPython reference
ip = get_ipython()


class MyPrompt(Prompts):
    def __init__(self, *args, **kwargs):
        super(MyPrompt, self).__init__(*args, **kwargs)

    def in_prompt_tokens(self, cli=None):
        return [
            (Token, os.getcwd()),
            (Token.Prompt, ">"),
        ]

    def out_prompt_tokens(self):
        return [
            (Token, ""),
            (Token.Prompt, "==>"),
        ]


ip.prompts = MyPrompt(ip)
ip.separate_in = ""
