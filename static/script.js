// =============================
// SEND MESSAGE
// =============================

async function sendMessage() {

    const messageInput = document.getElementById("message");
    const chatBox = document.getElementById("chat-box");

    const message = messageInput.value.trim();

    if (message === "") return;

    // Remove welcome message
    const welcomeMessage = document.querySelector(".welcome-message");

    if (welcomeMessage) {
        welcomeMessage.remove();
    }

    // Show user's message
    chatBox.innerHTML += `
        <div class="user-message">
            <b>You:</b>
            <p>${escapeHTML(message)}</p>
        </div>
    `;

    messageInput.value = "";

    // Loading message
    chatBox.innerHTML += `
        <div class="ai-message" id="loading">
            <b>Gemini:</b>
            <p>Thinking...</p>
        </div>
    `;

    chatBox.scrollTop = chatBox.scrollHeight;

    try {

        const response = await fetch("/chat", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                message: message
            })
        });

        const data = await response.json();

        const loading = document.getElementById("loading");

        if (loading) {
            loading.remove();
        }

        const formattedReply =
            formatGeminiResponse(data.reply);

        chatBox.innerHTML += `
            <div class="ai-message">
                <b>Gemini:</b>
                <div class="gemini-response">
                    ${formattedReply}
                </div>
            </div>
        `;

        chatBox.scrollTop = chatBox.scrollHeight;

    } catch (error) {

        const loading = document.getElementById("loading");

        if (loading) {
            loading.remove();
        }

        chatBox.innerHTML += `
            <div class="ai-message">
                <b>Error:</b>
                <p>Something went wrong. Please try again.</p>
            </div>
        `;

        console.error(error);
    }
}


// =============================
// FORMAT GEMINI RESPONSE
// =============================

