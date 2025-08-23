import google.generativeai as genai
import requests
import os
import json
from dotenv import load_dotenv
from datetime import datetime

# Load your API keys
load_dotenv()
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

# Weather API configuration (using OpenWeatherMap)
WEATHER_API_KEY = os.getenv('OPENWEATHER_API_KEY')  # Your OpenWeatherMap API key
WEATHER_BASE_URL = "https://api.openweathermap.org/data/2.5/weather"  # Using HTTPS as recommended

# Create the model
model = genai.GenerativeModel('gemini-1.5-flash')

def get_weather(city_name):
    """Get current weather for a city using OpenWeatherMap API"""
    try:
        # Format city name properly (handle spaces and special characters)
        city_formatted = city_name.strip()
        
        params = {
            'q': city_formatted,
            'appid': WEATHER_API_KEY,  # Note: OpenWeatherMap uses 'appid' (lowercase)
            'units': 'metric'  # Use Celsius
        }
        
        print(f"Fetching weather for: {city_formatted}")  # Debug info
        
        response = requests.get(WEATHER_BASE_URL, params=params)
        response.raise_for_status()
        
        data = response.json()
        
        weather_info = {
            'city': data['name'],
            'country': data['sys']['country'],
            'temperature': data['main']['temp'],
            'feels_like': data['main']['feels_like'],
            'humidity': data['main']['humidity'],
            'description': data['weather'][0]['description'].title(),
            'wind_speed': data['wind']['speed']
        }
        
        return weather_info
        
    except requests.exceptions.HTTPError as e:
        if response.status_code == 401:
            return "❌ Weather API key is invalid or not activated yet. Please check your API key."
        elif response.status_code == 404:
            return f"❌ City '{city_name}' not found. Please check the spelling."
        else:
            return f"❌ Weather API error: {str(e)}"
    except requests.exceptions.RequestException as e:
        return f"❌ Network error fetching weather data: {str(e)}"
    except KeyError as e:
        return f"❌ Error parsing weather data: {str(e)}"

def get_current_time():
    """Get current date and time"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def detect_intent(question):
    """Simple intent detection to determine if user is asking for weather or time"""
    question_lower = question.lower()
    
    if any(word in question_lower for word in ['weather', 'temperature', 'rain', 'sunny', 'cloudy']):
        return 'weather'
    elif any(word in question_lower for word in ['time', 'date', 'today', "what's the time"]):
        return 'time'
    else:
        return 'general'

def extract_city_from_question(question):
    """Extract city name from user question, handling punctuation properly"""
    import re
    
    # Remove punctuation and convert to lowercase for processing
    clean_question = re.sub(r'[^\w\s]', '', question.lower())
    words = clean_question.split()
    
    # Look for common patterns like "weather in [city]" or "weather for [city]"
    trigger_words = ['in', 'for', 'at']
    
    for trigger in trigger_words:
        if trigger in words:
            try:
                city_index = words.index(trigger) + 1
                if city_index < len(words):
                    # Handle multi-word city names (take remaining words)
                    city_parts = words[city_index:]
                    return ' '.join(city_parts).title()  # Proper case for city name
            except ValueError:
                continue
    
    # If no trigger words found, look for common city indicators
    # Check if any word looks like a city (capitalized in original question)
    original_words = question.split()
    for word in original_words:
        # Remove punctuation from word
        clean_word = re.sub(r'[^\w]', '', word)
        if clean_word and clean_word[0].isupper() and len(clean_word) > 2:
            # This might be a city name
            return clean_word
    
    return None

def ask_ai_with_tools(question):
    """Enhanced AI function that can use tools for real-time data"""
    intent = detect_intent(question)
    
    if intent == 'weather':
        city = extract_city_from_question(question)
        if not city:
            return "I can help you with weather! Please specify a city. For example: 'What's the weather in London?'"
        
        weather_data = get_weather(city)
        
        if isinstance(weather_data, dict):
            # Format weather data nicely and ask AI to present it conversationally
            weather_context = f"""
            Current weather data for {weather_data['city']}, {weather_data['country']}:
            - Temperature: {weather_data['temperature']}°C (feels like {weather_data['feels_like']}°C)
            - Condition: {weather_data['description']}
            - Humidity: {weather_data['humidity']}%
            - Wind speed: {weather_data['wind_speed']} m/s
            
            Present this weather information in a conversational way to answer the user's question: "{question}"
            """
            
            response = model.generate_content(weather_context)
            return response.text
        else:
            return weather_data  # Error message
    
    elif intent == 'time':
        current_time = get_current_time()
        time_context = f"Current date and time: {current_time}. Answer the user's question: '{question}'"
        response = model.generate_content(time_context)
        return response.text
    
    else:
        # Regular AI response for general questions
        response = model.generate_content(question)
        return response.text

    # Test the enhanced version
if __name__ == "__main__":
    print("Testing Enhanced AI with Tools...")
    print("Available tools: Weather data, Current time")
    print("Example questions:")
    print("- What's the weather in London")
    print("- Weather for New York") 
    print("- What time is it")
    print("- Regular questions still work too!")
    print("-" * 50)
    
    # Check if API key exists
    if not WEATHER_API_KEY:
        print("⚠️  Weather API key not found. Add OPENWEATHER_API_KEY to your .env file")
        print("⚠️  Get your free API key from: https://openweathermap.org/api")
    else:
        print(f"✅ Weather API key loaded: {WEATHER_API_KEY[:8]}...")
        
        # Test weather functionality
        print("Testing weather feature...")
        weather_response = ask_ai_with_tools("Weather in London")
        print(f"AI: {weather_response}\n")
    
    # Test time functionality  
    print("Testing time feature...")
    time_response = ask_ai_with_tools("What time is it")
    print(f"AI: {time_response}\n")
    
    # Interactive chat with tools
    print("Chat with Enhanced AI (type 'quit' to exit):")
    print("💡 Tip: Try questions like 'weather in Paris' or 'what time is it'")
    print()
    
    while True:
        user_input = input("You: ")
        if user_input.lower() in ['quit', 'exit', 'bye']:
            print("Goodbye!")
            break
        
        response = ask_ai_with_tools(user_input)
        print(f"AI: {response}")
        print()