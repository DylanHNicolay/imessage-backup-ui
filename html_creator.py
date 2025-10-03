import os
import json
from pathlib import Path
import shutil
import time
from datetime import datetime
from alive_progress import alive_it


class HtmlCreator:
    """Create a static website from the backup data."""

    def __init__(self, temp_dir: str | Path, out_dir: str | Path) -> None:
        """
        Initialize the HTML creator.
        
        Args:
            temp_dir: Directory containing the extracted backup data (chats and attachments)
            out_dir: Directory where the website will be created
        """
        self.temp_dir = Path(temp_dir)
        self.out_dir = Path(out_dir)
        self.chats_dir = Path(self.temp_dir, "chats")
        self.attachments_dir = Path(self.temp_dir, "attachments")
        
        # Create output directory structure
        os.makedirs(self.out_dir, exist_ok=True)
        os.makedirs(Path(self.out_dir, "css"), exist_ok=True)
        os.makedirs(Path(self.out_dir, "js"), exist_ok=True)
        os.makedirs(Path(self.out_dir, "attachments"), exist_ok=True)
        os.makedirs(Path(self.out_dir, "chats"), exist_ok=True)
    
    def create_website(self) -> None:
        """Generate the complete website from the backup data."""
        print("Creating website from backup data...")
        start_time = time.time()
        
        # Copy all attachments to the website directory
        self._copy_attachments()
        
        # Create individual HTML files for each chat
        chat_files = list(self.chats_dir.glob("*.json"))
        chat_data = []
        
        for chat_file in alive_it(chat_files, title="Creating chat pages"):
            with open(chat_file, 'r') as f:
                chat_json = json.load(f)
                chat_data.append(chat_json)
                self._create_chat_page(chat_json)
        
        # Create the index page with the list of all chats
        self._create_index_page(chat_data)
        
        # Create CSS and JS files
        self._create_css()
        self._create_js()
        
        print(f"Website created successfully in {(time.time() - start_time):.2f} seconds.")
        print(f"You can view the website by opening {Path(self.out_dir, 'index.html')}")
    
    def _copy_attachments(self) -> None:
        """Copy all attachments to the website directory."""
        attachments = list(self.attachments_dir.glob("*"))
        for attachment in alive_it(attachments, title="Copying attachments"):
            shutil.copy2(attachment, Path(self.out_dir, "attachments", attachment.name))
    
    def _create_chat_page(self, chat: dict) -> None:
        """Create an HTML page for a single chat."""
        chat_id = chat['chat_id']
        chat_name = chat.get('display_name') or self._get_chat_name(chat)
        participants = chat['participants']
        messages = chat['messages']
        
        # Sort messages by date
        messages.sort(key=lambda m: m['date'])
        
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Chat: {chat_name}</title>
    <link rel="stylesheet" href="../css/style.css">
</head>
<body>
    <div class="chat-container">
        <header>
            <a href="../index.html" class="back-button">&larr; Back to Chats</a>
            <h1>{chat_name}</h1>
            <div class="participants">
                {', '.join(participants.values())}
            </div>
        </header>
        <div class="messages">
"""
        
        current_date = None
        for message in messages:
            date = datetime.fromtimestamp(message['date'])
            date_str = date.strftime('%Y-%m-%d')
            time_str = date.strftime('%I:%M %p')
            
            # Add date divider if this is a new date
            if current_date != date_str:
                html += f'            <div class="date-divider">{date_str}</div>\n'
                current_date = date_str
            
            # Determine sender name
            sender_id = message['sender']
            sender_name = participants.get(sender_id, sender_id)
            if message['is_from_me']:
                sender_name = "Me"
                message_class = "message-outgoing"
            else:
                message_class = "message-incoming"
            
            # Create message HTML
            html += f'            <div class="{message_class}">\n'
            html += f'                <div class="message-header">\n'
            html += f'                    <span class="sender">{sender_name}</span>\n'
            html += f'                    <span class="time">{time_str}</span>\n'
            html += f'                </div>\n'
            html += f'                <div class="message-content">\n'
            
            # Add message text if it exists
            if message['text']:
                html += f'                    <p>{message["text"]}</p>\n'
            
            # Add attachment if it exists
            if message['attachment_path']:
                attachment_path = f"../attachments/{message['attachment_path']}"
                # Simple extension detection to determine if it's an image
                if any(message['attachment_path'].lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif']):
                    html += f'                    <img src="{attachment_path}" alt="Attachment" class="message-image">\n'
                else:
                    html += f'                    <a href="{attachment_path}" class="attachment-link">Attachment: {message["attachment_path"]}</a>\n'
            
            html += f'                </div>\n'
            html += f'            </div>\n'
        
        html += """        </div>
    </div>
    <script src="../js/script.js"></script>
