#!/usr/bin/env python3.10

def get_format(file_path: str) -> str:
    ext = (file_path.split("/")[-1]).split(".")[-1]
    filt_ext = ""
    for i in ext:
        if i.isalpha():
            filt_ext += i
    return str(filt_ext)
