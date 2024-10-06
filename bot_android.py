import nltk
from nltk.tokenize import word_tokenize
from collections import defaultdict
import random
import os
import re
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.label import Label

# Ensure nltk punkt is downloaded
nltk.download('punkt')

# File paths for data storage
DATA_FILE = "data.txt"
DIARY_FILE = "diary.txt"
MAX_MEMORY_SIZE = 100  # Maximum number of conversations to remember

# Response templates
RESPONSE_TEMPLATES = {
    'identity': "Hi, I'm {name}! I am an AI language model developed by Tick Studios! I am hoping to pass a Turing test someday. Want to ask me something?",
    'generic': "I don't know much yet. Can you teach me something?",
}

# Feeling responses
FEELING_RESPONSES = {
    1: "It's great!",
    2: "It's not so well.",
    3: "I'm upset.",
    4: "I'm not sure how I feel.",
}

# Load memory from data.txt if it exists
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return [line.strip() for line in f.readlines()]
    return []

# Save new conversations to data.txt
def save_data(user_input, bot_response):
    with open(DATA_FILE, "a") as f:
        f.write(f"User: {user_input}\n")
        f.write(f"Bot: {bot_response}\n")

# Log the bot's diary to diary.txt
def log_diary(entry):
    with open(DIARY_FILE, "a") as f:
        f.write(f"Diary Entry: {entry}\n")

# Create a dictionary for Markov Chain
def create_markov_chain(memory):
    markov_chain = defaultdict(list)

    for sentence in memory:
        words = sentence.split()
        for i in range(len(words) - 1):
            markov_chain[words[i]].append(words[i + 1])

    return markov_chain

# Generate a sentence based on the Markov chain
def generate_sentence(markov_chain):
    if not markov_chain:
        return ""

    word = random.choice(list(markov_chain.keys()))
    sentence = [word]
    while word in markov_chain:
        word = random.choice(markov_chain[word])
        sentence.append(word)
        if len(sentence) >= 10 or word.endswith(('.', '!', '?')):  # Limit sentence length
            break
    return ' '.join(sentence)

# Extract keywords and facts from user input
def extract_keywords(user_input):
    keywords = {}
    if "my name is" in user_input.lower():
        name_match = re.search(r"my name is ([\w\s]+)", user_input, re.I)
        if name_match:
            keywords['name'] = name_match.group(1).strip()
    if "you are" in user_input.lower():
        identity_match = re.search(r"you are ([\w\s]+)", user_input, re.I)
        if identity_match:
            keywords['identity'] = identity_match.group(1).strip()
    if "learn" in user_input.lower() or "fact" in user_input.lower():
        fact_match = re.search(r"learn\.? (.+)", user_input, re.I)
        if fact_match:
            keywords['fact'] = fact_match.group(1).strip()
    if "repeat after me" in user_input.lower():
        repeat_match = re.search(r"repeat after me: (.+)", user_input, re.I)
        if repeat_match:
            keywords['repeat'] = repeat_match.group(1).strip()
    if any(feeling in user_input.lower() for feeling in ["great", "not so well", "upset", "not sure how I feel"]):
        keywords['feeling'] = True
    return keywords

# Generate a response based on the current data and user input
def generate_response(user_input, memory, user_facts):
    keywords = extract_keywords(user_input)

    # Update user facts if new information is learned
    if 'name' in keywords:
        user_facts['name'] = keywords['name']
        return f"Got it! I'll remember that your name is '{keywords['name']}'."
    if 'identity' in keywords:
        user_facts['identity'] = keywords['identity']
    if 'fact' in keywords:
        user_facts['fact'] = keywords['fact']
        return f"Got it! I'll remember that: '{keywords['fact']}'"
    if 'repeat' in keywords:
        return keywords['repeat']
    if 'feeling' in keywords:
        feeling_response = random.choice(list(FEELING_RESPONSES.values()))
        return feeling_response

    # Prepare response
    if 'name' in user_facts:
        response = RESPONSE_TEMPLATES['identity'].format(name=user_facts['name'])
    else:
        response = RESPONSE_TEMPLATES['generic']

    # Create a Markov chain and generate a response
    markov_chain = create_markov_chain(memory)
    generated_sentence = generate_sentence(markov_chain)
    response += " " + generated_sentence if generated_sentence else ""

    return response.strip()

# Memory management: Forget old data if memory exceeds the limit
def manage_memory(memory):
    if len(memory) > MAX_MEMORY_SIZE:
        memory.pop(0)  # Remove the oldest conversation
    return memory

# Kivy interface
class ChatBotApp(App):
    def build(self):
        self.memory = load_data()
        self.user_facts = {}
        
        layout = BoxLayout(orientation='vertical')
        
        self.input_box = TextInput(hint_text='Type your message here', multiline=False)
        self.input_box.bind(on_text_validate=self.on_enter)

        self.response_label = Label(text='Bot: Hello! I\'m Sky! Chat with me!')

        send_button = Button(text='Send')
        send_button.bind(on_press=self.on_button_press)

        layout.add_widget(self.response_label)
        layout.add_widget(self.input_box)
        layout.add_widget(send_button)

        return layout

    def on_enter(self, instance):
        self.process_input()

    def on_button_press(self, instance):
        self.process_input()

    def process_input(self):
        user_input = self.input_box.text
        if user_input.lower() in ['exit', 'quit']:
            App.get_running_app().stop()
            return
        
        bot_response = generate_response(user_input, self.memory, self.user_facts)

        # Save user input and bot response
        save_data(user_input, bot_response)

        # Display bot response
        self.response_label.text = f"Bot: {bot_response}"

        # Log the bot's diary entry
        log_diary(f"User said: {user_input}. I responded with: {bot_response}")

        # Teach the bot by adding the user input to memory
        self.memory.append(user_input)

        # Manage memory (forget old data if necessary)
        self.memory = manage_memory(self.memory)

        # Clear input box
        self.input_box.text = ''

if __name__ == "__main__":
    ChatBotApp().run()