function formatGeminiResponse(text) {

    if (!text) {
        return "No response received.";
    }

    let formatted = escapeHTML(text);

    // ---------------------------------
    // Fix escaped bullets
    // ---------------------------------

 formatted = formatted.replace(/\\\*\s+/g, "• ");
formatted = formatted.replace(/^\s*\\\*\s+/gm, "• ");
formatted = formatted.replace(/^\s*-\s+/gm, "• ");

    // ---------------------------------
    // Code blocks
    // ---------------------------------

    formatted = formatted.replace(
        /```([\s\S]*?)```/g,
        function (match, code) {
            return `<pre><code>${code.trim()}</code></pre>`;
        }
    );


    // ---------------------------------
    // Headings
    // ---------------------------------

    formatted = formatted.replace(
        /^####\s+(.*)$/gm,
        "<h4>$1</h4>"
    );

    formatted = formatted.replace(
        /^###\s+(.*)$/gm,
        "<h3>$1</h3>"
    );

    formatted = formatted.replace(
        /^##\s+(.*)$/gm,
        "<h2>$1</h2>"
    );

    formatted = formatted.replace(
        /^#\s+(.*)$/gm,
        "<h2>$1</h2>"
    );


    // ---------------------------------
    // Horizontal lines
    // ---------------------------------

    formatted = formatted.replace(
        /^\s*-{3,}\s*$/gm,
        "<hr>"
    );


    // ---------------------------------
    // Bold
    // ---------------------------------

    formatted = formatted.replace(
        /\*\*(.*?)\*\*/g,
        "<strong>$1</strong>"
    );


    // ---------------------------------
    // Italic
    // ---------------------------------

    formatted = formatted.replace(
        /(?<!\*)\*([^*\n]+)\*(?!\*)/g,
        "<em>$1</em>"
    );


    // ---------------------------------
    // Convert Markdown table
    // ---------------------------------

    const lines = formatted.split("\n");

    let result = [];

    let i = 0;

    while (i < lines.length) {

        const currentLine = lines[i].trim();

        // Detect table header
        if (
            currentLine.includes("|") &&
            i + 1 < lines.length &&
            lines[i + 1].includes("|")
        ) {

            const separatorLine =
                lines[i + 1].trim();

            const separatorCells =
                separatorLine
                    .split("|")
                    .map(cell => cell.trim())
                    .filter(cell => cell !== "");

            const validSeparator =
                separatorCells.length > 0 &&
                separatorCells.every(cell =>
                    /^:?-{3,}:?$/.test(cell)
                );

            if (validSeparator) {

                const headers =
                    currentLine
                        .split("|")
                        .map(cell => cell.trim())
                        .filter(cell => cell !== "");

                let tableHTML = `
                    <div class="table-wrapper">
                        <table>
                            <thead>
                                <tr>
                `;

                headers.forEach(header => {
                    tableHTML += `<th>${header}</th>`;
                });

                tableHTML += `
                                </tr>
                            </thead>
                            <tbody>
                `;

                i += 2;

                while (
                    i < lines.length &&
                    lines[i].includes("|")
                ) {

                    const cells =
                        lines[i]
                            .split("|")
                            .map(cell => cell.trim())
                            .filter(cell => cell !== "");

                    if (cells.length === 0) {
                        break;
                    }

                    tableHTML += "<tr>";

                    cells.forEach(cell => {
                        tableHTML += `<td>${cell}</td>`;
                    });

                    tableHTML += "</tr>";

                    i++;
                }

                tableHTML += `
                            </tbody>
                        </table>
                    </div>
                `;

                result.push(tableHTML);

                continue;
            }
        }

        result.push(lines[i]);

        i++;
    }

    formatted = result.join("\n");


    // ---------------------------------
    // Bullet Lists
    // ---------------------------------

    formatted = formatted.replace(
        /(?:^|\n)((?:(?:•)\s+.*(?:\n|$))+)/g,
        function (match, list) {

            const items = list
                .trim()
                .split("\n")
                .filter(line => line.trim() !== "")
                .map(line => {

                    const item =
                        line.replace(/^•\s+/, "");

                    return `<li>${item}</li>`;
                })
                .join("");

            return `<ul>${items}</ul>`;
        }
    );


    // ---------------------------------
    // Numbered Lists
    // ---------------------------------

    formatted = formatted.replace(
        /(?:^|\n)((?:\d+\.\s+.*(?:\n|$))+)/g,
        function (match, list) {

            const items = list
                .trim()
                .split("\n")
                .filter(line => line.trim() !== "")
                .map(line => {

                    const item =
                        line.replace(/^\d+\.\s+/, "");

                    return `<li>${item}</li>`;
                })
                .join("");

            return `<ol>${items}</ol>`;
        }
    );


    // ---------------------------------
    // Clean excessive blank lines
    // ---------------------------------

    formatted = formatted.replace(
        /\n[ \t]*\n[ \t]*\n+/g,
        "\n\n"
    );


    // ---------------------------------
    // Remaining line breaks
    // ---------------------------------

    formatted = formatted.replace(
        /\n/g,
        "<br>"
    );


    // ---------------------------------
    // Remove unnecessary BR tags
    // ---------------------------------

    formatted = formatted.replace(
        /<br>\s*(<h[234]>)/g,
        "$1"
    );

    formatted = formatted.replace(
        /(<\/h[234]>)\s*<br>/g,
        "$1"
    );

    formatted = formatted.replace(
        /<br>\s*(<ul>)/g,
        "$1"
    );

    formatted = formatted.replace(
        /(<\/ul>)\s*<br>/g,
        "$1"
    );

    formatted = formatted.replace(
        /<br>\s*(<ol>)/g,
        "$1"
    );

    formatted = formatted.replace(
        /(<\/ol>)\s*<br>/g,
        "$1"
    );

    formatted = formatted.replace(
        /<br>\s*(<hr>)/g,
        "$1"
    );

    formatted = formatted.replace(
        /(<hr>)\s*<br>/g,
        "$1"
    );

    formatted = formatted.replace(
        /<br>\s*(<div class="table-wrapper">)/g,
        "$1"
    );

    formatted = formatted.replace(
        /(<\/div>)\s*<br>/g,
        "$1"
    );

    return formatted;
}


// =============================
// ESCAPE HTML
// =============================

function escapeHTML(text) {

    const div = document.createElement("div");

    div.textContent = text;

    return div.innerHTML;
}


// =============================
// ENTER KEY
// =============================

function handleKeyPress(event) {

    if (event.key === "Enter") {

        event.preventDefault();

        sendMessage();
    }
}


// =============================
// SPEECH TO TEXT
// =============================

function startListening() {

    if (
        !("webkitSpeechRecognition" in window) &&
        !("SpeechRecognition" in window)
    ) {

        alert(
            "Speech Recognition is not supported in this browser."
        );

        return;
    }

    const SpeechRecognition =
        window.SpeechRecognition ||
        window.webkitSpeechRecognition;

    const recognition =
        new SpeechRecognition();

    recognition.lang = "en-US";

    recognition.interimResults = false;

    recognition.maxAlternatives = 1;

    recognition.start();


    recognition.onstart = function () {

        console.log("Listening...");
    };


    recognition.onresult = function (event) {

        const transcript =
            event.results[0][0].transcript;

        document.getElementById("message").value =
            transcript;

        sendMessage();
    };


    recognition.onerror = function (event) {

        console.error(
            "Speech Recognition Error:",
            event.error
        );

        alert(
            "Speech Recognition Error: " +
            event.error
        );
    };


    recognition.onend = function () {

        console.log(
            "Speech recognition ended."
        );
    };
}