import requests
import time
import base64
from flask import Flask, jsonify, request
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from pydub import AudioSegment
import whisper

# Initialize Flask app
app = Flask(__name__)

# Function to solve reCAPTCHA using audio challenge
def solve_recaptcha(site_key, url):
    # Setting up Selenium WebDriver (with headless mode)
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Running in headless mode
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))

    driver.get(url)

    # Solve the reCAPTCHA by interacting with the DOM
    # Find and click the reCAPTCHA iframe
    # captcha_frame = driver.find_element(By.CSS_SELECTOR, "iframe[title='reCAPTCHA']")
    # driver.switch_to.frame(captcha_frame)

    # Find and click the reCAPTCHA
    audio_button = driver.find_element(By.CSS_SELECTOR, "#recaptcha-anchor")
    audio_button.click()
    # Click on the audio button to get the challenge
    audio_button = driver.find_element(By.CSS_SELECTOR, "#recaptcha-audio-button")
    audio_button.click()
    
    # Click on the play button to get the audio
    audio_button = driver.find_element(By.CSS_SELECTOR, ".rc-button-default")
    audio_button.click()

    # Wait for the audio file to be ready
    time.sleep(3)  # Sleep to wait for audio challenge to be loaded

    # Retrieve the audio URL from the DOM (You can find this from the "audio challenge" iframe)
    audio_element = driver.find_element(By.CSS_SELECTOR, "audio")
    audio_url = audio_element.get_attribute('src')

    driver.quit()

    # Download the audio file from the URL
    audio_data = requests.get(audio_url).content

    # Save the audio file
    audio_filename = "captcha_audio.mp3"
    with open(audio_filename, "wb") as audio_file:
        audio_file.write(audio_data)

    # Convert the audio to WAV using pydub for better compatibility
    audio = AudioSegment.from_mp3(audio_filename)
    audio.export("captcha_audio.wav", format="wav")

    # Transcribe the audio using Whisper
    model = whisper.load_model("base")  # Load the Whisper model (can use 'small' or 'large' for better accuracy)
    result = model.transcribe("captcha_audio.wav")
    return result['text'].strip()

# API route to solve reCAPTCHA
@app.route('/solve-captcha', methods=['POST'])
def solve_captcha():
    data = request.get_json()

    # Extract site_key and url from the request body
    site_key = data.get('siteKey')
    url = data.get('websiteUrl')

    # Call the function to solve the captcha
    try:
        captcha_solution = solve_recaptcha(site_key, url)
        return jsonify({"status": "success", "captchaSolution": captcha_solution})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)
