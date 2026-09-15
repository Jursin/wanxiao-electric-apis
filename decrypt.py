import base64
import sys
from urllib.parse import parse_qsl

from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad


def decrypt(body):
    form = dict(parse_qsl(body.strip(), keep_blank_values=True))
    cipher = base64.b64decode(form["encryptData"])
    ts = str(form["timestamp"])
    key = ((ts[:6] if int(ts) % 2 else ts[-6:]) + form["randomStr"]).encode()
    return unpad(AES.new(key, AES.MODE_ECB).decrypt(cipher), AES.block_size)


def main():
    print("请粘贴 SWAEEncryptServlet 请求的请求体 RAW 文本：", file=sys.stderr)
    text = ""
    for line in sys.stdin:
        text += line
        if "encryptData=" in text:
            break
    try:
        plain = decrypt(text)
    except Exception as exc:
        print(f"[error] {exc}", file=sys.stderr)
        return 1
    sys.stdout.buffer.write(plain)
    return 0


if __name__ == "__main__":
    sys.exit(main())
