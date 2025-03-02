// ==UserScript==
// @name         Console Log Recorder
// @namespace    http://tampermonkey.net/
// @version      1.1
// @description  TODO: Repo link
// @author       Your Name
// @match        play.pokemonshowdown.com/*
// @grant        none
// ==/UserScript==

(function() {
    'use strict';

    // Array to store the logs
    var logs = [];

    function invokeGuess() {
        const logData = {
            logs: logs
        };

        fetch('http://localhost:5000/guess', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(logData)
        })
        .then(response => response.json())
        .then(data => {
            console.log('State sent successfully:', data);
        })
        .catch(error => {
            console.error('Error calling guess:', error);
        });
    }

    function recordLog(log) {
        // We only want the simulator logs, which have a specific prefix
        if (!log.startsWith('<< >battle')) {
            return;
        }
        // We only want the current battle logs; purge anything when we see an init
        if (log.includes("init|battle")) {
            logs = []
        }
        logs.push(log);
    }

    // Override console.log
    const originalLog = console.log;
    console.log = function(...args) {
        recordLog(args.join(' '));
        originalLog.apply(console, args);
    };

    // Add a button to send the logs
    const button = document.createElement('button');
    button.textContent = 'Guess';
    button.style.position = 'fixed';
    button.style.backgroundColor = '#5599FF';
    button.style.bottom = '10px';
    button.style.right = '10px';
    button.style.zIndex = 1000;
    button.addEventListener('click', invokeGuess);
    document.body.appendChild(button);
})();