function csvToTable(csv) {
    const rows = csv.trim().split('\n');
    let table = '<table class="csv-table"><thead><tr>';
    const headers = rows[0].split(',');
    headers.forEach(header => {
        table += `<th>${header.trim()}</th>`;
    });
    table += '</tr></thead><tbody>';
    for (let i = 1; i < rows.length; i++) {
        if (rows[i].trim() === '') continue;
        const cells = rows[i].split(',');
        table += '<tr>';
        cells.forEach(cell => {
            table += `<td>${cell.trim()}</td>`;
        });
        table += '</tr>';
    }
    table += '</tbody></table>';
    return table;
}

function getColor(value) {
    switch (value) {
        case 1: return "red";
        case 2: return "orange";
        case 3: return "yellow";
        case 4: return "lightgreen";
        case 5: return "green";
        default: return "#e0e0e0";
    }
}

function createGauge(id, label, value) {
    const gauge = new JustGage({
        id: id,
        value: value,
        min: 1,
        max: 5,
        gaugeColor: "#e0e0e0",
        levelColors: [getColor(value)],
        pointer: true,
        hideInnerShadow: true,
        animationSpeed: 20,
        label: label,
        labelFontColor: "#000000"
    });
}

function resubmit() {
    let code = $('#code-editor').val();

    $.ajax({
        type: "POST",
        url: "/resubmit_answer",
        data: JSON.stringify({ code: code }),
        processData: false,
        contentType: "application/json",
        beforeSend: function () { 
            $("#spinner-div").show()
        },
        success: function(response) {
            console.log(response);
            session_data = response;
        },
        error: function(request, status, error) {
            console.log("Error resubmitting problem: ", error);
        },
        complete: function () { 
            $("#spinner-div").hide();
        }
    });
}

function adjustFeedbackHeight() {

    createGauge("gauge-clarity", "Clarity", session_data.clarity_score);
    createGauge("gauge-accuracy", "Accuracy", session_data.accuracy_score);
    createGauge("gauge-depth", "Depth", session_data.depth_score);

    let butColHeight = $('#score-content').outerHeight(true);
    $('.feedback-content').css('height', `calc(100vh - ${70 + 100 + butColHeight}px)`);
    
}

function cleanInput(input) {

    if (input.startsWith('"') && input.endsWith('"')) {
        input = input.slice(1, -1);
    }

    return input.split('\\n').map(line => line.trim()).filter(line => line !== '');
}

function formatDiff(original, modified) {
    const originalLines = cleanInput(original);
    const modifiedLines = cleanInput(modified);
    let formattedDiff = '';

    for (let i = 0; i < Math.max(originalLines.length, modifiedLines.length); i++) {
        const originalLine = originalLines[i] || '';
        const modifiedLine = modifiedLines[i] || '';

        if (originalLine === modifiedLine) {
            // Same lines
            formattedDiff += `<div class="line same">${originalLine}</div>\n`;
        } else if (!originalLine) {
            // New line added
            formattedDiff += `<div class="line added">+ ${modifiedLine}</div>\n`;
        } else if (!modifiedLine) {
            // Line removed
            formattedDiff += `<div class="line removed">- ${originalLine}</div>\n`;
        } else {
            // Line modified
            formattedDiff += `<div class="line removed">- ${originalLine}</div>\n`;
            formattedDiff += `<div class="line added">+ ${modifiedLine}</div>\n`;
        }
    }

    $('.diff-viewer').append(formattedDiff);
}

function checkScores() {
    if (session_data.clarity_score >= 4 && session_data.accuracy_score >= 4 && session_data.depth_score >= 4) {
        $('#complete-btn').prop('disabled', false);
    } else {
        $('#complete-btn').prop('disabled', true);
    }
}

function complete() {
    window.location.href = `/`;
}

/////////////////////////////////////////////////////////////////////////////////

function pageSetup() {
    console.log(session_data);

    var codeEditor = $('#code-editor');
    var cleanedCode = codeEditor.val().split('\n').map(function(line) {
        return line.trimStart();
    }).join('\n');
    codeEditor.val(cleanedCode);
    adjustFeedbackHeight();
    checkScores();
}

$(window).resize(adjustFeedbackHeight);

$(document).ready(function() {

    session_data.clarity_score = 4;

    pageSetup();

    const csvTable = csvToTable(session_data.dataset);
    $('#dataset-content').empty();
    $('#dataset-content').append(`${csvTable}`);

    $('#resubmit-btn').on('click', function() {
        resubmit();
    });

    $('#complete-btn').on('click', function() {
        complete();
    });

    $('#gauge-clarity').hover(
        function() {
            let feedbackContent = ``;
            if (session_data.clarity_score != 5) {
                try {
                    test
                    feedbackContent = `<p class="suggestions">${session_data.clarity}</p><div class="diff-viewer"></div>`;
                    $('#feedback-content').html(feedbackContent);
                    formatDiff(session_data.clarity_quote.trim(), session_data.clarity_diff.trim());
                } catch {
                    feedbackContent = `${session_data.clarity}<br><br>`;
                    feedbackContent += `
                        ${session_data.clarity_quote}<br><br>
                        ${session_data.clarity_diff}
                    `;
                    $('#feedback-content').html(feedbackContent);
                }
            } else {
                $('#feedback-content').html(session_data.clarity);
            }
            $('#clarity-col').css('background-color', '#f0f0f0');
            $('#accuracy-col').css('background-color', 'transparent');
            $('#depth-col').css('background-color', 'transparent');
        }
    );

    $('#gauge-accuracy').hover(
        function() {
            let feedbackContent = ``;
            if (session_data.accuracy_score != 5) {
                try {
                    test
                    feedbackContent = `<p class="suggestions">${session_data.accuracy}</p><div class="diff-viewer"></div>`;
                    $('#feedback-content').html(feedbackContent);
                    formatDiff(session_data.accuracy_quote.trim(), session_data.accuracy_diff.trim());
                } catch {
                    feedbackContent = `${session_data.accuracy}<br><br>`;
                    feedbackContent += `
                        ${session_data.accuracy_quote}<br><br>
                        ${session_data.accuracy_diff}
                    `;
                    $('#feedback-content').html(feedbackContent);
                }
            } else {
                $('#feedback-content').html(session_data.accuracy);
            }
            $('#clarity-col').css('background-color', 'transparent');
            $('#accuracy-col').css('background-color', '#f0f0f0');
            $('#depth-col').css('background-color', 'transparent');
        }
    );

    $('#gauge-depth').hover(
        function() {
            let feedbackContent = ``;
            if (session_data.depth_score != 5) {
                try {
                    test
                    feedbackContent = `<p class="suggestions">${session_data.depth}</p><div class="diff-viewer"></div>`;
                    $('#feedback-content').html(feedbackContent);
                    formatDiff(session_data.depth_quote.trim(), session_data.depth_diff.trim());
                } catch {
                    feedbackContent = `${session_data.depth}<br><br>`;
                    feedbackContent += `
                        ${session_data.depth_quote}<br><br>
                        ${session_data.depth_diff}
                    `;
                    $('#feedback-content').html(feedbackContent);
                }
            } else {
                $('#feedback-content').html(session_data.depth);
            }
            $('#clarity-col').css('background-color', 'transparent');
            $('#accuracy-col').css('background-color', 'transparent');
            $('#depth-col').css('background-color', '#f0f0f0');
        }
    );
    
});
