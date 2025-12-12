from duckduckgo_search import DDGS
import json
import requests
import urllib.parse

def get_weather(query: str) -> str:
    """
    Get weather information. Tries OpenWeatherMap first (if key provided), 
    falls back to wttr.in (no key required).
    """
    # Extract city from query (simple heuristic)
    city = query.lower().replace("weather", "").replace("in", "").strip()
    if not city:
        return ""

    # 1. Try OpenWeatherMap (User requested, but requires key usually)
    # Using the endpoint provided by user, but it will likely fail without a key.
    # We'll try it just in case, but expect 401.
    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?q={urllib.parse.quote(city)}&appid="
        resp = requests.get(url, timeout=2)
        if resp.status_code == 200:
            data = resp.json()
            weather = data['weather'][0]['description']
            temp = round(data['main']['temp'] - 273.15, 1) # Kelvin to Celsius
            return f"Current weather in {city}: {weather}, {temp}°C (Source: OpenWeatherMap)"
    except:
        pass

    # 2. Fallback to wttr.in (Reliable, no key)
    try:
        url = f"https://wttr.in/{urllib.parse.quote(city)}?format=3"
        resp = requests.get(url, timeout=3)
        if resp.status_code == 200:
            return f"Weather Info: {resp.text.strip()} (Source: wttr.in)"
    except Exception as e:
        return f"Could not fetch weather: {str(e)}"
    
    return ""

def search_wikipedia(query: str) -> str:
    """
    Search Wikipedia for a summary.
    """
    try:
        # Clean query for Wikipedia
        search_term = query.replace("who is", "").replace("what is", "").replace("define", "").strip()
        
        url = "https://en.wikipedia.org/w/api.php"
        params = {
            "action": "query",
            "format": "json",
            "prop": "extracts",
            "exintro": True,
            "explaintext": True,
            "titles": search_term
        }
        
        resp = requests.get(url, params=params, timeout=3)
        data = resp.json()
        
        pages = data.get("query", {}).get("pages", {})
        result_text = ""
        
        for page_id, page in pages.items():
            if page_id == "-1":
                continue
            title = page.get("title", "Unknown")
            extract = page.get("extract", "")
            if extract:
                result_text += f"Wikipedia Summary ({title}):\n{extract[:1000]}...\nSource: https://en.wikipedia.org/wiki/{urllib.parse.quote(title)}\n\n"
                
        return result_text
    except Exception as e:
        return f"Wikipedia search error: {str(e)}"

def search_web(query: str, max_results: int = 5) -> str:
    """
    Smart search that combines DuckDuckGo, Wikipedia, and Weather.
    """
    combined_results = []
    query_lower = query.lower()
    
    # 1. Check for Weather
    if "weather" in query_lower:
        weather_info = get_weather(query)
        if weather_info:
            combined_results.append(f"=== WEATHER ===\n{weather_info}")

    # 2. Check for Wikipedia intent (Who/What/Define)
    if any(x in query_lower for x in ["who is", "what is", "define", "wiki"]):
        wiki_info = search_wikipedia(query)
        if wiki_info:
            combined_results.append(f"=== WIKIPEDIA ===\n{wiki_info}")

    # 3. General Web Search (DuckDuckGo)
    # If it looks like a person search, we append "linkedin" to one of the search queries internally
    # or just rely on DDG. To ensure LinkedIn comes up, we can do a specific search.
    try:
        print(f"Searching web for: {query}")
        with DDGS() as ddgs:
            # Standard search
            results = list(ddgs.text(query, max_results=max_results))
            
            # If it looks like a person search (short query, no question words other than 'who'), 
            # try to find social links.
            # Simple heuristic: if query is short and doesn't have "weather" or "news"
            if len(query.split()) <= 3 and "weather" not in query_lower:
                 # Try to fetch LinkedIn specifically if not present
                 has_linkedin = any("linkedin.com" in r.get('href', '') for r in results)
                 if not has_linkedin:
                     linkedin_results = list(ddgs.text(f"{query} linkedin", max_results=1))
                     if linkedin_results:
                         results.extend(linkedin_results)

        if results:
            formatted_results = []
            for r in results:
                formatted_results.append(f"Title: {r['title']}\nLink: {r['href']}\nSnippet: {r['body']}")
            combined_results.append("=== WEB SEARCH RESULTS ===\n" + "\n\n".join(formatted_results))
        else:
            combined_results.append("No web search results found.")
            
    except Exception as e:
        combined_results.append(f"Error searching web: {str(e)}")

    return "\n\n".join(combined_results)