</body>
</html>"""
        
        # Write the HTML file
        with open(Path(self.out_dir, "chats", f"chat_{chat_id}.html"), 'w') as f:
            f.write(html)
    
    def _create_index_page(self, chats: list) -> None:
        """Create the index page with a list of all chats."""
        # Sort chats by last message date (newest first)
        chats.sort(key=lambda c: c['last_message_date'], reverse=True)
        
        html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>iMessage Backup</title>
    <link rel="stylesheet" href="css/style.css">
</head>
<body>
    <div class="container">
        <header class="main-header">
            <h1>iMessage Backup</h1>
            <p>Your backed up conversations</p>
        </header>
        <div class="search-bar">
            <input type="text" id="chat-search" placeholder="Search chats...">
        </div>
        <div class="chat-list">
"""
        
        for chat in chats:
            chat_id = chat['chat_id']
            chat_name = chat.get('display_name') or self._get_chat_name(chat)
            last_message_date = datetime.fromtimestamp(chat['last_message_date']).strftime('%Y-%m-%d %I:%M %p')
            
            # Get the last message text (if any)
            messages = chat['messages']
            last_message = ""
            if messages:
                # Sort messages by date (newest first)
                sorted_messages = sorted(messages, key=lambda m: m['date'], reverse=True)
                # Find the last message with text
                for msg in sorted_messages:
                    if msg['text']:
                        last_message = msg['text']
                        # Truncate if too long
                        if len(last_message) > 50:
                            last_message = last_message[:50] + "..."
                        break
            
            html += f"""            <a href="chats/chat_{chat_id}.html" class="chat-item">
                <div class="chat-info">
                    <h2 class="chat-name">{chat_name}</h2>
                    <p class="chat-preview">{last_message}</p>
                </div>
                <div class="chat-date">{last_message_date}</div>
            </a>
"""
        
        html += """        </div>
    </div>
    <script src="js/script.js"></script>
</body>
</html>"""
        
        # Write the HTML file
        with open(Path(self.out_dir, "index.html"), 'w') as f:
            f.write(html)
    
    def _create_css(self) -> None:
        """Create the CSS file for the website."""
        css = """/* General Styles */
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
    line-height: 1.6;
    color: #333;
    background-color: #f5f5f5;
}

.container {
    max-width: 800px;
    margin: 0 auto;
    padding: 20px;
}

/* Header Styles */
.main-header {
    text-align: center;
    margin-bottom: 30px;
    padding: 20px 0;
    border-bottom: 1px solid #ddd;
}

.main-header h1 {
    font-size: 2.5rem;
    margin-bottom: 10px;
    color: #007aff;
}

.main-header p {
    font-size: 1.2rem;
    color: #666;
}

/* Search Bar */
.search-bar {
    margin-bottom: 20px;
}

#chat-search {
    width: 100%;
    padding: 12px;
    border: 1px solid #ddd;
    border-radius: 8px;
    font-size: 1rem;
}

/* Chat List */
.chat-list {
    display: flex;
    flex-direction: column;
    gap: 10px;
}

.chat-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 15px;
    background-color: white;
    border-radius: 10px;
    text-decoration: none;
    color: inherit;
    box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
    transition: transform 0.2s, box-shadow 0.2s;
}

.chat-item:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
}

.chat-info {
    flex: 1;
}

.chat-name {
    font-size: 1.2rem;
    margin-bottom: 5px;
    color: #333;
}

.chat-preview {
    color: #666;
    font-size: 0.9rem;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.chat-date {
    color: #999;
    font-size: 0.8rem;
}

/* Chat Page Styles */
.chat-container {
    max-width: 800px;
    margin: 0 auto;
    padding: 20px;
    background-color: white;
    min-height: 100vh;
}

header {
    padding-bottom: 15px;
    margin-bottom: 20px;
    border-bottom: 1px solid #ddd;
}

header h1 {
    font-size: 1.8rem;
    margin: 10px 0;
}

.back-button {
    color: #007aff;
    text-decoration: none;
    font-size: 1rem;
    display: inline-block;
    margin-bottom: 10px;
}

.participants {
    color: #666;
    font-size: 0.9rem;
}

/* Messages */
.messages {
    display: flex;
    flex-direction: column;
    gap: 15px;
}

.date-divider {
    text-align: center;
    color: #999;
    font-size: 0.8rem;
    margin: 15px 0;
    position: relative;
}

.date-divider::before,
.date-divider::after {
    content: "";
    display: inline-block;
    width: 40%;
    height: 1px;
    background-color: #ddd;
    vertical-align: middle;
    margin: 0 10px;
}

.message-incoming,
.message-outgoing {
    max-width: 80%;
    padding: 10px 15px;
    border-radius: 18px;
    position: relative;
}

.message-incoming {
    align-self: flex-start;
    background-color: #e5e5ea;
}

.message-outgoing {
    align-self: flex-end;
    background-color: #007aff;
    color: white;
}

.message-header {
    display: flex;
    justify-content: space-between;
    margin-bottom: 5px;
    font-size: 0.8rem;
}

.message-outgoing .message-header {
    color: rgba(255, 255, 255, 0.8);
}

.message-content p {
    margin-bottom: 8px;
}

.message-content p:last-child {
    margin-bottom: 0;
}

.message-image {
    max-width: 100%;
    border-radius: 8px;
    margin-top: 5px;
}

.attachment-link {
    display: inline-block;
    margin-top: 5px;
    color: inherit;
    text-decoration: underline;
}

/* Responsive Adjustments */
@media (max-width: 600px) {
    .chat-item {
        flex-direction: column;
        align-items: flex-start;
    }
    
    .chat-date {
        align-self: flex-end;
        margin-top: 5px;
    }
    
    .message-incoming,
    .message-outgoing {
        max-width: 90%;
    }
}
"""
        
        # Write the CSS file
        with open(Path(self.out_dir, "css", "style.css"), 'w') as f:
            f.write(css)
    
    def _create_js(self) -> None:
        """Create the JavaScript file for the website."""
        js = """// Search functionality for the chat list
document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('chat-search');
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            const searchTerm = this.value.toLowerCase();
            const chatItems = document.querySelectorAll('.chat-item');
            
            chatItems.forEach(item => {
                const chatName = item.querySelector('.chat-name').textContent.toLowerCase();
                const chatPreview = item.querySelector('.chat-preview').textContent.toLowerCase();
                
                if (chatName.includes(searchTerm) || chatPreview.includes(searchTerm)) {
                    item.style.display = 'flex';
                } else {
                    item.style.display = 'none';
                }
            });
        });
    }
    
    // Handle image loading
    const messageImages = document.querySelectorAll('.message-image');
    messageImages.forEach(img => {
        img.addEventListener('click', function() {
            this.classList.toggle('expanded');
        });
        
        // Add loading state
        img.addEventListener('load', function() {
            this.classList.add('loaded');
        });
        
        img.addEventListener('error', function() {
            this.style.display = 'none';
            const errorMsg = document.createElement('p');
            errorMsg.className = 'error-message';
            errorMsg.textContent = 'Image could not be loaded';
            this.parentNode.appendChild(errorMsg);
        });
    });
});
"""
        
        # Write the JavaScript file
        with open(Path(self.out_dir, "js", "script.js"), 'w') as f:
            f.write(js)
    
    def _get_chat_name(self, chat: dict) -> str:
        """Generate a name for the chat based on participants."""
        participants = list(chat['participants'].values())
        
        # Remove "Me" from the participants list
        if "Me" in participants:
            participants.remove("Me")
        
        if not participants:
            return "Empty Chat"
        elif len(participants) == 1:
            return participants[0]
        else:
            # For group chats, list first 3 participants
            if len(participants) > 3:
                return f"{', '.join(participants[:3])}... ({len(participants)} people)"
            else:
                return f"{', '.join(participants)}"
