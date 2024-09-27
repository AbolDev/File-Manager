document.addEventListener('DOMContentLoaded', function() {
    var themeToggle = document.getElementById('theme-toggle');
    var isDarkMode = localStorage.getItem('darkMode') === 'true';

    if (isDarkMode) {
        document.body.classList.add('dark-mode');
        themeToggle.innerHTML = '<i class="fas fa-sun"></i> Toggle Light Mode';
    } else {
        themeToggle.innerHTML = '<i class="fas fa-moon"></i> Toggle Dark Mode';
    }
    
    function enableDarkMode() {
        document.body.classList.add('dark-mode');
        themeToggle.innerHTML = '<i class="fas fa-sun"></i> Toggle Light Mode';
        localStorage.setItem('darkMode', 'true');
    }
    
    function disableDarkMode() {
        document.body.classList.remove('dark-mode');
        themeToggle.innerHTML = '<i class="fas fa-moon"></i> Toggle Dark Mode';
        localStorage.setItem('darkMode', 'false');
    }
    
    themeToggle.addEventListener('click', function() {
        if (document.body.classList.contains('dark-mode')) {
            disableDarkMode();
        } else {
            enableDarkMode();
        }
    });
});

document.addEventListener('DOMContentLoaded', function() {
    const lastModifiedElements = document.querySelectorAll('.last-modified');

    lastModifiedElements.forEach(function (element) {
        element.addEventListener('mouseenter', function () {
            const modTime = parseInt(this.getAttribute('data-modtime'));

            if (isNaN(modTime)) {
                this.setAttribute('title', 'Unknown modification time');
                return;
            }

            const now = Math.floor(Date.now() / 1000);
            let timeDiff = now - modTime;

            const days = Math.floor(timeDiff / 86400);
            timeDiff %= 86400;
            const hours = Math.floor(timeDiff / 3600);
            timeDiff %= 3600;
            const minutes = Math.floor(timeDiff / 60);
            const seconds = timeDiff % 60;

            let timeString = '';
            if (days > 0) timeString += days + " days, ";
            if (hours > 0) timeString += hours + " hours, ";
            if (minutes > 0) timeString += minutes + " minutes, ";
            timeString += seconds + " seconds ago";

            this.setAttribute('title', timeString);
        });
    });
});

function getMimeType(filename) {
    var ext = filename.split('.').pop().toLowerCase();
    var mimeTypes = {
        'txt': 'text/plain',
        'pdf': 'application/pdf',
        'doc': 'application/msword',
        'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'xls': 'application/vnd.ms-excel',
        'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'csv': 'text/csv',
        'png': 'image/png',
        'jpg': 'image/jpeg',
        'jpeg': 'image/jpeg',
        'gif': 'image/gif',
        'bmp': 'image/bmp',
        'webp': 'image/webp',
        'svg': 'image/svg+xml',
        'ico': 'image/vnd.microsoft.icon',
        'mp4': 'video/mp4',
        'avi': 'video/x-msvideo',
        'mkv': 'video/x-matroska',
        'mov': 'video/quicktime',
        'wmv': 'video/x-ms-wmv',
        'mp3': 'audio/mpeg',
        'wav': 'audio/wav',
        'ogg': 'audio/ogg',
        'flac': 'audio/flac',
        'zip': 'application/zip',
        'rar': 'application/x-rar-compressed',
        'tar': 'application/x-tar',
        'gz': 'application/gzip',
        '7z': 'application/x-7z-compressed',
        'html': 'text/html',
        'css': 'text/css',
        'js': 'application/javascript',
        'json': 'application/json',
        'xml': 'application/xml',
        'ppt': 'application/vnd.ms-powerpoint',
        'pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
        'woff': 'font/woff',
        'woff2': 'font/woff2',
        'cpp': 'text/x-c++src',
        'hpp': 'text/x-c++hdr',
        'md': 'text/markdown',
        'yaml': 'application/x-yaml',
        'toml': 'application/toml',
        'log': 'text/plain',
        'bat': 'application/x-msdos-program',
        'sh': 'application/x-sh',
        'yml': 'application/x-yaml',
        'py': 'text/x-python',
        'java': 'text/x-java-source',
        'class': 'application/java-vm',
        'log.tmp': 'text/plain',
        'ini': 'text/plain',
        'sys': 'application/octet-stream',
        'cab': 'application/vnd.ms-cab-compressed',
        'msi': 'application/x-msi',
        'wsb': 'application/octet-stream',
        'lnk': 'application/x-ms-shortcut',
        'db': 'application/x-sqlite3',
    };
    return mimeTypes[ext] || 'application/octet-stream';
}

$('#file-table tbody tr').each(function() {
    updateDropdownOptions(this);
});

function stopMediaPlayback() {
    var mediaElement = document.querySelector('#modal-media');
    if (mediaElement) {
        if (mediaElement.tagName === 'VIDEO' || mediaElement.tagName === 'AUDIO') {
            mediaElement.pause();
            mediaElement.currentTime = 0;
        }
    }
}

function closeModal() {
    $('#mediaModal').hide();
    stopMediaPlayback();
}

$('.close').click(function() {
    closeModal();
});

$(window).click(function(e) {
    if ($(e.target).is('#mediaModal')) {
        closeModal();
    }
});

$(document).keydown(function(e) {
    if (e.key === "Escape" && $('#mediaModal').is(":visible")) {
        closeModal();
    }
});
