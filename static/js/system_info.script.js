// Function to convert bytes to human-readable format
function formatBytes(bytes, decimals = 2) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const dm = decimals < 0 ? 0 : decimals;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
}

// Function to fetch and update system information
async function fetchSystemInfo() {
    try {
        const response = await fetch('/api/system-info');
        if (!response.ok) throw new Error('Network response was not ok.');
        const data = await response.json();
        
        document.getElementById('system').innerText = data.system_information.system;
        document.getElementById('node-name').innerText = data.system_information.node_name;
        document.getElementById('release').innerText = data.system_information.release;
        document.getElementById('version').innerText = data.system_information.version;
        document.getElementById('machine').innerText = data.system_information.machine;
        document.getElementById('processor').innerText = data.system_information.processor;
        document.getElementById('boot-time').innerText = data.system_information.boot_time;
    } catch (error) {
        console.error('Error fetching system information:', error);
    }
}

// Function to fetch and update CPU, RAM, Disk usage
async function fetchUsage() {
    try {
        const response = await fetch('/api/system-info');
        if (!response.ok) throw new Error('Network response was not ok.');
        const data = await response.json();

        // Update CPU usage
        const cpuPath = document.getElementById('cpu-path');
        const cpuText = document.getElementById('cpu-text');
        const cpuPercentage = data.cpu_info.total_cpu_usage;
        cpuPath.style.strokeDasharray = `${(cpuPercentage / 100) * 295.31}, 295.31`;
        cpuText.innerText = `${cpuPercentage.toFixed(2)}%`;
        document.getElementById('cpu-cores').innerText = data.cpu_info.total_cores;

        // Update RAM usage
        const ramPath = document.getElementById('ram-path');
        const ramText = document.getElementById('ram-text');
        const ramUsed = formatBytes(data.memory_information.used);
        const ramTotal = formatBytes(data.memory_information.total);
        const ramPercentage = data.memory_information.percentage;
        ramPath.style.strokeDasharray = `${(ramPercentage / 100) * 295.31}, 295.31`;
        ramText.innerText = `${ramPercentage.toFixed(2)}%`;
        document.getElementById('ram-used').innerText = ramUsed;
        document.getElementById('ram-total').innerText = ramTotal;

        // Update Disk usage
        const diskPath = document.getElementById('disk-path');
        const diskText = document.getElementById('disk-text');
        const diskUsed = formatBytes(data.disk_information[0].used);  // Assume only one disk for simplicity
        const diskTotal = formatBytes(data.disk_information[0].total_size);
        const diskPercentage = data.disk_information[0].percentage;
        diskPath.style.strokeDasharray = `${(diskPercentage / 100) * 295.31}, 295.31`;
        diskText.innerText = `${diskPercentage.toFixed(2)}%`;
        document.getElementById('disk-used').innerText = diskUsed;
        document.getElementById('disk-total').innerText = diskTotal;

    } catch (error) {
        console.error('Error fetching usage data:', error);
    }
}

// Function to fetch and update network information
async function fetchNetworkInfo() {
    try {
        const response = await fetch('/api/network-info');
        if (!response.ok) throw new Error('Network response was not ok.');
        const data = await response.json();

        // Update total upload and download
        const totalUpload = formatBytes(data.network_information.io_stats.total_bytes_sent, 2);
        const totalDownload = formatBytes(data.network_information.io_stats.total_bytes_received, 2);
        document.getElementById('total-upload').innerText = `Out: ${totalUpload}`;
        document.getElementById('total-download').innerText = `In: ${totalDownload}`;

        // Update current upload and download speed
        const currentUpload = formatBytes(data.network_information.io_stats.bytes_sent, 2) + '/s';
        const currentDownload = formatBytes(data.network_information.io_stats.bytes_received, 2) + '/s';
        document.getElementById('current-upload').innerText = `Up: ${currentUpload}`;
        document.getElementById('current-download').innerText = `Down: ${currentDownload}`;

    } catch (error) {
        console.error('Error fetching network information:', error);
    }
}

// Function to fetch all data
async function fetchData() {
    await fetchSystemInfo();
    await fetchUsage();
    await fetchNetworkInfo();
}

// Fetch data on page load and refresh every 3 seconds
fetchData();
setInterval(fetchData, 3000);
