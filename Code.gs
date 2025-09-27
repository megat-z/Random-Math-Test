// --- Configuration: use Script Properties for repo dispatch and PAT ---
function getConfig() {
  const scriptProperties = PropertiesService.getScriptProperties();
  return {
    url: scriptProperties.getProperty("DISPATCH_URL"),
    pat: scriptProperties.getProperty("GITHUB_PAT")
  };
}

/**
 * Handles incoming POST requests from GitHub Actions.
 */
function doPost(e) {
  const update = JSON.parse(e.postData.contents);
  try {
    // Check if the payload contains commits.
    if (!update.commits || update.commits.length === 0) {
      return ContentService.createTextOutput("OK - Ping received").setMimeType(ContentService.MimeType.TEXT);
    }
    // Check if any of the commits in the push include the addition or modification of 'test/test-cases.json',
    const testCaseChanges = update.commits.some(commit => {
      const wasAdded = commit.added && commit.added.includes('test/test-cases.json');
      const wasModified = commit.modified && commit.modified.includes('test/test-cases.json');
      return wasAdded || wasModified;
    });
    // Trigger the GitHub Actions workflow if test cases file was changed
    if (testCaseChanges){
      triggerSetup();
      return ContentService.createTextOutput("OK - Setup Workflow Triggered").setMimeType(ContentService.MimeType.TEXT);
    } else {
      return ContentService.createTextOutput("OK - Condition not met").setMimeType(ContentService.MimeType.TEXT);
    }
  } catch (error) {
    return ContentService.createTextOutput("Error").setMimeType(ContentService.MimeType.TEXT).setStatusCode(500);
  }
}

/**
 * Triggers the 'setup-matrices' workflow in the repository.
 */
function triggerSetup() {
  try {
    const config = getConfig();
    if (!config.githubPAT || !config.dispatchURL) {
      return ContentService.createTextOutput("Error - Missing GITHUB_PAT or DISPATCH_URL in script properties").setMimeType(ContentService.MimeType.TEXT).setStatusCode(500);
    }
    const response = UrlFetchApp.fetch(config.url, {
      method: 'post',
      contentType: 'application/json',
      headers: {
        'Authorization': 'Bearer ' + config.pat
        'Accept': 'application/vnd.github.v3+json'
      },
      payload: JSON.stringify({
        event_type: 'setup-matrices',
        client_payload: {
          triggered_by: 'Google Apps Script Webhook',
          timestamp: new Date().toISOString()
        }
      }),
      muteHttpExceptions: true
    });
    if (response.getResponseCode() === 204) return;
    throw new Error(`Trigger setup failed: ${response.getContentText()}`);
  } catch (e) {
    throw new Error(`Trigger setup failed: ${JSON.stringify(e.stack)}`);
  }
}
