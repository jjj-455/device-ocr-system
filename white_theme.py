#!/usr/bin/env python3
"""Apply white theme + layout reorder to index.html"""

filepath = 'E:/claude/web-app/index.html'

with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# ===== 1. Replace entire CSS block =====
old_style_end = '</style>'

# Insert new styles right before the closing </style> tag
# We'll replace everything between <style> and </style>
style_start = content.find('<style>')
style_end = content.find('</style>')

old_css = content[style_start:style_end + len('</style>')]

new_css = '''<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }

  body {
    font-family: -apple-system, 'Segoe UI', system-ui, sans-serif;
    background: #f0f2f5;
    min-height: 100vh;
    padding: 24px;
    display: flex;
    justify-content: center;
  }

  .container { width: 100%; max-width: 780px; }

  /* ---- Header ---- */
  .header {
    text-align: center;
    color: #1a2332;
    padding: 20px 0 16px;
  }
  .header h1 {
    font-size: 22px;
    font-weight: 700;
    letter-spacing: 0.5px;
    background: linear-gradient(135deg, #667eea, #764ba2);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
  }
  .header .sub { font-size: 13px; color: #777; margin-top: 4px; }
  .header .time { font-size: 12px; color: #999; margin-top: 2px; }

  /* ---- Cards ---- */
  .card {
    background: #fff;
    border-radius: 14px;
    padding: 20px;
    margin-bottom: 14px;
    box-shadow: 0 2px 12px rgba(0,0,0,0.06);
    transition: box-shadow 0.3s, transform 0.2s;
    border: 1px solid rgba(0,0,0,0.04);
  }
  .card:hover {
    box-shadow: 0 4px 20px rgba(0,0,0,0.1);
  }
  .card-title {
    font-size: 14px;
    font-weight: 600;
    color: #333;
    margin-bottom: 14px;
    display: flex;
    align-items: center;
    gap: 8px;
  }

  /* ---- Params Grid ---- */
  .params-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 10px;
  }
  .param-card {
    background: #f8f9fc;
    border-radius: 12px;
    padding: 14px 16px;
    border: 1px solid #eef0f4;
    transition: all 0.3s;
    position: relative;
    overflow: hidden;
  }
  .param-card::before {
    content: '';
    position: absolute;
    left: 0;
    top: 0;
    width: 3px;
    height: 100%;
    background: #667eea;
    opacity: 0;
    transition: opacity 0.3s;
  }
  .param-card:hover {
    border-color: #d0d5e0;
    box-shadow: 0 2px 8px rgba(102,126,234,0.1);
  }
  .param-card:hover::before { opacity: 1; }
  .param-label {
    font-size: 12px;
    font-weight: 500;
    color: #666;
    margin-bottom: 6px;
  }
  .param-value {
    font-size: 26px;
    font-weight: 700;
    color: #1a2332;
    font-variant-numeric: tabular-nums;
    cursor: pointer;
    transition: opacity 0.2s;
  }
  .param-value:hover { opacity: 0.7; }
  .param-value.editing { font-size: 20px; cursor: text; }
  .param-value input {
    width: 100px;
    padding: 4px 8px;
    border: 2px solid #667eea;
    border-radius: 8px;
    background: #fff;
    color: #1a2332;
    font-size: 20px;
    font-weight: 700;
    outline: none;
  }
  .param-value input:focus { border-color: #8ea4f0; box-shadow: 0 0 0 3px rgba(102,126,234,0.15); }
  .param-unit {
    font-size: 13px;
    font-weight: 400;
    color: #999;
    margin-left: 3px;
  }
  .param-time {
    font-size: 10px;
    color: #bbb;
    margin-top: 4px;
  }
  .param-card .status-dot {
    display: inline-block;
    width: 7px; height: 7px;
    border-radius: 50%;
    margin-right: 5px;
  }
  .param-card .status-dot.ok { background: #27ae60; }
  .param-card .status-dot.warn { background: #f39c12; }
  .param-card .status-dot.alert { background: #e74c3c; animation: blink 0.8s ease infinite; }
  @keyframes blink { 50% { opacity: 0.3; } }

  /* ---- Upload Area ---- */
  .upload-area {
    display: flex;
    gap: 10px;
    align-items: center;
  }
  .upload-btn {
    padding: 10px 20px;
    background: #f0f2f5;
    color: #667eea;
    border: 1.5px dashed #c5cde8;
    border-radius: 12px;
    cursor: pointer;
    font-size: 14px;
    transition: all 0.2s;
    flex: 1;
    text-align: center;
    font-weight: 500;
  }
  .upload-btn:hover {
    background: #eef1ff;
    border-color: #667eea;
    color: #5a6fd6;
  }
  .submit-btn {
    padding: 10px 24px;
    background: #667eea;
    color: #fff;
    border: none;
    border-radius: 10px;
    cursor: pointer;
    font-size: 14px;
    font-weight: 600;
    transition: all 0.2s;
    white-space: nowrap;
    letter-spacing: 0.3px;
  }
  .submit-btn:hover { background: #5a6fd6; }
  .submit-btn:active { transform: scale(0.97); }
  .submit-btn:disabled { background: #b0b8d0; cursor: not-allowed; }

  /* ---- Image Preview ---- */
  .img-preview {
    display: none;
    align-items: center;
    gap: 12px;
    padding: 12px;
    background: #f8f9fc;
    border-radius: 10px;
    margin-top: 12px;
    border: 1px solid #eef0f4;
  }
  .img-preview.show { display: flex; }
  .img-preview img {
    width: 56px; height: 56px;
    border-radius: 8px;
    object-fit: cover;
    border: 1px solid #e0e3ea;
  }
  .img-preview .file-info { flex: 1; font-size: 13px; color: #777; }
  .img-preview .file-info .name { color: #333; font-weight: 500; }
  .analyze-btn {
    padding: 6px 14px;
    background: #eef1ff;
    color: #667eea;
    border: 1px solid #d5dcf5;
    border-radius: 8px;
    cursor: pointer;
    font-size: 12px;
    font-weight: 500;
    transition: all 0.2s;
  }
  .analyze-btn:hover { background: #dfe5ff; }
  .analyze-btn:disabled { opacity: 0.5; cursor: wait; }
  .remove-img-btn {
    background: none; border: none;
    color: #bbb;
    font-size: 20px; cursor: pointer;
    padding: 2px 6px;
    transition: color 0.2s;
  }
  .remove-img-btn:hover { color: #e74c3c; }

  /* ---- Analyze Progress ---- */
  .analyze-progress {
    display: none;
    align-items: center;
    gap: 8px;
    padding: 10px 14px;
    background: #f8f9fc;
    border-radius: 10px;
    margin-top: 10px;
    font-size: 13px;
    color: #777;
    border: 1px solid #eef0f4;
  }
  .analyze-progress.show { display: flex; }
  .spinner {
    width: 14px; height: 14px;
    border: 2px solid #e0e3ea;
    border-top-color: #667eea;
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
    flex-shrink: 0;
  }
  @keyframes spin { to { transform: rotate(360deg); } }

  /* ---- Manual Input ---- */
  .manual-group { display: flex; flex-direction: column; gap: 3px; }
  .manual-group .unit-label {
    font-size: 11px; color: #888;
    padding-left: 2px;
  }
  .manual-group .unit-label .unit-tag { color: #bbb; margin-left: 2px; }
  .manual-group input {
    padding: 9px 12px; border-radius: 8px;
    border: 1.5px solid #e0e3ea;
    background: #fafbfc;
    color: #333; font-size: 13px; outline: none;
    transition: all 0.2s;
  }
  .manual-group input:focus {
    border-color: #667eea;
    box-shadow: 0 0 0 3px rgba(102,126,234,0.1);
    background: #fff;
  }
  .manual-group input::placeholder { color: #ccc; }

  /* ---- Trend Chart ---- */
  .chart-select {
    width: 100%;
    padding: 10px 14px;
    border-radius: 10px;
    border: 1.5px solid #e0e3ea;
    background: #fafbfc;
    color: #333;
    font-size: 14px;
    outline: none;
    transition: border-color 0.2s;
    margin-bottom: 12px;
  }
  .chart-select:focus { border-color: #667eea; }

  /* ---- Records List ---- */
  .record-item-wrapper {
    border-radius: 10px;
    overflow: hidden;
    margin-bottom: 6px;
    border: 1px solid #eef0f4;
    transition: border-color 0.3s;
  }
  .record-item-wrapper:hover { border-color: #d5dcf5; }
  .record-item-wrapper.editing { border-color: #667eea; background: #f5f7ff; }
  .record-item {
    padding: 12px 14px;
    cursor: pointer;
    display: flex;
    align-items: center;
    gap: 10px;
    transition: background 0.2s;
  }
  .record-item:hover { background: #fafbfc; }
  .record-item .idx {
    color: #ccc;
    font-size: 11px;
    min-width: 30px;
    font-weight: 600;
  }
  .record-item .time {
    color: #888;
    font-size: 12px;
    min-width: 130px;
    font-weight: 500;
  }
  .record-item .vals {
    flex: 1;
    font-size: 12px;
    color: #aaa;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  .record-item .vals span { color: #555; }
  .record-actions {
    display: flex;
    gap: 2px;
    flex-shrink: 0;
    opacity: 0;
    transition: opacity 0.3s;
  }
  .record-item-wrapper:hover .record-actions { opacity: 1; }
  .record-action-btn {
    width: 30px; height: 30px;
    display: flex; align-items: center; justify-content: center;
    border-radius: 8px;
    border: none;
    background: #f0f2f5;
    color: #888;
    cursor: pointer;
    font-size: 14px;
    transition: all 0.2s;
  }
  .record-action-btn:hover { background: #e0e3ea; }
  .record-action-btn.edit:hover { color: #667eea; background: #eef1ff; }
  .record-action-btn.delete:hover { color: #e74c3c; background: #fdeaea; }

  /* ---- Pagination ---- */
  .pagination { display: flex; justify-content: center; align-items: center; gap: 4px; margin-top: 14px; padding: 4px 0; }
  .page-btn {
    min-width: 34px; height: 34px;
    border-radius: 8px;
    border: 1px solid #e0e3ea;
    background: #fff;
    color: #666;
    font-size: 13px;
    cursor: pointer;
    display: flex; align-items: center; justify-content: center;
    transition: all 0.2s;
    padding: 0 8px;
  }
  .page-btn:hover { background: #eef1ff; border-color: #667eea; color: #667eea; }
  .page-btn.active { background: #667eea; border-color: #667eea; color: #fff; font-weight: 600; }
  .page-btn:disabled { opacity: 0.3; cursor: default; background: #f8f9fc; border-color: #eef0f4; color: #ccc; }
  .page-info { font-size: 12px; color: #aaa; margin: 0 8px; white-space: nowrap; }

  /* ---- Expanded Record ---- */
  .record-expanded {
    padding: 14px 16px;
    background: #f8f9fc;
    border-top: 1px solid #eef0f4;
  }
  .record-expanded .params {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 8px 20px;
  }
  .record-expanded .params .item {
    display: flex;
    justify-content: space-between;
    padding: 6px 0;
    border-bottom: 1px solid #eef0f4;
    font-size: 12px;
    color: #777;
  }
  .record-expanded .params .item .v { color: #333; font-weight: 600; }
  .record-expanded .params .item input {
    width: 90px; padding: 3px 8px; border-radius: 6px;
    border: 1.5px solid #d5dcf5;
    background: #fff;
    color: #333; font-size: 12px; font-weight: 600; text-align: right;
    outline: none;
  }
  .record-expanded .params .item input:focus { border-color: #667eea; box-shadow: 0 0 0 2px rgba(102,126,234,0.1); }

  .edit-actions { display: flex; gap: 8px; margin-top: 12px; }
  .edit-actions button {
    flex: 1; padding: 8px 12px; border-radius: 8px;
    border: none; font-size: 12px; cursor: pointer; font-weight: 600;
    transition: all 0.2s;
  }
  .edit-actions button:hover { transform: translateY(-1px); }
  .edit-actions button.save-edit { background: #667eea; color: #fff; }
  .edit-actions button.cancel-edit { background: #f0f2f5; color: #666; }
  .edit-actions button.cancel-edit:hover { background: #e0e3ea; }

  .load-to-dash-btn {
    width: 100%;
    padding: 8px;
    border-radius: 8px;
    border: 1px solid #d5dcf5;
    background: #eef1ff;
    color: #667eea;
    font-size: 12px;
    cursor: pointer;
    font-weight: 500;
    transition: all 0.2s;
    text-align: center;
  }
  .load-to-dash-btn:hover { background: #dfe5ff; border-color: #667eea; }

  /* ---- IO Buttons ---- */
  .io-row { display: flex; gap: 8px; margin-top: 12px; }
  .io-row .io-btn {
    flex: 1; padding: 9px; border-radius: 10px;
    font-size: 12px; cursor: pointer; font-weight: 500;
    transition: all 0.2s; text-align: center;
    background: #f8f9fc;
    border: 1px solid #e0e3ea;
    color: #888;
  }
  .io-row .io-btn:hover { background: #f0f2f5; }
  .io-row .io-btn.import-btn { border-color: #d5dcf5; color: #667eea; }
  .io-row .io-btn.import-btn:hover { background: #eef1ff; }
  .io-row .io-btn.export-btn { border-color: #c8e6c9; color: #388e3c; }
  .io-row .io-btn.export-btn:hover { background: #e8f5e9; }

  /* ---- Clear Button ---- */
  .clear-btn {
    margin-top: 6px;
    padding: 7px;
    background: none;
    border: 1px solid #eef0f4;
    border-radius: 10px;
    color: #aaa;
    font-size: 12px;
    cursor: pointer;
    width: 100%;
    transition: all 0.2s;
  }
  .clear-btn:hover { color: #e74c3c; border-color: #f5c6cb; background: #fdf0f0; }

  /* ---- Search Bar ---- */
  .search-bar { display: flex; gap: 8px; margin-bottom: 12px; }
  .search-bar input {
    flex: 1;
    padding: 8px 14px; border-radius: 10px;
    border: 1.5px solid #e0e3ea;
    background: #fafbfc;
    color: #555; font-size: 12px;
    outline: none; transition: all 0.2s;
  }
  .search-bar input:focus { border-color: #667eea; box-shadow: 0 0 0 3px rgba(102,126,234,0.1); background: #fff; }
  .search-bar input::placeholder { color: #ccc; }

  /* ---- Record Image ---- */
  .record-img {
    margin-bottom: 10px; text-align: center;
    background: #f0f2f5; border-radius: 8px;
    padding: 8px; overflow: hidden;
  }
  .record-img img {
    max-width: 100%; max-height: 160px;
    border-radius: 6px; object-fit: contain;
    cursor: pointer; transition: opacity 0.2s;
  }
  .record-img img:hover { opacity: 0.8; }
  .record-img .no-img {
    font-size: 11px; color: #bbb;
    padding: 16px 0;
  }

  /* ---- Toast ---- */
  .toast {
    position: fixed;
    top: 24px;
    left: 50%;
    transform: translateX(-50%) translateY(-100px);
    background: #fff;
    color: #333;
    padding: 12px 28px;
    border-radius: 12px;
    font-size: 14px;
    font-weight: 500;
    opacity: 0;
    transition: all 0.4s cubic-bezier(0.68, -0.55, 0.265, 1.55);
    z-index: 999;
    pointer-events: none;
    border: 1px solid #e0e3ea;
    box-shadow: 0 8px 32px rgba(0,0,0,0.12);
  }
  .toast.show { transform: translateX(-50%) translateY(0); opacity: 1; }

  /* ---- Import Summary Modal ---- */
  .import-summary {
    position: fixed; top: 50%; left: 50%; transform: translate(-50%,-50%);
    background: #fff; border-radius: 16px; padding: 28px 32px;
    z-index: 1000; min-width: 340px; max-width: 440px;
    border: 1px solid #e0e3ea;
    box-shadow: 0 20px 60px rgba(0,0,0,0.15);
    display: none;
  }
  .import-summary.show { display: block; }
  .import-summary h3 { color: #333; font-size: 16px; margin-bottom: 12px; }
  .import-summary .stat { font-size: 13px; color: #666; line-height: 1.8; }
  .import-summary .stat b { color: #333; }
  .import-summary .warn { color: #f39c12; font-size: 12px; margin-top: 8px; }
  .import-summary .io-actions { display: flex; gap: 10px; margin-top: 16px; }
  .import-summary .io-actions button {
    flex: 1; padding: 10px; border-radius: 10px;
    border: none; font-size: 13px; cursor: pointer; font-weight: 600;
    transition: all 0.2s;
  }
  .import-summary .io-actions button:hover { opacity: 0.85; transform: translateY(-1px); }
  .import-summary .io-actions .confirm-import { background: #667eea; color: #fff; }
  .import-summary .io-actions .cancel-import { background: #f0f2f5; color: #666; }

  /* ---- Image Viewer ---- */
  .img-viewer {
    position: fixed; top: 0; left: 0; width: 100%; height: 100%;
    background: rgba(0,0,0,0.85);
    z-index: 2000;
    display: none;
    justify-content: center;
    align-items: center;
    cursor: zoom-out;
  }
  .img-viewer.show { display: flex; }
  .img-viewer img {
    max-width: 92vw;
    max-height: 92vh;
    border-radius: 12px;
    box-shadow: 0 8px 40px rgba(0,0,0,0.5);
    object-fit: contain;
    cursor: default;
  }
  .img-viewer .close-viewer {
    position: fixed; top: 16px; right: 24px;
    color: rgba(255,255,255,0.6); font-size: 28px;
    cursor: pointer; background: none; border: none;
    transition: color 0.2s; z-index: 2001;
    line-height: 1;
  }
  .img-viewer .close-viewer:hover { color: #fff; }

  /* ---- Mobile ---- */
  @media (max-width: 500px) {
    body { padding: 12px; }
    .container { max-width: 100%; }
    .card { padding: 16px; border-radius: 12px; }
    .params-grid { grid-template-columns: 1fr; }
    .upload-area { flex-direction: column; }
    .submit-btn { width: 100%; }
    .param-value { font-size: 22px; }
    .header h1 { font-size: 18px; }
    .record-item { flex-wrap: wrap; gap: 6px; }
    .record-item .time { min-width: auto; font-size: 11px; }
    .record-item .idx { display: none; }
    .record-actions { opacity: 0.6; }
    .record-expanded .params { grid-template-columns: 1fr; }
    .pagination { gap: 2px; flex-wrap: wrap; }
    .page-btn { min-width: 30px; height: 30px; font-size: 12px; }
  }
</style>'''

