# build.py
# Makes usj_guide.html (the phone preview page) from template.html.
# The park data is read from ../data.py, so the page always uses the
# same rides, paths and weights as the Streamlit app. Run it again after
# changing data.py:   python build.py
#
# This page is only a preview for phones. It is NOT part of the 1D project
# submission (the project must be Python + Streamlit only).

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))

import assistant
import data
import map_view

# Collect every UPPER_CASE value from data.py.
page_data = {}
for name in dir(data):
    if name.isupper():
        page_data[name] = getattr(data, name)

# The map drawing constants, the chatbot keywords and the menu order.
page_data["MAP"] = {}
for name in dir(map_view):
    if name.isupper():
        page_data["MAP"][name] = getattr(map_view, name)
page_data["KEYWORDS"] = assistant.KEYWORDS
page_data["COMMON_WORDS"] = assistant.COMMON_WORDS
page_data["MENU_CATEGORIES"] = ["Shops", "Services", "Amenities", "Emergency"]

template = open(os.path.join(HERE, "template.html"), encoding="utf-8").read()
assert template.count("/*__DATA__*/null") == 1
# "</" is escaped so that data can never close the <script> tag early.
data_text = json.dumps(page_data, ensure_ascii=False).replace("</", "<\\/")
page = template.replace("/*__DATA__*/null", data_text)

open(os.path.join(HERE, "usj_guide.html"), "w", encoding="utf-8", newline="\n").write(page)
print("Wrote usj_guide.html,", len(page) // 1024, "KB")

# A second copy that opens straight from this folder in a laptop browser.
# (The published page gets this wrapper added automatically.)
local = ('<!doctype html><html><head><meta charset="utf-8">'
         '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">'
         '<style>body{margin:0}[hidden]{display:none!important}</style></head><body>'
         + page + '</body></html>')
open(os.path.join(HERE, "usj_guide_local.html"), "w", encoding="utf-8", newline="\n").write(local)
