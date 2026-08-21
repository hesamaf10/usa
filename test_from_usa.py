import base64
import concurrent.futures
import socket
import time
import urllib3
import requests

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# لینک سابسکرایپشن
SUB_URL = "https://raw.githubusercontent.com/ebrasha/free-v2ray-public-list/main/V2Ray-Config-By-EbraSha.txt"


def decode_base64(data):
    data = data.strip()
    missing_padding = len(data) % 4
    if missing_padding:
        data += "=" * (4 - missing_padding)
    try:
        return base64.b64decode(data).decode("utf-8", errors="ignore")
    except Exception:
        return data


def parse_node_host_port(config):
    try:
        if config.startswith(("vless://", "vmess://", "trojan://", "ss://")):
            parts = config.split("://")[1].split("#")[0]
            net_part = parts.split("@")[1] if "@" in parts else parts
            host_port = net_part.split("?")[0]
            if ":" in host_port:
                host, port = host_port.split(":")[:2]
                return host.strip(), int(port.strip())
    except Exception:
        pass
    return None, None


def test_from_usa(config):
    """تست سرور از داخل خاک آمریکا بدون فیلترینگ"""
    host, port = parse_node_host_port(config)
    if not host or not port:
        return None

    start = time.time()
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2.0)
        res = sock.connect_ex((host, port))
        sock.close()

        if res == 0:
            latency = int((time.time() - start) * 1000)
            # فیلتر فقط سرورهای آمریکا
            if any(
                tag in config.lower()
                for tag in ["us", "usa", "united", "america", "🇺🇸"]
            ):
                return {"config": config, "latency": latency}
    except Exception:
        pass
    return None


def main():
    session = requests.Session()
    session.trust_env = False

    res = session.get(SUB_URL, timeout=12, verify=False)
    if res.status_code == 200:
        content = res.text
        if not any(p in content for p in ["vless://", "vmess://", "trojan://"]):
            content = decode_base64(content)

        lines = [
            l.strip()
            for l in content.splitlines()
            if l.strip().startswith(
                ("vless://", "vmess://", "trojan://", "ss://")
            )
        ]

        healthy_nodes = []
        with concurrent.futures.ThreadPoolExecutor(
            max_workers=50
        ) as executor:
            results = executor.map(test_from_usa, lines)
            for r in results:
                if r:
                    healthy_nodes.append(r)

        healthy_nodes.sort(key=lambda x: x["latency"])

        if healthy_nodes:
            best_config = healthy_nodes[0]["config"]
            with open("usa_config.txt", "w", encoding="utf-8") as f:
                f.write(best_config + "\n")
            print(
                f"✅ بهترین کانفیگ آمریکا از داخل خاک آمریکا با پینگ {healthy_nodes[0]['latency']}ms استخراج شد!"
            )


if __name__ == "__main__":
    main()
