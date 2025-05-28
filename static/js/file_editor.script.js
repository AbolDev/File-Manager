document.addEventListener('DOMContentLoaded', function() {
    let editor;
    if (!window.isDatabase) {
        editor = CodeMirror.fromTextArea(document.getElementById('editor'), {
            lineNumbers: true,
            lineWrapping: true,
            mode: 'text/plain',
            theme: 'default'
        });

        function refreshEditor() {
            editor.setSize('100%', 'calc(80vh - 200px)');
            editor.getWrapperElement().style.maxHeight = '400px';
            editor.getWrapperElement().style.overflowY = 'auto';
            editor.refresh();
        }

        $('#saveButton').on('click', function() {
            editor.save();
            const content = $('#editor').val();
            const filePath = window.filePath;
            $.ajax({
                url: '/save_file/' + encodeURIComponent(filePath),
                type: 'POST',
                contentType: 'application/x-www-form-urlencoded',
                data: { content: content },
                success: function(response) {
                    const alertClass = response.success ? 'alert-success' : 'alert-danger';
                    const message = response.success ? response.message : response.error;
                    const alertHtml = `<div class="alert ${alertClass} alert-dismissible fade show" role="alert">
                        ${message}
                        <button type="button" class="close" data-dismiss="alert" aria-label="Close">
                            <span aria-hidden="true">×</span>
                        </button>
                    </div>`;
                    $('#flash-messages').html(alertHtml);
                    setTimeout(() => $('.alert').alert('close'), 7000);
                },
                error: function(xhr, status, error) {
                    const alertHtml = `<div class="alert alert-danger alert-dismissible fade show" role="alert">
                        Error saving file: ${xhr.responseJSON?.error || error}
                        <button type="button" class="close" data-dismiss="alert" aria-label="Close">
                            <span aria-hidden="true">×</span>
                        </button>
                    </div>`;
                    $('#flash-messages').html(alertHtml);
                    setTimeout(() => $('.alert').alert('close'), 7000);
                }
            });
        });

        $('#font-size').on('change', function() {
            editor.getWrapperElement().style.fontSize = this.value + 'px';
            refreshEditor();
            // editor.refresh();
        });

        $('#word-wrap').on('change', function() {
            editor.setOption('lineWrapping', this.checked);
            refreshEditor();
        });

        $('#language').on('change', function() {
            editor.setOption('mode', this.value);
            refreshEditor();
        });

        editor.getWrapperElement().style.fontSize = '14px';
        refreshEditor();

        const fileExtension = window.filePath.split('.').pop().toLowerCase();
        const modeMap = {
            'html': 'text/html', 'htm': 'text/html', 'css': 'text/css', 'js': 'text/javascript',
            'py': 'text/x-python', 'java': 'text/x-java', 'c': 'text/x-csrc', 'cpp': 'text/x-c++src',
            'php': 'text/x-php', 'json': 'application/json', 'md': 'text/x-markdown',
            'sh': 'application/x-shellscript', 'rb': 'text/x-ruby', 'pl': 'text/x-perl',
            'sql': 'text/x-sql', 'go': 'text/x-go', 'bash': 'text/x-bash', 'm': 'text/x-objc',
            'lua': 'text/x-lua', 'hs': 'text/x-haskell', 'kt': 'text/x-kotlin', 'dart': 'text/x-dart',
            'scala': 'text/x-scala', 'jl': 'text/x-julia', 'swift': 'text/x-swift', 'r': 'text/x-r'
        };
        if (modeMap[fileExtension]) {
            $('#language').val(modeMap[fileExtension]);
            editor.setOption('mode', modeMap[fileExtension]);
            $('#show-preview').css('display', fileExtension === 'md' || fileExtension === 'html' ? 'inline-block' : 'none');
        }

        $('#show-preview').on('click', function() {
            const fileExtension = window.filePath.split('.').pop().toLowerCase();
            let content = editor.getValue();
            if (fileExtension === 'md') content = marked(content);
            $('#previewContent').html(content);
            $('#previewModal').modal('show');
        });

        $('#copyButton').on('click', function() {
            editor.save();
            const content = $('#editor').val();
            navigator.clipboard.writeText(content).then(() => {
                alert('Code copied to clipboard!');
            }).catch(err => {
                console.error('Failed to copy: ', err);
            });
        });

        let currentSearchCursor = null;
        function searchEditor(isReplace = false) {
            const searchText = isReplace ? $('#replaceSearchText').val() : $('#searchText').val();
            const caseSensitive = isReplace ? $('#replaceCaseSensitive').prop('checked') : $('#searchCaseSensitive').prop('checked');
            const matchCountElement = isReplace ? $('#replaceMatchCount') : $('#searchMatchCount');
            editor.getAllMarks().forEach(mark => mark.clear());
            matchCountElement.text(searchText ? '' : '');
            if (!searchText) return;
            let matchCount = 0;
            currentSearchCursor = editor.getSearchCursor(searchText, null, { caseFold: !caseSensitive });
            editor.operation(() => {
                while (currentSearchCursor.findNext()) {
                    editor.markText(currentSearchCursor.from(), currentSearchCursor.to(), { className: 'cm-searching' });
                    matchCount++;
                }
                if (matchCount > 0) currentSearchCursor = editor.getSearchCursor(searchText, null, { caseFold: !caseSensitive });
            });
            matchCountElement.text(matchCount + ' match' + (matchCount !== 1 ? 'es' : ''));
        }

        function navigateSearch(direction) {
            if (!currentSearchCursor) return;
            editor.getAllMarks().forEach(mark => mark.clear());
            if (direction === 'next' && currentSearchCursor.findNext()) {
                editor.markText(currentSearchCursor.from(), currentSearchCursor.to(), { className: 'cm-searching' });
                editor.setSelection(currentSearchCursor.from(), currentSearchCursor.to());
                editor.scrollIntoView({ from: currentSearchCursor.from(), to: currentSearchCursor.to() });
            } else if (direction === 'prev' && currentSearchCursor.findPrevious()) {
                editor.markText(currentSearchCursor.from(), currentSearchCursor.to(), { className: 'cm-searching' });
                editor.setSelection(currentSearchCursor.from(), currentSearchCursor.to());
                editor.scrollIntoView({ from: currentSearchCursor.from(), to: currentSearchCursor.to() });
            } else {
                currentSearchCursor = editor.getSearchCursor($('#searchText').val() || $('#replaceSearchText').val(), null, { 
                    caseFold: !$('#searchCaseSensitive').prop('checked') 
                });
                if (direction === 'next' && currentSearchCursor.findNext()) {
                    editor.markText(currentSearchCursor.from(), currentSearchCursor.to(), { className: 'cm-searching' });
                    editor.setSelection(currentSearchCursor.from(), currentSearchCursor.to());
                    editor.scrollIntoView({ from: currentSearchCursor.from(), to: currentSearchCursor.to() });
                }
            }
        }

        function replaceEditor() {
            const searchText = $('#replaceSearchText').val();
            const replaceText = $('#replaceText').val();
            const caseSensitive = $('#replaceCaseSensitive').prop('checked');
            if (!searchText || !currentSearchCursor) return;
            editor.operation(() => {
                if (currentSearchCursor.findNext()) {
                    currentSearchCursor.replace(replaceText);
                    editor.markText(currentSearchCursor.from(), currentSearchCursor.to(), { className: 'cm-searching' });
                    editor.setSelection(currentSearchCursor.from(), currentSearchCursor.to());
                    editor.scrollIntoView({ from: currentSearchCursor.from(), to: currentSearchCursor.to() });
                }
            });
            searchEditor(true);
        }

        function replaceAllEditor() {
            const searchText = $('#replaceSearchText').val();
            const replaceText = $('#replaceText').val();
            const caseSensitive = $('#replaceCaseSensitive').prop('checked');
            if (!searchText) return;
            editor.operation(() => {
                const cursor = editor.getSearchCursor(searchText, null, { caseFold: !caseSensitive });
                while (cursor.findNext()) {
                    cursor.replace(replaceText);
                }
            });
            searchEditor(true);
        }

        $('#searchText').on('input', () => searchEditor());
        $('#searchCaseSensitive').on('change', () => searchEditor());
        $('#replaceSearchText').on('input', () => searchEditor(true));
        $('#replaceCaseSensitive').on('change', () => searchEditor(true));
        $('#searchPrevious').on('click', () => navigateSearch('prev'));
        $('#searchNext').on('click', () => navigateSearch('next'));
        $('#replacePrevious').on('click', () => navigateSearch('prev'));
        $('#replaceNext').on('click', () => navigateSearch('next'));
        $('#replaceButton').on('click', replaceEditor);
        $('#replaceAllButton').on('click', replaceAllEditor);
        $('#closeSearch').on('click', () => {
            editor.getAllMarks().forEach(mark => mark.clear());
            $('#searchBox').hide();
        });
        $('#closeReplace').on('click', () => {
            editor.getAllMarks().forEach(mark => mark.clear());
            $('#replaceBox').hide();
        });
        $('#openSearch').on('click', () => {
            $('#replaceBox').hide();
            $('#searchBox').css('display', 'flex');
            $('#searchText').val($('#replaceSearchText').val());
            $('#searchCaseSensitive').prop('checked', $('#replaceCaseSensitive').prop('checked'));
            $('#searchText').focus();
            searchEditor();
        });
        $('#openReplace').on('click', () => {
            $('#searchBox').hide();
            $('#replaceBox').css('display', 'flex');
            $('#replaceSearchText').val($('#searchText').val());
            $('#replaceCaseSensitive').prop('checked', $('#searchCaseSensitive').prop('checked'));
            $('#replaceSearchText').focus();
            searchEditor(true);
        });
        $('#searchCaseSensitive').on('change', () => {
            $('#replaceCaseSensitive').prop('checked', $('#searchCaseSensitive').prop('checked'));
            searchEditor();
        });
        $('#replaceCaseSensitive').on('change', () => {
            $('#searchCaseSensitive').prop('checked', $('#replaceCaseSensitive').prop('checked'));
            searchEditor(true);
        });
    } else {
        function loadTableData(tableName) {
            $.ajax({
                url: `/api/database/${encodeURIComponent(window.filePath)}/tables/${encodeURIComponent(tableName)}`,
                type: 'GET',
                success: function(response) {
                    if (response.success) {
                        const { columns, rows, pk_column } = response;
                        // Filtering valid columns
                        const validColumns = columns.filter(col => col && col !== 'undefined');
                        $('#tableHead').html(`<tr>${validColumns.map(col => `<th>${col}</th>`).join('')}<th>Actions</th></tr>`);
                        $('#tableBody').html(rows.map((row) => {
                            const pkValue = row[0];  // Primary key value or rowid
                            const rowData = row.slice(1, validColumns.length + 1);  // Sync with validColumns
                            return `
                                <tr data-pk-value="${pkValue}">
                                    ${rowData.map(cell => `<td>${cell ?? ''}</td>`).join('')}
                                    <td>
                                        <button class="btn btn-sm btn-warning edit-row">Edit</button>
                                        <button class="btn btn-sm btn-danger delete-row">Delete</button>
                                    </td>
                                </tr>
                            `;
                        }).join(''));
                        $('#addRowForm').html(`
                            <form id="addRowFormInner">
                                ${validColumns.map(col => `
                                    <div class="form-group">
                                        <label>${col}</label>
                                        <input type="text" name="${col}" class="form-control form-control-sm">
                                    </div>
                                `).join('')}
                                <button type="submit" class="btn btn-sm btn-primary">Submit</button>
                                <button type="button" class="btn btn-sm btn-secondary cancel-add">Cancel</button>
                            </form>
                        `);
                    } else {
                        console.error('Error loading table:', response.error);
                        $('#flash-messages').html(`<div class="alert alert-danger alert-dismissible fade show" role="alert">
                            ${response.error}
                            <button type="button" class="close" data-dismiss="alert" aria-label="Close">
                                <span aria-hidden="true">×</span>
                            </button>
                        </div>`);
                    }
                },
                error: function(xhr) {
                    console.error('Error loading table:', xhr.responseJSON?.error || 'Unknown error');
                    $('#flash-messages').html(`<div class="alert alert-danger alert-dismissible fade show" role="alert">
                        Error loading table: ${xhr.responseJSON?.error || 'Unknown error'}
                        <button type="button" class="close" data-dismiss="alert" aria-label="Close">
                            <span aria-hidden="true">×</span>
                        </button>
                    </div>`);
                }
            });
        }

        $('#tableSelect').on('change', function() {
            loadTableData(this.value);
        });

        $('#addRowButton').on('click', function() {
            $('#addRowForm').show();
            $('#editRowForm').hide();
        });

        $(document).on('click', '.cancel-add', function() {
            $('#addRowForm').hide();
        });

        $(document).on('submit', '#editRowFormInner', function(e) {
            e.preventDefault();
            const tableName = $('#tableSelect').val();
            const formData = $(this).serializeArray();
            const data = {};
            formData.forEach(item => data[item.name] = item.value);
            $.ajax({
                url: `/api/database/${encodeURIComponent(window.filePath)}/tables/${encodeURIComponent(tableName)}/update`,
                type: 'POST',
                data: data,
                success: function(response) {
                    if (response.success) {
                        $('#flash-messages').html(`<div class="alert alert-success alert-dismissible fade show" role="alert">
                            ${response.message}
                            <button type="button" class="close" data-dismiss="alert" aria-label="Close">
                                <span aria-hidden="true">×</span>
                            </button>
                        </div>`);
                        loadTableData(tableName);
                        $('#editRowForm').hide();
                    } else {
                        console.error('Update failed:', response.error);
                        $('#flash-messages').html(`<div class="alert alert-danger alert-dismissible fade show" role="alert">
                            ${response.error}
                            <button type="button" class="close" data-dismiss="alert" aria-label="Close">
                                <span aria-hidden="true">×</span>
                            </button>
                        </div>`);
                    }
                },
                error: function(xhr) {
                    console.error('Error updating row:', xhr.responseJSON?.error || 'Unknown error');
                    $('#flash-messages').html(`<div class="alert alert-danger alert-dismissible fade show" role="alert">
                        Error updating row: ${xhr.responseJSON?.error || 'Unknown error'}
                        <button type="button" class="close" data-dismiss="alert" aria-label="Close">
                            <span aria-hidden="true">×</span>
                        </button>
                    </div>`);
                }
            });
        });

        $(document).on('click', '.edit-row', function() {
            const row = $(this).closest('tr');
            const pkValue = row.data('pk-value');
            const cells = row.find('td').slice(0, -1).map((i, cell) => $(cell).text()).get();
            $.ajax({
                url: `/api/database/${encodeURIComponent(window.filePath)}/tables/${encodeURIComponent($('#tableSelect').val())}`,
                type: 'GET',
                success: function(response) {
                    if (response.success) {
                        const { columns, pk_column } = response;
                        const validColumns = columns.filter(col => col && col !== 'undefined');
                        if (validColumns.length !== cells.length) {
                            console.error('Mismatch between columns and cells:', validColumns.length, cells.length);
                            $('#flash-messages').html(`<div class="alert alert-danger alert-dismissible fade show" role="alert">
                                خطا: تعداد ستون‌ها همخوانی ندارد
                                <button type="button" class="close" data-dismiss="alert" aria-label="Close">
                                    <span aria-hidden="true">×</span>
                                </button>
                            </div>`);
                            return;
                        }
                        $('#editRowForm').html(`
                            <form id="editRowFormInner">
                                <input type="hidden" name="old_pk_value" value="${pkValue}">
                                ${validColumns.map((col, i) => `
                                    <div class="form-group">
                                        <label>${col}</label>
                                        <input type="text" name="${col}" value="${cells[i] || ''}" class="form-control form-control-sm">
                                    </div>
                                `).join('')}
                                <button type="submit" class="btn btn-sm btn-primary">Submit</button>
                                <button type="button" class="btn btn-sm btn-secondary cancel-edit">Cancel</button>
                            </form>
                        `).show();
                        $('#addRowForm').hide();
                    } else {
                        console.error('Error fetching table info:', response.error);
                        $('#flash-messages').html(`<div class="alert alert-danger alert-dismissible fade show" role="alert">
                            ${response.error}
                            <button type="button" class="close" data-dismiss="alert" aria-label="Close">
                                <span aria-hidden="true">×</span>
                            </button>
                        </div>`);
                    }
                },
                error: function(xhr) {
                    console.error('Error fetching table info:', xhr.responseJSON?.error || 'Unknown error');
                    $('#flash-messages').html(`<div class="alert alert-danger alert-dismissible fade show" role="alert">
                        خطا در دریافت اطلاعات جدول: ${xhr.responseJSON?.error || 'خطای ناشناخته'}
                        <button type="button" class="close" data-dismiss="alert" aria-label="Close">
                            <span aria-hidden="true">×</span>
                        </button>
                    </div>`);
                }
            });
        });

        $(document).on('click', '.cancel-edit', function() {
            $('#editRowForm').hide();
        });

        $(document).on('click', '.delete-row', function() {
            if (!confirm('Are you sure you want to delete this row?')) return;
            const row = $(this).closest('tr');
            const pkValue = row.data('pk-value');
            const tableName = $('#tableSelect').val();
            $.ajax({
                url: `/api/database/${encodeURIComponent(window.filePath)}/tables/${encodeURIComponent(tableName)}/delete`,
                type: 'POST',
                data: { pk_value: pkValue },  // Using pk_value
                success: function(response) {
                    if (response.success) {
                        $('#flash-messages').html(`<div class="alert alert-success alert-dismissible fade show" role="alert">
                            ${response.message}
                            <button type="button" class="close" data-dismiss="alert" aria-label="Close">
                                <span aria-hidden="true">×</span>
                            </button>
                        </div>`);
                        loadTableData(tableName);
                    } else {
                        console.error('Delete failed:', response.error);
                        $('#flash-messages').html(`<div class="alert alert-danger alert-dismissible fade show" role="alert">
                            ${response.error}
                            <button type="button" class="close" data-dismiss="alert" aria-label="Close">
                                <span aria-hidden="true">×</span>
                            </button>
                        </div>`);
                    }
                },
                error: function(xhr) {
                    console.error('Error deleting row:', xhr.responseJSON?.error || 'Unknown error');
                    $('#flash-messages').html(`<div class="alert alert-danger alert-dismissible fade show" role="alert">
                        Error deleting row: ${xhr.responseJSON?.error || 'Unknown error'}
                        <button type="button" class="close" data-dismiss="alert" aria-label="Close">
                            <span aria-hidden="true">×</span>
                        </button>
                    </div>`);
                }
            });
        });

        const themeToggle = $('#theme-toggle');
        const isDarkMode = localStorage.getItem('darkMode') === 'true';
        function enableDarkMode() {
            document.body.classList.add('dark-mode');
            themeToggle.html('<i class="fas fa-sun"></i> Toggle Light Mode');
            localStorage.setItem('darkMode', 'true');
        }
        function disableDarkMode() {
            document.body.classList.remove('dark-mode');
            themeToggle.html('<i class="fas fa-moon"></i> Toggle Dark Mode');
            localStorage.setItem('darkMode', 'false');
        }
        if (isDarkMode) enableDarkMode();
        themeToggle.on('click', function() {
            if (document.body.classList.contains('dark-mode')) {
                disableDarkMode();
            } else {
                enableDarkMode();
            }
        });

        if ($('#tableSelect').val()) {
            loadTableData($('#tableSelect').val());
        }
    }
});