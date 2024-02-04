// ==UserScript==
// @name        Reddit Submission Limiter report linkifier
// @namespace   Violentmonkey Scripts
// @match       https://reddit.com/r/*
// @grant       none
// @version     1.0
// @author      Jack Webb
// @description 04/02/2024, 13:39:46
// ==/UserScript==

(function() {
    'use strict';

    const BOT_USERNAME = 'PUT YOUR BOT USERNAME HERE'; 

    function linkifyReportReason(text) {
        const idRegex = /'([a-zA-Z0-9]{7})'/g;
        return text.replace(idRegex, (match, id) => `<a href="https://reddit.com/${id}">${id}</a>`);
    }

    function processReportReasons() {
        const reportReasons = document.querySelectorAll('.report-reason-text');

        reportReasons.forEach(reason => {
            const lines = reason.textContent.split('\n');

            lines.forEach(line => {
                if (line.trim().startsWith(BOT_USERNAME)) {
                    const updatedLine = linkifyReportReason(line);
                    reason.innerHTML = reason.innerHTML.replace(line, updatedLine);
                }
            });
        });
    }

    window.addEventListener('load', processReportReasons);
    setInterval(processReportReasons, 1000);
})();
