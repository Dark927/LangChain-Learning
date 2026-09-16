import codecs

with open('src/ui.py', 'r', encoding='utf-8') as f:
    content = f.read()

target = """            def _make_toggle(e=entry):
                def toggle():
                    e.configure(show="" if e.cget("show") == "●" else "●")
                return toggle

            ctk.CTkButton(entry_row, text="👁", width=36, height=36, font=PRO_FONT,
                          command=_make_toggle()).pack(side="left")"""

replacement = """            def _make_paste(e=entry):
                def do_paste():
                    try:
                        clip = e.clipboard_get()
                        e.delete(0, "end")
                        e.insert(0, clip)
                    except Exception:
                        pass
                return do_paste

            def _make_toggle(e=entry):
                def toggle():
                    e.configure(show="" if e.cget("show") == "●" else "●")
                return toggle

            ctk.CTkButton(entry_row, text="📋", width=36, height=36, font=PRO_FONT,
                          command=_make_paste()).pack(side="left", padx=(0, 6))

            ctk.CTkButton(entry_row, text="👁", width=36, height=36, font=PRO_FONT,
                          command=_make_toggle()).pack(side="left")"""

if target in content:
    with open('src/ui.py', 'w', encoding='utf-8') as f:
        f.write(content.replace(target, replacement))
    print('Replaced successfully.')
else:
    print('Target not found.')
