# HTML template as a string
html_template = """
<!DOCTYPE html>
<html>
<head>
    <title>Text Reverser</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }
        h1 {
            color: #333;
        }
        .form-group {
            margin-bottom: 15px;
        }
        label {
            display: block;
            margin-bottom: 5px;
        }
        textarea {
            width: 100%;
            height: 100px;
            padding: 8px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-family: inherit;
            font-size: 16px;
        }
        button {
            background-color: #4CAF50;
            color: white;
            padding: 10px 15px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 16px;
        }
        button:hover {
            background-color: #45a049;
        }
        .result {
            margin-top: 20px;
            padding: 15px;
            background-color: #f8f9fa;
            border-radius: 4px;
            display: none;
        }
    </style>
</head>
<body>
    <h1>Text Reverser</h1>
    <p>Enter text below to reverse it!</p>
    
    <div class="form-group">
        <label for="text">Text to reverse:</label>
        <textarea id="text" placeholder="Type or paste your text here"></textarea>
    </div>
    <button id="reverseButton">Reverse Text</button>
    
    <div id="resultSection" class="result">
        <h3>Reversed Text:</h3>
        <pre id="reversedText"></pre>
    </div>

    <script>
        document.getElementById('reverseButton').addEventListener('click', function() {
            // Get the input text
            const text = document.getElementById('text').value;
            
            // Send the text to the server for reversing
            fetch('/reverse', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ text: text })
            })
            .then(response => response.json())
            .then(data => {
                // Update the result section with the server-reversed text
                document.getElementById('reversedText').textContent = data.reversed_text;
                document.getElementById('resultSection').style.display = 'block';
            })
            .catch(error => {
                console.error('Error:', error);
                alert('An error occurred while reversing the text.');
            });
        });
    </script>
</body>
</html>
"""
