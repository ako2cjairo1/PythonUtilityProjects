# from pygments import highlight
from pygments.lexers import PythonLexer
# from pygments.formatters import TerminalFormatter


# def highlight_code(code: str):
#     print(highlight(code, PythonLexer(), TerminalFormatter()))


# highlight_code("This is a text that contains a code snippet in Python: ```print('Hello World!')```. And this is a code snippet in JavaScript ```console.log('Hello World!')```")


import re
from pygments import highlight
from pygments.lexers import get_all_lexers, get_lexer_by_name
from pygments.formatters import TerminalFormatter


def highlight_code_snippets(text: str):
    code_snippets = re.findall(r'```(.+?)```', text)
    for code in code_snippets:
        print(code)
        pattern = re.compile(r'```(.+?)```', re.DOTALL)
        if pattern.search(code):
            # if '```' in code:
            code = re.sub(r'```', '', code)
            # print(highlight(code, PythonLexer(), TerminalFormatter()))
        else:
            print('')
        # for lexer_name in get_all_lexers():
        #     try:
        #         lexer = get_lexer_by_name(lexer_name, stripall=True)
        #         lexer.analyse_text(code)
        #         break
        #     except:
        #         pass
        # if lexer:
        #     # print(highlight(code, lexer, TerminalFormatter(style='xcode')))
        #     print(f"this code: {code}")
        # else:
        #     # print(code)
        #     print(highlight(code, PythonLexer(), TerminalFormatter()))


highlight_code_snippets(
    "This is a text that contains a code snippet in Python: ```print('Hello World!')```. And this is a code snippet in JavaScript ```console.log('Hello World!')```")