content = content[:style_start] + new_css + content[style_end + len('</style>'):]

# ===== 2. Move trend chart card before records card =====
# Find the trend chart card and the records card sections
trend_start = content.find('<div class="card">\n    <div class="card-title">📈 趋势图')
records_start = content.find('<div class="card records-section">')

if trend_start > 0 and records_start > 0 and trend_start > records_start:
    print("Trend chart is after records, need to move it")
    # Extract the trend chart card
    # Find end of trend card - look for "</div>\n\n  <div class="card records-section">"
    trend_end = records_start
    trend_card = content[trend_start:trend_end]

    # Remove it from current position
    content_before_records = content[:trend_start]
    content_after_records = content[trend_end:]

    # Find the manual input card end to insert trend chart after it
    manual_end = content_before_records.rfind('</div>\n\n  </div>')
    # More specifically, find end of manual input card
    manual_card_end = content_before_records.find('class="submit-btn" id="manualApplyBtn"')
    manual_card_end = content_before_records.find('</div>', manual_card_end) + 6
    # Go to the closing </div> of the manual card
    manual_card_end = content_before_records.find('</div>', manual_card_end) + 6

    # Insert trend card after manual card
    content = content_before_records[:manual_card_end] + '\n\n' + trend_card + content_after_records

    print("Trend chart moved before records section")
else:
    print("Trend chart already in correct position or not found")

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)

print('White theme applied successfully')
