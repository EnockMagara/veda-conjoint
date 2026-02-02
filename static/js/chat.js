/**
 * Jack & Jill Chat Application
 * Handles the conversational UI flow for conjoint experiment
 * Luxury Edition with AI-like delays
 */

class ChatApp {
    constructor() {
        // DOM Elements
        this.chatMessages = document.getElementById('chatMessages');
        this.userInput = document.getElementById('userInput');
        this.sendBtn = document.getElementById('sendBtn');
        this.textInputContainer = document.getElementById('textInputContainer');
        this.choiceOptionsContainer = document.getElementById('choiceOptionsContainer');
        
        // Job Cards Overlay Elements
        this.jobCardsOverlay = document.getElementById('jobCardsOverlay');
        this.jobCardsContainer = document.getElementById('jobCardsContainer');
        this.cardA = document.getElementById('cardA');
        this.cardB = document.getElementById('cardB');
        this.cardAContent = document.getElementById('cardAContent');
        this.cardBContent = document.getElementById('cardBContent');
        this.roundNumberEl = document.getElementById('roundNumber');
        this.totalRoundsEl = document.getElementById('totalRounds');
        this.conjointPrompt = document.getElementById('conjointPrompt');
        
        // Other UI Elements
        this.progressBar = document.getElementById('progressBar');
        this.loadingOverlay = document.getElementById('loadingOverlay');
        
        // Completion Page Elements
        this.completionPage = document.getElementById('completionPage');
        this.completedRoundsEl = document.getElementById('completedRounds');
        this.completionSessionIdEl = document.getElementById('completionSessionId');
        this.completionUserNameEl = document.getElementById('completionUserName');

        // State
        this.sessionId = null;
        this.sessionSeed = null;
        this.currentQuestion = null;
        this.currentRound = 0;
        this.totalRounds = 10;
        this.cardShowTime = null;
        this.responses = {};
        this.userName = null;

        // AI-like timing configuration (longer delays for natural feel)
        this.timing = {
            typingMin: 1200,        // Min typing indicator duration
            typingMax: 2000,        // Max typing indicator duration
            betweenMessages: 600,   // Delay between messages
            afterUserMessage: 800,  // Delay after user sends message
            beforeCards: 1000,      // Delay before showing job cards
            afterCardSelect: 500,   // Delay after selecting a card
            feedbackDelay: 1500,    // Delay before next round feedback
            completionDelay: 1500   // Delay before showing completion
        };

        // Initialize
        this.init();
    }

    // Helper to get random delay within range
    getTypingDelay() {
        return this.timing.typingMin + Math.random() * (this.timing.typingMax - this.timing.typingMin);
    }

    init() {
        this.bindEvents();
        this.startSession();
    }

