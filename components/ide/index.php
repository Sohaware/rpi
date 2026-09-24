<?php
// ===============================
// CodyNick Device Info Page
// ===============================

// JSON file path
$jsonFile = "/device_info.json";

// Default values
$device = [
    "devicename" => "CodyNick",
    "serial_number" => "unknown",
    "production_date" => "2026-09-23",
    "description" => "CodyNick 0.7.6",
    "software_version" => "0.7.6",
    "support_link" => "https://support.codynick.com",
    "logo_path" => "/assets/logo.png"
];

// Load JSON if available
if (file_exists($jsonFile)) {
    $jsonData = json_decode(file_get_contents($jsonFile), true);

    if (is_array($jsonData)) {
        $device = array_merge($device, $jsonData);
    }
}

// Escape output safely
function e($value) {
    return htmlspecialchars($value ?? "", ENT_QUOTES, "UTF-8");
}
?>

<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title><?php echo e($device["devicename"]); ?></title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">

    <style>
        :root {
            --primary: #2563eb;
            --primary-dark: #1d4ed8;
            --bg: #f8fafc;
            --card: #ffffff;
            --text: #1e293b;
            --muted: #64748b;
            --border: #e2e8f0;
        }

        * {
            box-sizing: border-box;
        }

        body {
            margin: 0;
            min-height: 100vh;
            font-family: Arial, Tahoma, sans-serif;
            background:
                radial-gradient(circle at top left, rgba(37, 99, 235, 0.16), transparent 35%),
                linear-gradient(135deg, #f8fafc, #eef2ff);
            color: var(--text);
            display: flex;
            flex-direction: column;
        }

        .page {
            flex: 1;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 32px 16px;
        }

        .card {
            width: 100%;
            max-width: 720px;
            background: var(--card);
            border: 1px solid var(--border);
            border-radius: 28px;
            box-shadow: 0 24px 60px rgba(15, 23, 42, 0.12);
            overflow: hidden;
        }

        .header {
            padding: 36px 28px 28px;
            text-align: center;
            background: linear-gradient(135deg, #ffffff, #eff6ff);
            border-bottom: 1px solid var(--border);
        }

        .logo {
            width: 96px;
            height: 96px;
            margin: 0 auto 18px;
            border-radius: 50%;
            background: linear-gradient(135deg, var(--primary), #60a5fa);
            display: flex;
            align-items: center;
            justify-content: center;
            color: #ffffff;
            font-size: 34px;
            font-weight: bold;
            box-shadow: 0 12px 30px rgba(37, 99, 235, 0.28);
            overflow: hidden;
            padding: 12px;
        }

        .logo img {
            width: 100%;
            height: 100%;
            object-fit: contain;
        }

        .device-name {
            margin: 0;
            font-size: 30px;
            line-height: 1.2;
            font-weight: 800;
        }

        .subtitle {
            margin-top: 8px;
            color: var(--muted);
            font-size: 15px;
        }

        .content {
            padding: 28px;
        }

        .info-grid {
            display: grid;
            grid-template-columns: 1fr;
            gap: 14px;
        }

        .info-box {
            border: 1px solid var(--border);
            border-radius: 18px;
            padding: 14px 18px;
            background: #ffffff;
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .label {
            font-size: 13px;
            color: var(--muted);
            font-weight: bold;
            text-transform: uppercase;
            letter-spacing: 0.04em;
            white-space: nowrap;
        }

        .label::after {
            content: ":";
        }

        .value {
            font-size: 17px;
            line-height: 1.5;
            flex: 1;
        }

        .links {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 14px;
            margin-bottom: 26px;
        }

        .link-card {
            text-decoration: none;
            color: var(--text);
            border: 1px solid var(--border);
            border-radius: 18px;
            padding: 18px;
            background: #f8fafc;
            transition: all 0.2s ease;
        }

        .link-card:hover {
            transform: translateY(-3px);
            border-color: var(--primary);
            box-shadow: 0 12px 28px rgba(15, 23, 42, 0.10);
            background: #ffffff;
        }

        .link-title {
            font-weight: 800;
            font-size: 16px;
            margin-bottom: 5px;
            color: var(--primary-dark);
        }

        .link-desc {
            font-size: 13px;
            color: var(--muted);
            line-height: 1.4;
        }

        footer {
            text-align: center;
            padding: 18px;
            color: var(--muted);
            font-size: 13px;
        }

        @media (max-width: 560px) {
            .logo img {
            width: 100%;
            height: 100%;
            object-fit: contain;
        }

        .device-name {
                font-size: 24px;
            }

            .links {
                grid-template-columns: 1fr;
            }

            .content {
                padding: 22px;
            }
        }
    </style>
</head>

<body>

<div class="page">
    <main class="card">

        <section class="header">
            <div class="logo">
                <img src="<?php echo e($device["logo_path"]); ?>" alt="CodyNick Logo" onerror="this.style.display='none'; this.parentNode.textContent='CN';">
            </div>
            <h1 class="device-name"><?php echo e($device["devicename"]); ?></h1>
            <div class="subtitle">CodyNick On-Device Information Page</div>
        </section>

        <section class="content">

            <div class="links">
                <a class="link-card" href="/code">
                    <div class="link-title">On-Device IDE</div>
                    <div class="link-desc">Open the local coding environment.</div>
                </a>

                <a class="link-card" href="/dashboard">
                    <div class="link-title">On-Device Dashboard</div>
                    <div class="link-desc">View live controls and device data.</div>
                </a>

                <a class="link-card" href="/docs">
                    <div class="link-title">On-Device Documentation</div>
                    <div class="link-desc">Read local guides and instructions.</div>
                </a>

                <a class="link-card" href="/teachers">
                    <div class="link-title">Teacher Guides</div>
                    <div class="link-desc">Open protected presenter material.</div>
                </a>

                <a class="link-card" href="/gadget-tests">
                    <div class="link-title">Gadget Tests</div>
                    <div class="link-desc">Run public hardware checks and copy test code.</div>
                </a>

                <a class="link-card" href="<?php echo e($device["support_link"]); ?>" target="_blank" rel="noopener">
                    <div class="link-title">Support</div>
                    <div class="link-desc">Get help, updates, and support resources.</div>
                </a>
            </div>

            <div class="info-grid">
                <div class="info-box">
                    <div class="label">Serial Number</div>
                    <div class="value"><?php echo e($device["serial_number"]); ?></div>
                </div>

                <div class="info-box">
                    <div class="label">Production Date</div>
                    <div class="value"><?php echo e($device["production_date"]); ?></div>
                </div>

                <div class="info-box">
                    <div class="label">Software Version</div>
                    <div class="value"><?php echo e($device["software_version"]); ?></div>
                </div>

                <div class="info-box">
                    <div class="label">Device Description</div>
                    <div class="value"><?php echo e($device["description"]); ?></div>
                </div>
            </div>

        </section>

    </main>
</div>

<footer>
    © <?php echo date("Y"); ?> CodyNick. All rights reserved.
</footer>

</body>
</html>
