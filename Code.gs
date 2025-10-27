// -------- Script Properties Helper --------
function getConfig() {
  const scriptProperties = PropertiesService.getScriptProperties();
  return {
    pat: scriptProperties.getProperty("GITHUB_PAT"),
    url: scriptProperties.getProperty("DISPATCH_URL"),
  };
}

// -------- Sheets management --------
let _doc, _ss = {};
function getss(sheet) {
  const s = String(sheet);
  if (!_ss[s]) {
    if (!_doc) { _doc = SpreadsheetApp.getActiveSpreadsheet() }
    _ss[s] = _doc.getSheetByName(s);
    if (!_ss[s]){
      const template = _doc.getSheetByName('log');
      _ss[s] = _doc.insertSheet(s, {template: template});
    }
  }
  return _ss[s];
}

// -------- File changes detection --------
function detectFile(update, path){
  return update.commits.some(commit => {
    const added = commit.added && commit.added.includes(path);
    const modified = commit.modified && commit.modified.includes(path);
    return added || modified;
  });
}

// -------- Check if commits should skip execution --------
function shouldSkipExecution(update) {
  // Check if any commit has [skip-execute] marker
  const hasSkipMarker = update.commits.some(commit => 
    commit.message && commit.message.includes('[skip-execute]')
  );
  
  if (hasSkipMarker) return true;
  
  // Check if ALL changes across ALL commits are ONLY to tcp.json
  let hasTcpJsonChange = false;
  let hasOtherChanges = false;
  
  update.commits.forEach(commit => {
    const allFiles = [
      ...(commit.added || []),
      ...(commit.modified || []),
      ...(commit.removed || [])
    ];
    
    allFiles.forEach(file => {
      if (file === 'test/tcp.json') {
        hasTcpJsonChange = true;
      } else {
        hasOtherChanges = true;
      }
    });
  });
  
  // Skip if ONLY tcp.json changed (no other files)
  return hasTcpJsonChange && !hasOtherChanges;
}

// -------- Trigger dispatch workflow --------
function triggerDispatches(event, branch) {
  const config = getConfig();
  if (!config.pat || !config.url) {
    getss(branch).appendRow([new Date(), "FATAL: Missing GITHUB_PAT or DISPATCH_URL in script properties."]);
    return;
  }
  try {
    const response = UrlFetchApp.fetch(config.url, {
      method: 'post',
      contentType: 'application/json',
      headers: {
        'Authorization': 'Bearer ' + config.pat,
        'Accept': 'application/vnd.github.v3+json'
      },
      payload: JSON.stringify({
        event_type: event,
        client_payload: {
          triggered_by: 'Google Apps Script Webhook',
          timestamp: new Date().toISOString(),
          branch: branch
        }
      }),
      muteHttpExceptions: true
    });
    if (response.getResponseCode() === 204) return;
    throw new Error(`Trigger dispatch failed: ${response.getContentText()}`);
  } catch (e) {
    getss(branch).appendRow([new Date(), "FATAL: Error during triggerDispatches UrlFetchApp.fetch.", e.toString()]);
  }
}

// -------- Main webhook handler --------
function doPost(e) {
  const update = JSON.parse(e.postData.contents);
  try {
    if (!update.commits || update.commits.length === 0) {
      getss('log').appendRow([new Date(), "Received a webhook event without commits.", JSON.stringify(update, null, 2)]);
      return ContentService.createTextOutput("OK - Ping received").setMimeType(ContentService.MimeType.TEXT);
    }

    // -------- Branch detection --------
    const parts = update.ref.split('/');
    const branch = parts.length >= 3 ? parts.slice(2).join('/') : null;
    getss(branch).appendRow([new Date(), JSON.stringify(update, null, 2)]);

    // -------- Check for skip-execute conditions --------
    if (shouldSkipExecution(update)) {
      getss(branch).appendRow([
        new Date(), 
        "Skipping execution: [skip-execute] marker found or only tcp.json was modified.", 
        JSON.stringify(update, null, 2)
      ]);
      return ContentService.createTextOutput("OK - Execution skipped (tcp.json-only or skip marker)").setMimeType(ContentService.MimeType.TEXT);
    }

    // -------- Switch case for file changes --------
    let workflow, logMsg, resultMsg;

    switch (true) {
      case detectFile(update, '.github/workflows/generate.py'):
        workflow = 'generate-tests';
        logMsg = "'generate.py' was changed. Triggering generate-tests workflow.";
        resultMsg = "OK - Generate Workflow Triggered";
        break;
      case detectFile(update, 'test/test-cases.json'):
        workflow = 'setup-matrices';
        logMsg = "'test/test-cases.json' was changed. Triggering setup-matrices workflow.";
        resultMsg = "OK - Setup Workflow Triggered";
        break;
      case detectFile(update, 'test/tcp.json'):
        workflow = 'execute-tests';
        logMsg = "'test/tcp.json' was changed. Triggering execute-tests workflow.";
        resultMsg = "OK - Execute Workflow Triggered";
        break;
      case detectFile(update, 'test/string-distances/input.json'):
        workflow = 'prioritize-cases';
        logMsg = "'test/string-distance/input.json' was changed. Triggering prioritize-cases workflow.";
        resultMsg = "OK - Prioritize Workflow Triggered";
        break;
      default:
        getss(branch).appendRow([new Date(), "Other files changed. Exiting to avoid infinite loop.", JSON.stringify(update, null, 2)]);
        return ContentService.createTextOutput("OK - no workflow triggered.").setMimeType(ContentService.MimeType.TEXT);
    }

    triggerDispatches(workflow, branch);
    getss(branch).appendRow([new Date(), logMsg, JSON.stringify(update, null, 2)]);
    return ContentService.createTextOutput(resultMsg).setMimeType(ContentService.MimeType.TEXT);

  } catch (error) {
    getss('log').appendRow([new Date(), "An error occurred.", JSON.stringify(update, null, 2), error.stack]);
    return ContentService.createTextOutput("Error").setMimeType(ContentService.MimeType.TEXT).setStatusCode(500);
  }
}
