from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import requests
from bs4 import BeautifulSoup
import openai
import os
import re
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Rate limiting: 250 requests per day per IP address
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["250 per day", "50 per hour"],
    storage_uri="memory://"
)

# Groq API Configuration
# IMPORTANT: API key is loaded from environment variable for security
openai.api_key = os.environ.get('GROQ_API_KEY')
openai.api_base = "https://api.groq.com/openai/v1"

if not openai.api_key:
    print("⚠️  WARNING: GROQ_API_KEY environment variable not set!")
    print("   AI features will be disabled.")
    print("   Set GROQ_API_KEY=your-api-key in your environment")

def get_image_size(img_url):
    """
    Проверява размера на снимката в байтове
    """
    try:
        response = requests.head(img_url, timeout=3, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        size = int(response.headers.get('content-length', 0))
        return size
    except:
        return 0

@app.route('/api/scrape', methods=['POST'])
@limiter.limit("10 per minute")  # Additional stricter limit for scraping endpoint
def scrape_url():
    """
    Приема URL, скрапва страницата, използва AI за структуриране
    """
    try:
        data = request.json
        url = data.get('url')
        
        if not url:
            return jsonify({'error': 'URL is required'}), 400
        
        # Стъпка 1: Скрапване на страницата
        logger.info(f"Scraping URL: {url}")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # Стъпка 2: Парсване на HTML
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Извличане на ВСИЧКИ текстове
        texts = soup.stripped_strings
        full_text = ' '.join(texts)
        
        # Извличане на ВСИЧКИ възможни image URLs
        all_image_urls = set()
        
        # 1. От <img> тагове (всички възможни атрибути)
        for img in soup.find_all('img'):
            for attr in ['src', 'data-src', 'data-lazy-src', 'data-zoom-image', 'data-large-image', 'data-original', 'data-full']:
                img_url = img.get(attr)
                if img_url:
                    all_image_urls.add(img_url)
        
        # 2. От <a> линкове към снимки
        for link in soup.find_all('a', href=True):
            href = link['href']
            if any(ext in href.lower() for ext in ['.jpg', '.jpeg', '.png']):
                all_image_urls.add(href)
        
        # 3. От JavaScript/текст (regex търсене в целия HTML)
        html_text = str(soup)
        found_urls = re.findall(r'(https?://[^\s\'"<>]+\.(?:jpg|jpeg|png))', html_text, re.IGNORECASE)
        all_image_urls.update(found_urls)
        
        logger.info(f"Found {len(all_image_urls)} potential image URLs")
        
        # Направи ги абсолютни и филтрирай
        processed_images = []
        
        for img_url in all_image_urls:
            # Направи абсолютен URL
            if img_url.startswith('//'):
                img_url = 'https:' + img_url
            elif img_url.startswith('/'):
                from urllib.parse import urljoin
                img_url = urljoin(url, img_url)
            
            img_url_lower = img_url.lower()
            
            # Пропусни GIF
            if '.gif' in img_url_lower:
                continue
            
            # Пропусни нежелани keywords
            if any(skip in img_url_lower for skip in [
                'logo', 'icon', 'banner', 'button', 'arrow',
                'loading', 'spacer', 'blank', 'spinner',
                'facebook', 'twitter', 'instagram', 'youtube', 'pinterest',
                'paypal', 'visa', 'mastercard', 'amex', 'stripe', 'discover',
                'flag', 'menu', 'cart', 'search', 'user', 'avatar',
                'header', 'footer', 'nav', 'star', 'heart', 'favorite',
                '_thumb', '-thumb', '_small', '-small', '_sm', '-sm',
                '_xs', '-xs', '_150', '_200', '_250', '_300',
                'thumbnail', 'widget', 'sidebar'
            ]):
                continue
            
            processed_images.append(img_url)
        
        logger.info(f"After filtering: {len(processed_images)} images")
        
        # КРИТИЧНО: Сортирай по размер на файла
        images_with_size = []
        checked = 0
        for img_url in processed_images:
            if checked >= 25:  # Провери максимум 25 снимки
                break
            
            size = get_image_size(img_url)
            if size > 15000:  # Минимум 15KB (по-големи от thumbnails)
                images_with_size.append((size, img_url))
                logger.debug(f"  {img_url.split('/')[-1]} - {size // 1000}KB")
            
            checked += 1
        
        # Сортирай по размер (най-големите първи)
        images_with_size.sort(reverse=True, key=lambda x: x[0])
        
        # Вземи само най-големите 2-3 снимки
        images = [img[1] for img in images_with_size[:3]]
        
        logger.info(f"Selected {len(images)} largest images")
        
        # Стъпка 3: AI обработка
        logger.debug("=== AI Processing ===")
        logger.debug(f"API Key configured: {bool(openai.api_key)}")
        
        if openai.api_key:
            logger.debug("Calling AI extraction function...")
            try:
                structured_data = extract_coin_data_with_ai(full_text)
                logger.info(f"AI successfully extracted data")
            except Exception as e:
                logger.error(f"AI extraction failed: {str(e)}", exc_info=True)
                structured_data = {
                    'year': '',
                    'emperor': '',
                    'ruler': '',
                    'dynasty': '',
                    'mint': '',
                    'city': '',
                    'province': '',
                    'country': '',
                    'moneyer': '',
                    'denomination': '',
                    'catalogNumbers': '',
                    'obverseDescription': '',
                    'reverseDescription': '',
                    'material': '',
                    'diameter': '',
                    'weight': '',
                    'grade': '',
                    'price': '',
                    'notes': full_text[:500]
                }
        else:
            logger.warning("No API key configured - AI features disabled")
            structured_data = {
                'year': '',
                'emperor': '',
                'ruler': '',
                'dynasty': '',
                'mint': '',
                'city': '',
                'province': '',
                'country': '',
                'moneyer': '',
                'denomination': '',
                'catalogNumbers': '',
                'obverseDescription': '',
                'reverseDescription': '',
                'material': '',
                'diameter': '',
                'weight': '',
                'grade': '',
                'price': '',
                'notes': full_text[:500]
            }
        
        # Добави снимките
        structured_data['images'] = images
        
        return jsonify(structured_data), 200
        
    except Exception as e:
        logger.error(f"Error scraping URL: {str(e)}", exc_info=True)
        return jsonify({'error': 'Failed to scrape URL'}), 500

def extract_coin_data_with_ai(text):
    """
    Използва Groq API за извличане на структурирани данни
    """
    try:
        # Ограничи текста до 2000 символа
        text_sample = text[:2000]
        
        prompt = f"""Extract coin information from this text and return ONLY a valid JSON object.

Text: {text_sample}

Extract and return a JSON object with ALL these fields (use empty string "" if not found):
{{
  "year": "year or period (e.g., '100-200 AD', '336-323 BC')",
  "emperor": "emperor, ruler, sultan, or caliph name (e.g., 'Trajan', 'Alexander III', 'Saladin')",
  "ruler": "same as emperor - ruler name for non-Roman coins",
  "dynasty": "dynasty or ruling family (e.g., 'Julio-Claudian', 'Umayyad', 'Heraclian')",
  "mint": "mint location or city (e.g., 'Rome', 'Athens', 'Antioch', 'Constantinople')",
  "city": "same as mint - city name (e.g., 'Athens', 'Corinth', 'Syracuse')",
  "province": "province or region (e.g., 'Lydia', 'Thrace', 'Syria')",
  "country": "country or kingdom (e.g., 'France', 'England', 'Holy Roman Empire')",
  "moneyer": "moneyer or magistrate name for Roman Republican coins",
  "denomination": "coin denomination (e.g., 'Denarius', 'Tetradrachm', 'AE', 'Follis', 'Solidus')",
  "obverseDescription": "description of obverse/front side",
  "reverseDescription": "description of reverse/back side",
  "material": "metal type (e.g., 'Silver', 'Bronze', 'Gold', 'Billon', 'Copper')",
  "diameter": "diameter in mm (ONLY the number, e.g., '20' or '20.5')",
  "weight": "weight in grams (ONLY the number, e.g., '3.5' or '12.3')",
  "catalogNumbers": "catalog references (e.g., 'RIC 123', 'Sear 456', 'SNG 789')",
  "grade": "condition or grade (e.g., 'VF', 'XF', 'EF', 'Fine', 'Good', 'Choice')",
  "price": "price with currency (e.g., '45 EUR', '$50', '30 USD')",
  "notes": "any additional important information"
}}

IMPORTANT EXTRACTION RULES:
- For diameter and weight: extract ONLY the numeric value, remove units like 'mm', 'g', 'grams'
- For grade: look for condition terms like VF, XF, EF, Fine, Good Fine, Very Fine, Extremely Fine, Choice
- For price: include both number and currency symbol/code
- For denomination: recognize terms like Tetradrachm, Drachm, Obol, Denarius, Sestertius, As, AE (bronze), Follis, Solidus, Miliaresion
- emperor and ruler should have the same value (fill both with the ruler's name)
- mint and city should have the same value (fill both with the location)
- If you see "moneyer" or "magistrate" in the text, extract it to the moneyer field
- If you see dynasty name (e.g., "Julio-Claudian", "Flavian", "Severan", "Abbasid"), extract it to dynasty field
- If text mentions a province (e.g., "Lydia", "Thrace", "Bithynia"), extract it to province field

Return ONLY the JSON object, no explanation:"""
        
        response = openai.ChatCompletion.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "You are a numismatic expert JSON API. Return only valid JSON with coin data, nothing else."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=500
        )
        
        response_text = response.choices[0].message.content.strip()
        logger.debug(f"AI raw response: {response_text[:200]}...")
        
        # Опитай се да извлечеш JSON
        import json
        
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
            result = json.loads(json_str)
            logger.debug("Successfully parsed JSON from AI response")
            return result
        else:
            logger.warning("No JSON found in AI response")
            raise ValueError("No JSON in response")
        
    except Exception as e:
        logger.error(f"AI extraction error: {str(e)}", exc_info=True)
        return {
            'year': '',
            'emperor': '',
            'ruler': '',
            'dynasty': '',
            'mint': '',
            'city': '',
            'province': '',
            'country': '',
            'moneyer': '',
            'denomination': '',
            'catalogNumbers': '',
            'obverseDescription': '',
            'reverseDescription': '',
            'material': '',
            'diameter': '',
            'weight': '',
            'grade': '',
            'price': '',
            'notes': text[:500]
        }

@app.route('/api/health', methods=['GET'])
def health_check():
    """
    Проверка дали сървърът работи
    """
    return jsonify({'status': 'OK', 'message': 'Backend is running'}), 200

@app.errorhandler(429)
def ratelimit_handler(e):
    """Handle rate limit exceeded"""
    logger.warning(f'Rate limit exceeded from {get_remote_address()}')
    return jsonify({
        'error': 'Rate limit exceeded',
        'message': 'You have exceeded the maximum number of requests. Please try again later.'
    }), 429

@app.errorhandler(404)
def not_found(e):
    """Handle 404 errors"""
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(e):
    """Handle 500 errors"""
    logger.error(f'Internal server error: {str(e)}', exc_info=True)
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug_mode = os.environ.get('DEBUG', 'False').lower() == 'true'

    logger.info("🚀 Coin Collector Backend starting...")
    logger.info(f"📡 Server running on port {port}")
    logger.info(f"🔐 API Key configured: {bool(openai.api_key)}")
    logger.info(f"🛡️  Rate limiting: 250 requests/day, 50 requests/hour")

    app.run(debug=debug_mode, host='0.0.0.0', port=port)