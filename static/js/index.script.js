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

    function getFileIcon(filename) {
        if (!filename.includes('.')) {
            return 'fas fa-file text-secondary';
        }

        var ext = filename.split('.').pop().toLowerCase();
        var iconMap = {
            // ================= Documents =================
            'pdf': 'fas fa-file-pdf text-danger',
            'doc': 'fas fa-file-word text-primary',
            'docx': 'fas fa-file-word text-primary',
            'odt': 'fas fa-file-word text-primary',
            'xls': 'fas fa-file-excel text-success',
            'xlsx': 'fas fa-file-excel text-success',
            'ods': 'fas fa-file-excel text-success',
            'ppt': 'fas fa-file-powerpoint text-warning',
            'pptx': 'fas fa-file-powerpoint text-warning',
            'txt': 'fas fa-file-alt text-secondary',
            'rtf': 'fas fa-file-alt text-secondary',
            'md': 'fas fa-file-alt text-secondary',
            'log': 'fas fa-file-alt text-warning',
            'csv': 'fas fa-file-csv text-success',
            'tsv': 'fas fa-file-csv text-success',
            'dat': 'fas fa-file text-secondary',

            // ================= Images =================
            'jpg': 'fas fa-file-image text-info',
            'jpeg': 'fas fa-file-image text-info',
            'png': 'fas fa-file-image text-info',
            'gif': 'fas fa-file-image text-info',
            'bmp': 'fas fa-file-image text-info',
            'webp': 'fas fa-file-image text-info',
            'svg': 'fas fa-file-image text-info',
            'tif': 'fas fa-file-image text-info',
            'tiff': 'fas fa-file-image text-info',
            'avif': 'fas fa-file-image text-info',
            'eps': 'fas fa-file-image text-info',
            'ai': 'fas fa-file-image text-info',
            'ico': 'fas fa-file-image text-warning',
            'heic': 'fas fa-file-image text-info',

            // ================= Audio =================
            'mp3': 'fas fa-file-audio text-success',
            'wav': 'fas fa-file-audio text-success',
            'ogg': 'fas fa-file-audio text-success',
            'flac': 'fas fa-file-audio text-success',
            'm4a': 'fas fa-file-audio text-success',

            // ================= Video =================
            'mp4': 'fas fa-file-video text-purple',
            'mkv': 'fas fa-file-video text-purple',
            'avi': 'fas fa-file-video text-purple',
            'mov': 'fas fa-file-video text-purple',
            'wmv': 'fas fa-file-video text-purple',
            'webm': 'fas fa-file-video text-purple',

            // ================= Archives =================
            'zip': 'fas fa-file-archive text-warning',
            'rar': 'fas fa-file-archive text-warning',
            '7z': 'fas fa-file-archive text-warning',
            'tar': 'fas fa-file-archive text-warning',
            'gz': 'fas fa-file-archive text-warning',
            'xz': 'fas fa-file-archive text-warning',
            'bz2': 'fas fa-file-archive text-warning',

            // ================= Code =================
            'html': 'fas fa-file-code text-danger',
            'htm': 'fas fa-file-code text-danger',
            'css': 'fas fa-file-code text-primary',
            'js': 'fas fa-file-code text-warning',
            'ts': 'fas fa-file-code text-info',
            'json': 'fas fa-file-code text-secondary',
            'php': 'fas fa-file-code text-purple',
            'py': 'fas fa-file-code text-success',
            'java': 'fas fa-file-code text-danger',
            'c': 'fas fa-file-code text-info',
            'cpp': 'fas fa-file-code text-info',
            'cs': 'fas fa-file-code text-info',
            'go': 'fas fa-file-code text-info',
            'rb': 'fas fa-file-code text-info',
            'sql': 'fas fa-file-code text-info',
            'sh': 'fas fa-file-code text-info',
            'xml': 'fas fa-file-code text-secondary',
            'yml': 'fas fa-file-code text-secondary',
            'yaml': 'fas fa-file-code text-secondary',
            'bat': 'fas fa-file-code text-secondary',
            'ini': 'fas fa-file-code text-secondary',
            'ps1': 'fas fa-file-code text-primary',
            'ipynb': 'fas fa-file-code text-warning',

            // ================= Fonts =================
            'ttf': 'fas fa-font text-dark',
            'otf': 'fas fa-font text-dark',
            'woff': 'fas fa-font text-dark',
            'woff2': 'fas fa-font text-dark',

            // ================= Databases =================
            'db': 'fas fa-database text-primary',
            'sqlite': 'fas fa-database text-primary',

            // ================= System =================
            'sys': 'fas fa-microchip text-danger',
            'dll': 'fas fa-cogs text-primary',
            'exe': 'fas fa-cogs text-danger',
            'tmp': 'fas fa-exclamation-circle text-muted',
            'msi': 'fas fa-cogs text-danger',

            // ================= Shortcuts =================
            'lnk': 'fas fa-link text-info',
            'wsb': 'fas fa-link text-info',

            // ================= Config/System =================
            'cfg': 'fas fa-cogs text-secondary',
            'conf': 'fas fa-cogs text-secondary',
            'env': 'fas fa-cogs text-secondary',
            'toml': 'fas fa-cogs text-secondary',

            // ================= 3D/Design =================
            'obj': 'fas fa-cube text-info',
            'stl': 'fas fa-cube text-info',
            'blend': 'fas fa-cube text-info',

            // ================= Ebooks =================
            'epub': 'fas fa-book text-primary',
            'mobi': 'fas fa-book text-primary',
        };

        return iconMap[ext] || 'fas fa-file text-secondary';
    }

    // Using type cell to decide icon
    $('#file-table tbody tr').each(function() {
        const $nameCell = $(this).find('td:eq(1) a');
        const $typeCell = $(this).find('td:eq(2)');
        const fileName = $nameCell.text().trim();
        const fileType = $typeCell.text().trim().toLowerCase();

        let iconClass;
        if (fileType === 'directory') {
            iconClass = 'fas fa-folder text-warning';
        } else {
            iconClass = getFileIcon(fileName);
        }
        $nameCell.prepend(`<i class="${iconClass} mr-2"></i>`);
    });

    // Select all files
    $('#select-all').on('change', function() {
        $('#file-table tbody tr:visible .select-file').prop('checked', this.checked);
        toggleActionButtons();
    });

    $('.select-file').on('change', function() {
        toggleActionButtons();
    });

    function toggleActionButtons() {
        const selectedCount = $('#file-table tbody tr:visible .select-file:checked').length;
        const buttons = $('#delete-selected-btn, #copy-selected-btn, #cut-selected-btn, #download-selected-btn');
        const selectedCountSpan = $('#selected-count');

        if (selectedCount > 0) {
            buttons.show().prop('disabled', false);
            selectedCountSpan.text(`${selectedCount} item${selectedCount !== 1 ? 's' : ''} selected`).show();
        } else {
            buttons.hide().prop('disabled', true);
            selectedCountSpan.hide();
        }
    }

    // Delete selected files
    $('#delete-selected-btn').on('click', function() {
        const filepaths = $('.select-file:checked').map(function() {
            return $(this).data('filepath');
        }).get();

        if (filepaths.length === 0) return;

        if (confirm(`Are you sure you want to delete ${filepaths.length} selected item(s)?`)) {
            $.ajax({
                url: '/delete_files',
                type: 'POST',
                data: { 'filepaths[]': filepaths },
                success: function(response) {
                    location.reload();
                },
                error: function(xhr, status, error) {
                    alert('Error deleting items: ' + error);
                }
            });
        }
    });

    // Copy selected files
    $('#copy-selected-btn').on('click', function() {
        const filepaths = $('.select-file:checked').map(function() {
            return $(this).data('filepath');
        }).get();

        if (filepaths.length === 0) return;

        const new_path = prompt('Enter the new path for the selected items:');
        if (new_path) {
            $.ajax({
                url: '/copy',
                type: 'POST',
                data: { 'file_paths[]': filepaths, 'new_path': new_path },
                success: function(response) {
                    if (response.success) {
                        alert('Items copied successfully!');
                        location.reload();
                    } else {
                        alert('Error: ' + response.error);
                    }
                },
                error: function(xhr, status, error) {
                    alert('Error copying items: ' + error);
                }
            });
        }
    });

    // Cut selected files
    $('#cut-selected-btn').on('click', function() {
        const filepaths = $('.select-file:checked').map(function() {
            return $(this).data('filepath');
        }).get();

        if (filepaths.length === 0) return;

        const new_path = prompt('Enter the new path for the selected items:');
        if (new_path) {
            $.ajax({
                url: '/cut',
                type: 'POST',
                data: { 'file_paths[]': filepaths, 'new_path': new_path },
                success: function(response) {
                    if (response.success) {
                        alert('Items moved successfully!');
                        location.reload();
                    } else {
                        alert('Error: ' + response.error);
                    }
                },
                error: function(xhr, status, error) {
                    alert('Error moving items: ' + error);
                }
            });
        }
    });

    // Download selected files
    $('#download-selected-btn').on('click', function() {
        const filepaths = $('.select-file:checked').map(function() {
            return $(this).data('filepath');
        }).get();

        if (filepaths.length === 0) return;

        filepaths.forEach(function(filepath) {
            const downloadUrl = '/download/' + encodeURIComponent(filepath);
            const link = document.createElement('a');
            link.href = downloadUrl;
            link.download = ''; // The browser gets the file name from the server response.
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        });
    });

    // Delete a file or folder from the actions menu
    $('#file-table').on('click', '.delete-btn', function() {
        var filepath = $(this).data('filepath');
        var itemType = $(this).data('type');
        var isDirectory = itemType === 'Directory';
        var confirmMessage = isDirectory 
            ? `Are you sure you want to delete the directory: ${filepath}? It may contain multiple files.`
            : `Are you sure you want to delete the file: ${filepath}?`;

        if (confirm(confirmMessage)) {
            $.ajax({
                url: '/delete_files',
                type: 'POST',
                data: { 'filepaths[]': [filepath] },
                success: function(response) {
                    location.reload();
                },
                error: function(xhr, status, error) {
                    alert(`Error deleting ${itemType.toLowerCase()}: ${error}`);
                }
            });
        }
    });

    // Copy file or folder from the actions menu
    $('#file-table').on('click', '.copy-btn', function() {
        var filepath = $(this).data('filepath');
        var itemType = $(this).data('type');
        var new_path = prompt(`Enter the new path for the ${itemType.toLowerCase()}:`);

        if (new_path && new_path !== filepath) {
            $.ajax({
                url: '/copy',
                type: 'POST',
                data: { 'file_paths[]': [filepath], 'new_path': new_path },
                success: function(response) {
                    if (response.success) {
                        alert(`${itemType} copied successfully!`);
                        location.reload();
                    } else {
                        alert(`Error: ${response.error}`);
                    }
                },
                error: function(xhr, status, error) {
                    alert(`Error copying ${itemType.toLowerCase()}: ${error}`);
                }
            });
        }
    });

    // Cut file or folder from the actions menu
    $('#file-table').on('click', '.cut-btn', function() {
        var filepath = $(this).data('filepath');
        var itemType = $(this).data('type');
        var new_path = prompt(`Enter the new path for the ${itemType.toLowerCase()}:`);

        if (new_path && new_path !== filepath) {
            $.ajax({
                url: '/cut',
                type: 'POST',
                data: { 'file_paths[]': [filepath], 'new_path': new_path },
                success: function(response) {
                    if (response.success) {
                        alert(`${itemType} moved successfully!`);
                        location.reload();
                    } else {
                        alert(`Error: ${response.error}`);
                    }
                },
                error: function(xhr, status, error) {
                    alert(`Error moving ${itemType.toLowerCase()}: ${error}`);
                }
            });
        }
    });

    // File Filter
    $('#filter-input').on('keyup', function() {
        var filterTerm = $(this).val().toLowerCase();
        $('#file-table tbody tr').each(function() {
            var fileName = $(this).find('td:eq(1) a').text().toLowerCase();
            if (fileName.includes(filterTerm)) {
                $(this).show();
            } else {
                $(this).hide();
            }
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
        
        'webp': 'image/webp',
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
        'log.tmp': 'text/plain',                   // Log file (temporary)
        'ini': 'text/plain',                       // Configuration file
        'sys': 'application/octet-stream',         // System file
        'cab': 'application/vnd.ms-cab-compressed',// Microsoft Cabinet file
        'msi': 'application/x-msi',                // Microsoft Installer file
        'wsb': 'application/octet-stream',         // Windows Sandbox file
        'lnk': 'application/x-ms-shortcut',        // Windows Shortcut file
        'db': 'application/x-sqlite3',             // Database file (SQLite for example)
    };
    return mimeTypes[ext] || 'application/octet-stream';
}

function updateDropdownOptions(row) {
    var filename = $(row).find('td:first-child a').text();
    var mimeType = getMimeType(filename);
    var $dropdown = $(row).find('.dropdown-menu');

    $dropdown.find('.dynamic-option').remove();

    if (mimeType.startsWith('image/') || mimeType.startsWith('video/') || mimeType.startsWith('audio/')) {
        $dropdown.append('<a href="#" class="dropdown-item dynamic-option view-btn">View</a>');
    }
}

$('#file-table tbody tr').each(function() {
    updateDropdownOptions(this);
});

$('.close').click(function() {
    $('#mediaModal').hide();
});

$(window).click(function(e) {
    if ($(e.target).is('#mediaModal')) {
        $('#mediaModal').hide();
    }
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

function checkEmpty(input) {
    if (input.value === '') {
        input.value = 'None';
    } 
    else if (input.value <= '0') {
        input.value = '0';
    }
}
