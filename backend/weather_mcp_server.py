import json
import urllib.parse
import urllib.request
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Weather Manager")


def _fetch(city: str) -> dict:
    url = f"https://wttr.in/{urllib.parse.quote(city)}?format=j1&lang=zh"
    req = urllib.request.Request(url, headers={"User-Agent": "curl/8.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        raw = resp.read().decode("utf-8")
    return json.loads(raw)


def _zh_desc(cur: dict) -> str:
    lang = cur.get("lang_zh")
    if lang and isinstance(lang, list) and lang[0].get("value"):
        return lang[0]["value"]
    desc = cur.get("weatherDesc")
    if desc and isinstance(desc, list):
        return desc[0].get("value", "")
    return ""


@mcp.tool()
def query_weather(city: str) -> str:
    """查询指定城市的实时天气。
    :param city: 城市名称，如"北京"、"上海"，支持中英文
    """
    try:
        data = _fetch(city)
    except Exception as e:
        return json.dumps({"error": f"查询失败: {e}"}, ensure_ascii=False)

    if "current_condition" not in data:
        return json.dumps({"error": f"未获取到 {city} 的天气数据"}, ensure_ascii=False)

    cur = data["current_condition"][0]
    result = {
        "city": city,
        "temp_C": cur.get("temp_C"),
        "feels_like_C": cur.get("FeelsLikeC"),
        "weather": _zh_desc(cur),
        "humidity": cur.get("humidity"),
        "wind_dir": cur.get("winddir16Point"),
        "wind_speed_kmph": cur.get("windspeedKmph"),
        "observed_at": cur.get("localObsDateTime"),
    }
    return json.dumps(result, ensure_ascii=False)


@mcp.tool()
def query_forecast(city: str, days: int = 3) -> str:
    """查询指定城市未来几天的天气预报。
    :param city: 城市名称，如"北京"
    :param days: 预报天数，1-3，默认 3
    """
    days = max(1, min(int(days), 3))
    try:
        data = _fetch(city)
    except Exception as e:
        return json.dumps({"error": f"查询失败: {e}"}, ensure_ascii=False)

    weather = data.get("weather", [])[:days]
    result = []
    for d in weather:
        hourly = d.get("hourly", [])
        mid = hourly[len(hourly) // 2] if hourly else {}
        result.append({
            "date": d.get("date"),
            "max_temp_C": d.get("maxtempC"),
            "min_temp_C": d.get("mintempC"),
            "weather": _zh_desc(mid) if mid else "",
        })
    return json.dumps({"city": city, "forecast": result}, ensure_ascii=False)


if __name__ == "__main__":
    mcp.run(transport="stdio")