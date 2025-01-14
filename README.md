# AI Phone Agent

AI Phone Agent is an interactive, voice-based chatbot designed for customer interaction over the phone. This project integrates Rasa for natural language understanding and generation, Twilio for telephony services, Flask for API management, and Vercel for deployment. The system enables dynamic conversations and can handle queries effectively using voice.

## Features
- **Voice Interaction**: Converts speech to text and text to speech for seamless communication.
- **Dynamic Conversations**: Supports context-aware conversations powered by Rasa.
- **Call Handling**: Uses Twilio to initiate and manage phone calls.
- **Web Integration**: Simple webpage interface for initiating calls.
- **Deployable**: Runs on Vercel for live demonstrations and scalability.

---
 


## Usage
1. Navigate to the deployed web interface.
2. Enter a phone number in the provided input field.
3. Click on the "Call" button.
4. Receive a call and interact with the AI agent.

---

## Project Structure
ai-phone-agent/
├── rasa_bot/           # Rasa chatbot setup
├── web/                # Web interface
├── app.py              # Flask server for API
├── requirements.txt    # Python dependencies
├── README.md           # Project documentation
└── .env                # Environment variables (not included in repo)
```

---

## Technologies Used
- **Rasa**: For intent recognition and conversational flows.
- **Twilio**: For telephony services.
- **Flask**: For API management.
- **Vercel**: For deployment of web interface.
- **JavaScript**: For the front-end web interface.

---

## Future Improvements
- **Improved NLP**: Enhance intent recognition with more training data.
- **Multilingual Support**: Add support for multiple languages.
- **Analytics Dashboard**: Track call logs and user interactions.
- **Automated Testing**: Add unit tests for Rasa and Flask components.

---

## Contribution
Contributions are welcome! Please follow these steps:
1. Fork the repository.
2. Create a new branch for your feature or bug fix.
3. Submit a pull request with a detailed explanation.


---

## Acknowledgments
- Rasa for enabling dynamic conversations.
- Twilio for seamless telephony integration.
- Vercel for easy and scalable deployment.

