// ===== Accordion Toggle =====
document.addEventListener('DOMContentLoaded', function() {
    const infoToggle = document.getElementById('info-toggle');
    const learnSection = document.getElementById('learn');
    
    if (infoToggle && learnSection) {
        infoToggle.addEventListener('click', function() {
            const isHidden = learnSection.getAttribute('aria-hidden') === 'true';
            learnSection.setAttribute('aria-hidden', !isHidden);
            learnSection.style.display = isHidden ? 'block' : 'none';
            infoToggle.textContent = isHidden ? 'Hide guide' : 'Learn about the tech';
        });
    }

    // ===== Accordion Headers =====
    const accHeads = document.querySelectorAll('.acc-head');
    accHeads.forEach(head => {
        head.addEventListener('click', function() {
            const body = this.nextElementSibling;
            const isOpen = body.style.display === 'block';
            
            // Close all other accordions
            document.querySelectorAll('.acc-body').forEach(b => {
                b.style.display = 'none';
            });
            
            // Toggle current
            body.style.display = isOpen ? 'none' : 'block';
            this.classList.toggle('active', !isOpen);
        });
    });

    // ===== Sample Image Button =====
    const sampleBtn = document.getElementById('sample-btn');
    const fileInput = document.getElementById('file-input');
    
    if (sampleBtn && fileInput) {
        sampleBtn.addEventListener('click', async function() {
            try {
                // Fetch a random sample image from the server
                const response = await fetch('/sample-image');
                if (response.ok) {
                    const blob = await response.blob();
                    const file = new File([blob], 'sample.jpeg', { type: 'image/jpeg' });
                    
                    // Create a DataTransfer object to set the file
                    const dataTransfer = new DataTransfer();
                    dataTransfer.items.add(file);
                    fileInput.files = dataTransfer.files;
                    
                    // Trigger preview
                    showPreview(file);
                    
                    // Show success message
                    showMessage('Sample image loaded! Click "Analyze Image" to proceed.', 'success');
                } else {
                    showMessage('Could not load sample image. Please try uploading your own image.', 'error');
                }
            } catch (error) {
                console.error('Error loading sample image:', error);
                showMessage('Error loading sample image. Please try uploading your own image.', 'error');
            }
        });
    }

    // ===== Form Submission Prevention =====
    const uploadForm = document.getElementById('upload-form');
    if (uploadForm) {
        let isSubmitting = false;
        uploadForm.addEventListener('submit', function(e) {
            if (isSubmitting) {
                e.preventDefault();
                return false;
            }
            isSubmitting = true;
            const submitBtn = uploadForm.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.textContent = 'Analyzing...';
            }
        });
    }

    // ===== File Input Preview =====
    if (fileInput) {
        fileInput.addEventListener('change', function(e) {
            if (e.target.files && e.target.files[0]) {
                showPreview(e.target.files[0]);
            }
        });
    }

    // ===== Drag and Drop =====
    const dropZone = document.getElementById('drop-zone');
    const dropText = document.getElementById('drop-text');
    const preview = document.getElementById('preview');
    
    if (dropZone && fileInput) {
        dropZone.addEventListener('click', () => fileInput.click());
        
        dropZone.addEventListener('dragover', function(e) {
            e.preventDefault();
            dropZone.classList.add('dragover');
        });
        
        dropZone.addEventListener('dragleave', function() {
            dropZone.classList.remove('dragover');
        });
        
        dropZone.addEventListener('drop', function(e) {
            e.preventDefault();
            dropZone.classList.remove('dragover');
            
            const files = e.dataTransfer.files;
            if (files.length > 0 && files[0].type.startsWith('image/')) {
                fileInput.files = files;
                showPreview(files[0]);
            } else {
                showMessage('Please drop an image file (jpg, jpeg, png)', 'error');
            }
        });
    }

    function showPreview(file) {
        if (!preview || !dropText) return;
        
        const reader = new FileReader();
        reader.onload = function(e) {
            preview.src = e.target.result;
            preview.style.display = 'block';
            dropText.style.display = 'none';
        };
        reader.readAsDataURL(file);
    }

    function showMessage(text, type) {
        // Remove existing messages
        const existing = document.querySelector('.flash-message');
        if (existing) existing.remove();
        
        const message = document.createElement('div');
        message.className = `flash-message ${type}`;
        message.textContent = text;
        message.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 12px 20px;
            background: ${type === 'success' ? '#2b8a3e' : '#c92a2a'};
            color: white;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            z-index: 1000;
            animation: slideIn 0.3s ease;
        `;
        document.body.appendChild(message);
        
        setTimeout(() => {
            message.style.animation = 'slideOut 0.3s ease';
            setTimeout(() => message.remove(), 300);
        }, 3000);
    }
});

// ===== Gauge Visualization (for result page) =====
document.addEventListener('DOMContentLoaded', function() {
    const gauge = document.getElementById('gauge');
    const finalLabel = document.getElementById('final-label');
    
    if (gauge && finalLabel) {
        const labelText = finalLabel.textContent.trim();
        let percentage = 50;
        let color = '#6b7280';
        
        if (labelText.includes('Pneumonia')) {
            percentage = 75;
            color = '#c92a2a';
        } else if (labelText.includes('Normal')) {
            percentage = 25;
            color = '#2b8a3e';
        } else {
            percentage = 50;
            color = '#b8860b';
        }
        
        gauge.style.cssText = `
            width: 200px;
            height: 200px;
            border-radius: 50%;
            background: conic-gradient(${color} 0% ${percentage}%, #e5e7eb ${percentage}% 100%);
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0 auto;
            position: relative;
        `;
        
        const inner = document.createElement('div');
        inner.style.cssText = `
            width: 150px;
            height: 150px;
            background: white;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.5rem;
            font-weight: bold;
            color: ${color};
        `;
        inner.textContent = `${percentage}%`;
        gauge.appendChild(inner);
    }

    // ===== Gemini Chat Functionality =====
    const chatForm = document.getElementById('chat-form');
    const chatInput = document.getElementById('chat-input');
    const chatMessages = document.getElementById('chat-messages');
    const chatError = document.getElementById('chat-error');
    const chatSendBtn = document.getElementById('chat-send-btn');
    
    if (chatForm && chatInput && chatMessages) {
        chatForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const message = chatInput.value.trim();
            if (!message) return;
            
            // Disable input and show loading
            chatInput.disabled = true;
            chatSendBtn.disabled = true;
            chatSendBtn.innerHTML = '<span>Sending...</span>';
            chatError.style.display = 'none';
            
            // Add user message to chat
            addMessageToChat('user', message);
            chatInput.value = '';
            
            try {
                const response = await fetch('/api/chat', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ message: message })
                });
                
                const data = await response.json();
                
                if (response.ok && data.response) {
                    // Add assistant response
                    addMessageToChat('assistant', data.response);
                } else {
                    showChatError(data.error || 'Failed to get response from AI');
                }
            } catch (error) {
                console.error('Chat error:', error);
                showChatError('Network error. Please try again.');
            } finally {
                // Re-enable input
                chatInput.disabled = false;
                chatSendBtn.disabled = false;
                chatSendBtn.innerHTML = '<span>Send</span><span class="send-icon">➤</span>';
                chatInput.focus();
            }
        });
        
        // Auto-focus chat input
        if (chatInput) {
            setTimeout(() => chatInput.focus(), 500);
        }
    }
    
    function addMessageToChat(role, content) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role}-message`;
        
        const avatar = role === 'user' ? '👤' : '🤖';
        const time = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        
        // Format content: escape HTML but preserve newlines
        const formattedContent = formatMessageContent(content);
        
        messageDiv.innerHTML = `
            <div class="message-avatar">${avatar}</div>
            <div class="message-content">
                <div class="message-text">${formattedContent}</div>
                <div class="message-time">${time}</div>
            </div>
        `;
        
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        
        // Animate message appearance
        setTimeout(() => {
            messageDiv.style.opacity = '1';
            messageDiv.style.transform = 'translateY(0)';
        }, 10);
    }
    
    function showChatError(errorText) {
        chatError.textContent = errorText;
        chatError.style.display = 'block';
        setTimeout(() => {
            chatError.style.display = 'none';
        }, 5000);
    }
    
    function formatMessageContent(text) {
        // Escape HTML to prevent XSS
        const div = document.createElement('div');
        div.textContent = text;
        let escaped = div.innerHTML;
        // Convert newlines to <br> tags
        escaped = escaped.replace(/\n/g, '<br>');
        return escaped;
    }
});

