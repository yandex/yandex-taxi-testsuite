window.addEventListener('load', function () {
    var sendButton = document.getElementById('send');
    var loginButton = document.getElementById('login');
    var messageListDiv = document.getElementById('message-list');
    var inputMessageWrapperDiv = document.getElementById('input-message-wrapper');
    var inputMessage = document.getElementById('input-message');
    var inputNickname = document.getElementById('input-login');
    var nicknameDiv = document.getElementById('nickname');

    var username = '';

    var messageTemplateTheir = document.getElementById('message-template-their');
    messageTemplateTheir.removeAttribute('id');
    var messageTemplateYour = document.getElementById('message-template-your');
    messageTemplateYour.removeAttribute('id');

    loginButton.addEventListener('click', handleLogIn);
    inputNickname.addEventListener('keypress', function (e) {
        if (e.code === 'Enter') {
            handleLogIn();
        }
    });

    sendButton.addEventListener('click', handleSendMessage);
    inputMessage.addEventListener('keypress', function (e) {
        if (e.code === 'Enter') {
            handleSendMessage();
        }
    });

    setInterval(updateMessages, 500);

    function handleLogIn() {
        if (!inputNickname.value) {
            return;
        }
        username = inputNickname.value;
        nicknameDiv.innerText = 'Logged in as: ' + username;

        loginButton.classList.add('hide');
        inputNickname.classList.add('hide');
        nicknameDiv.classList.remove('hide');

        messageListDiv.classList.remove('hide');
        inputMessageWrapperDiv.classList.remove('hide');
        updateMessages();
        inputMessage.focus();
    }

    function handleSendMessage() {
        var messageValue = inputMessage.value;
        if (messageValue) {
            inputMessage.value = '';
            inputMessage.focus();
            sendMessage(messageValue, function () {
                updateMessages();
            });
        }
    }

    function updateMessages() {
        var xhr = new XMLHttpRequest();
        xhr.open('POST', '/messages/retrieve', true);
        xhr.setRequestHeader("Content-Type", "application/json;charset=UTF-8");
        xhr.send();

        xhr.onreadystatechange = function () {
            if (xhr.readyState !== 4) {
                return;
            }
            if (xhr.status !== 200) {
                return;
            }
            var responseBody = JSON.parse(xhr.responseText);
            var messages = responseBody['messages'];
            messageListDiv.innerHTML = '';
            var messagesHtml = '';
            for (var i = 0; i < messages.length; i++) {
                var message = messages[i];
                if (message.username === username)
                    var templateElement;
                templateElement = message.username === username
                    ? messageTemplateYour
                    : messageTemplateTheir;
                var messageHtml = templateElement.outerHTML;
                messageHtml = messageHtml.replace('{message}', message.text);
                messageHtml = messageHtml.replace('{username}', message.username);
                messageHtml = messageHtml.replace('{date}', formatIsoDate(message.created));
                messagesHtml += messageHtml;
            }
            if (messagesHtml) {
                messageListDiv.innerHTML = messagesHtml;
            }
        }
    }

    function sendMessage(message, callbackOnCompleted) {
        var xhr = new XMLHttpRequest();
        xhr.open('POST', '/messages/send', true);
        xhr.setRequestHeader("Content-Type", "application/json;charset=UTF-8");
        xhr.send(JSON.stringify({
            'username': username,
            'text': message
        }));

        xhr.onreadystatechange = function () {
            if (xhr.readyState !== 4) {
                return;
            }
            callbackOnCompleted();
        }
    }
});

function formatIsoDate(isoDate) {
    var date = new Date(isoDate);
    return padStr(date.getHours()) + ':' +
        padStr(date.getMinutes()) + ':' +
        padStr(date.getSeconds())
}

function padStr(i) {
    return (i < 10) ? "0" + i : "" + i;
}