    bindEvents() {
        // Text input events
        this.userInput.addEventListener('input', () => this.handleInputChange());
        this.userInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !this.sendBtn.disabled) {
                this.handleSend();
            }
        });
        this.sendBtn.addEventListener('click', () => this.handleSend());

        // Job card selection
        this.cardA.addEventListener('click', () => this.handleCardSelect('A'));
        this.cardB.addEventListener('click', () => this.handleCardSelect('B'));
    }

    // ============== Session Management ==============

    async startSession() {
        this.showLoading();
        try {
            const response = await fetch('/api/session/start', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({})  // Explicitly send empty object
            });
            
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.error || `HTTP ${response.status}`);
            }
            
            const data = await response.json();

            this.sessionId = data.session_id;
            this.sessionSeed = data.session_seed;
            this.totalRounds = data.total_conjoint_rounds;
            this.currentQuestion = data.question;

            this.hideLoading();
            this.displayQuestion(data.question);
        } catch (error) {
            console.error('Error starting session:', error);
            this.hideLoading();
            this.showError('Failed to start session. Please refresh the page.');
        }
    }

    // ============== Question Display ==============

    displayQuestion(question) {
        this.currentQuestion = question;

        // Add bot message with typing effect (longer AI-like delay)
        this.showTypingIndicator();

        setTimeout(() => {
            this.removeTypingIndicator();
            this.addBotMessage(question.message);
            this.showInputForQuestion(question);
            this.updateProgress();
        }, this.getTypingDelay());
    }

    showInputForQuestion(question) {
        // Hide all input types first
        this.textInputContainer.classList.add('hidden');
        this.choiceOptionsContainer.classList.add('hidden');

        switch (question.type) {
            case 'info':
                // Auto-advance after a brief pause for reading
                setTimeout(() => this.handleInfoContinue(), 2000);
                break;

            case 'text':
                this.textInputContainer.classList.remove('hidden');
                this.userInput.placeholder = question.placeholder || 'Type your response...';
                this.userInput.value = '';
                this.userInput.focus();
                this.sendBtn.disabled = true;
                break;

            case 'choice':
                this.displayChoiceOptions(question.options);
                break;

            case 'conjoint':
                this.loadConjointRound();
                break;
        }
    }

    // ============== Choice Options Handling ==============

    displayChoiceOptions(options) {
        // Clear previous options
        this.choiceOptionsContainer.innerHTML = '';

        // Create option buttons
        options.forEach(option => {
            const btn = document.createElement('button');
            btn.className = 'choice-option-btn';
            btn.textContent = option.label;
            btn.dataset.value = option.value;
            btn.addEventListener('click', () => this.handleChoiceSelect(option.value, option.label));
            this.choiceOptionsContainer.appendChild(btn);
        });

        // Show the container
        this.choiceOptionsContainer.classList.remove('hidden');
        this.scrollToBottom();
    }

    async handleChoiceSelect(value, label) {
        // Add user message showing the selected choice
        this.addUserMessage(label);

        // Store response
        this.responses[this.currentQuestion.id] = value;

        // Hide choice options
        this.choiceOptionsContainer.classList.add('hidden');

        // Submit response
        await this.submitResponse(value);
    }

    // ============== Text Input Handling ==============

    handleInputChange() {
        const value = this.userInput.value.trim();
        this.sendBtn.disabled = value.length === 0;
    }

    async handleSend() {
        const value = this.userInput.value.trim();
        if (!value) return;

        // Add user message
        this.addUserMessage(value);

        // Store response
        this.responses[this.currentQuestion.id] = value;

        // Clear input
        this.userInput.value = '';
        this.sendBtn.disabled = true;

        // Submit response
        await this.submitResponse(value);
    }

    async submitResponse(value) {
        this.showLoading();

        try {
            const response = await fetch(`/api/session/${this.sessionId}/respond`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    question_id: this.currentQuestion.id,
                    response: value,
                    question_type: this.currentQuestion.type
                })
            });

            const data = await response.json();
            this.hideLoading();

            // Store the user's name if this was the name question
            if (this.currentQuestion.id === 'name') {
                this.userName = value;
            }

            if (data.error) {
                this.showError(data.error);
                return;
            }

            if (data.next) {
                if (data.next.complete) {
                    this.showCompletion();
                } else {
                    this.displayQuestion(data.next);
                }
            }
        } catch (error) {
            console.error('Error submitting response:', error);
            this.hideLoading();
            this.showError('Failed to submit response. Please try again.');
        }
    }

    // ============== Info Message Auto-Continue ==============

    async handleInfoContinue() {
        try {
            const response = await fetch(`/api/session/${this.sessionId}/respond`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    question_id: this.currentQuestion.id,
                    response: 'acknowledged',
                    question_type: 'info'
                })
            });

            const data = await response.json();

            if (data.next) {
                if (data.next.complete) {
                    this.showCompletion();
                } else {
                    this.displayQuestion(data.next);
                }
            }
        } catch (error) {
            console.error('Error continuing:', error);
            this.showError('Failed to continue. Please try again.');
        }
    }

    // ============== Conjoint Handling ==============

    async loadConjointRound() {
        this.currentRound = this.currentQuestion.current_round || 1;
        
        try {
            const response = await fetch(
                `/api/conjoint/${this.sessionId}/round/${this.currentRound}`
            );
            const data = await response.json();

            if (data.error) {
                this.showError(data.error);
                return;
            }

            this.displayJobCards(data);
        } catch (error) {
            console.error('Error loading conjoint round:', error);
            this.showError('Failed to load job options. Please refresh.');
        }
    }

    displayJobCards(data) {
        // Update round info in the overlay header
        this.roundNumberEl.textContent = data.round_number;
        this.totalRoundsEl.textContent = data.total_rounds;
        this.totalRounds = data.total_rounds;

        // Populate Card A
        this.cardAContent.innerHTML = this.renderCardAttributes(data.card_a.attributes);

        // Populate Card B
        this.cardBContent.innerHTML = this.renderCardAttributes(data.card_b.attributes);

        // Show the job cards overlay (full screen, scrollable)
        this.jobCardsOverlay.classList.remove('hidden');

        // Reset selection state
        this.cardA.classList.remove('selected');
        this.cardB.classList.remove('selected');

        // Record show time for response time calculation
        this.cardShowTime = Date.now();

        // Update progress
        this.updateProgress();
    }

    renderCardAttributes(attributes) {
        return attributes.map(attr => {
            // Determine if this is a long text attribute (company description or DEI statement)
            const isLongText = attr.key === 'company_description' || 
                               attr.key === 'culture_values' ||
                               attr.value.length > 100;
            const className = isLongText ? 'job-attribute long-text' : 'job-attribute';
            return `
                <div class="${className}">
                    <span class="attribute-label">${attr.label}</span>
                    <span class="attribute-value">${attr.value}</span>
                </div>
            `;
        }).join('');
    }

    async handleCardSelect(choice) {
        // Calculate response time
        const responseTime = Date.now() - this.cardShowTime;

        // Visual feedback - add selection
        this.cardA.classList.remove('selected');
        this.cardB.classList.remove('selected');
        
        if (choice === 'A') {
            this.cardA.classList.add('selected');
        } else {
            this.cardB.classList.add('selected');
        }

        // Hide overlay after selection animation and clear selection state
        setTimeout(() => {
            this.jobCardsOverlay.classList.add('hidden');
            // Clear selection after hiding so next round starts fresh
            this.cardA.classList.remove('selected');
            this.cardB.classList.remove('selected');
        }, this.timing.afterCardSelect);

        // Submit choice with delay for natural feel
        setTimeout(() => {
            this.submitConjointChoice(choice, responseTime);
        }, this.timing.afterUserMessage);
    }

    async submitConjointChoice(choice, responseTime) {
        this.showLoading();

        try {
            const response = await fetch(`/api/conjoint/${this.sessionId}/choice`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    round_number: this.currentRound,
                    choice: choice,
                    response_time_ms: responseTime
                })
            });

            const data = await response.json();
            this.hideLoading();

            if (data.error) {
                this.showError(data.error);
                return;
            }

            if (data.conjoint_complete) {
                // Conjoint phase finished - show completion page
                setTimeout(() => this.showCompletion(), this.timing.completionDelay);
            } else {
                // Load next round with brief delay
                this.currentRound = data.next_round;
                
                setTimeout(() => {
                    this.currentQuestion.current_round = this.currentRound;
                    this.loadConjointRound();
                }, this.timing.beforeCards);
            }
        } catch (error) {
            console.error('Error submitting choice:', error);
            this.hideLoading();
            this.showError('Failed to submit choice. Please try again.');
        }
    }

    // ============== Message Display ==============

    addBotMessage(text) {
        const message = document.createElement('div');
        message.className = 'message bot';
        message.innerHTML = `
            <div class="message-avatar">J</div>
            <div class="message-content">${text}</div>
        `;
        this.chatMessages.appendChild(message);
        this.scrollToBottom();
    }

    addUserMessage(text) {
        const message = document.createElement('div');
        message.className = 'message user';
        message.innerHTML = `
            <div class="message-avatar">U</div>
            <div class="message-content">${text}</div>
        `;
        this.chatMessages.appendChild(message);
        this.scrollToBottom();
    }

    showTypingIndicator() {
        const typing = document.createElement('div');
        typing.className = 'message bot';
        typing.id = 'typingIndicator';
        typing.innerHTML = `
            <div class="message-avatar">J</div>
            <div class="message-content">
                <div class="typing-indicator">
                    <span></span>
                    <span></span>
                    <span></span>
                </div>
            </div>
        `;
        this.chatMessages.appendChild(typing);
        this.scrollToBottom();
    }

    removeTypingIndicator() {
        const typing = document.getElementById('typingIndicator');
        if (typing) {
            typing.remove();
        }
    }

    showError(message) {
        this.addBotMessage(`⚠️ ${message}`);
    }

    // ============== Progress & UI Updates ==============

    updateProgress() {
        let progress = 0;

        if (this.currentQuestion) {
            const questionOrder = ['welcome', 'name', 'email', 'zip_code', 'intro_conjoint', 'conjoint', 'completion'];
            const currentIdx = questionOrder.indexOf(this.currentQuestion.id);
            
            if (this.currentQuestion.id === 'conjoint') {
                // Calculate progress within conjoint phase
                const baseProgress = (currentIdx / questionOrder.length) * 100;
                const conjointProgress = (this.currentRound / this.totalRounds) * (100 / questionOrder.length);
                progress = baseProgress + conjointProgress;
            } else {
                progress = ((currentIdx + 1) / questionOrder.length) * 100;
            }
        }

        this.progressBar.style.width = `${progress}%`;
    }

    scrollToBottom() {
        setTimeout(() => {
            this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
        }, 100);
    }

    showLoading() {
        this.loadingOverlay.classList.remove('hidden');
    }

    hideLoading() {
        this.loadingOverlay.classList.add('hidden');
    }

    showCompletion() {
        // Update completion page with session info
        this.completedRoundsEl.textContent = this.totalRounds;
        this.completionSessionIdEl.textContent = this.sessionId ? this.sessionId.substring(0, 8) + '...' : '-';
        
        // Show user's name
        if (this.userName) {
            // Get first name only
            const firstName = this.userName.split(' ')[0];
            this.completionUserNameEl.textContent = firstName;
        }
        
        // Show the completion page
        this.completionPage.classList.remove('hidden');
        
        // Set progress to 100%
        this.progressBar.style.width = '100%';
    }
}

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.chatApp = new ChatApp();
});
