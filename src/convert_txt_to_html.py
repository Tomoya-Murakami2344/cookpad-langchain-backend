"""
txtファイルをhtmlに変換する
"""
from jinja2 import Template
import sys
file_name = sys.argv[1]

# txtファイルを読み込む,title : 料理名, instruction : 料理の作り方
with open(file_name, "r") as f:
    text = f.read()
# title を取得
title = text.split(":")[5].split("\n")[0].strip()
# instruction を取得
instruction = text.split(":")[6].replace("\n", "<br>").strip()


html_template = Template("""
        <html>
        <body>
        <h1>{{ title }}</h1>
        <p>{{ instruction }}</p>
        </body>
        </html>
        """)
html = html_template.render(title=title, instruction=instruction)
with open(file_name.replace(".txt", ".html"), "w") as f:
    f.write(html)