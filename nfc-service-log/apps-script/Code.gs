/**
 * Home Services Log - NFC tap receiver.
 * Bound to the "Home Services Log" Google Sheet (Extensions > Apps Script).
 *
 * Each tap POSTs {"service": "Laundry", "source": "NFC"}.
 * Appends to the service's own tab (Date, Time, Service, Source) and to
 * "All Services" (Date, Time, Service, Source, Email ID, Tap ID).
 */
const SECRET_PROPERTY = 'TAP_TOKEN';          // set in Project Settings > Script properties
const ALL_TAB = 'All Services';
const DEFAULT_EMAIL = 'Cristyan.david99@gmail.com';
// Notion "Home Services Log" database. Script properties needed: NOTION_TOKEN
const NOTION_DB_ID = '20f6be6bfc124b03a5ac35a93f5cecc5';
const SERVICES = ['Garbage', 'Coffee Mug', 'Coffee Machine', 'Laundry', 'Toothbrush'];

function doPost(e) {
  const lock = LockService.getScriptLock();
  lock.waitLock(10000);
  try {
    const expected = PropertiesService.getScriptProperties().getProperty(SECRET_PROPERTY);
    if (!expected || (e.parameter && e.parameter.token) !== expected) {
      return json_({ ok: false, error: 'unauthorized' });
    }
    const body = JSON.parse((e.postData && e.postData.contents) || '{}');
    const service = SERVICES.find(s => s.toLowerCase() === String(body.service || '').trim().toLowerCase());
    if (!service) return json_({ ok: false, error: 'unknown service: ' + body.service });

    const ss = SpreadsheetApp.getActiveSpreadsheet();
    const tz = ss.getSpreadsheetTimeZone();
    const now = new Date();
    const date = Utilities.formatDate(now, tz, 'yyyy-MM-dd');
    const time = Utilities.formatDate(now, tz, 'HH:mm:ss');
    const source = body.source || 'NFC';
    const tapId = Utilities.formatDate(now, tz, 'yyyyMMddHHmmss') + '-' + service.replace(/\s+/g, '').slice(0, 4).toUpperCase();

    ss.getSheetByName(service).appendRow([date, time, service, source]);
    ss.getSheetByName(ALL_TAB).appendRow([date, time, service, source, body.emailId || DEFAULT_EMAIL, tapId]);
    const notion = toNotion_(service, source, now, tz, body.emailId || DEFAULT_EMAIL, tapId);
    return json_({ ok: true, message: service + ' logged ' + date + ' ' + time + (notion ? '' : ' (Notion failed)') });
  } catch (err) {
    return json_({ ok: false, error: String(err) });
  } finally {
    lock.releaseLock();
  }
}

/** Adds a row to the Notion database. Never throws, so a Notion outage can't lose the Sheet row. */
function toNotion_(service, source, now, tz, email, tapId) {
  const token = PropertiesService.getScriptProperties().getProperty('NOTION_TOKEN');
  if (!token) return false;
  try {
    const res = UrlFetchApp.fetch('https://api.notion.com/v1/pages', {
      method: 'post',
      contentType: 'application/json',
      muteHttpExceptions: true,
      headers: { Authorization: 'Bearer ' + token, 'Notion-Version': '2022-06-28' },
      payload: JSON.stringify({
        parent: { database_id: NOTION_DB_ID },
        properties: {
          'Name': { title: [{ text: { content: service + ' - ' + Utilities.formatDate(now, tz, 'yyyy-MM-dd HH:mm') } }] },
          'Service': { select: { name: service } },
          'Logged At': { date: { start: Utilities.formatDate(now, tz, "yyyy-MM-dd'T'HH:mm:ssXXX") } },
          'Source': { select: { name: source } },
          'Email ID': { email: email },
          'Tap ID': { rich_text: [{ text: { content: tapId } }] },
        },
      }),
    });
    return res.getResponseCode() === 200;
  } catch (e) { return false; }
}

function doGet() { return json_({ ok: true, message: 'Home Services Log endpoint is up' }); }

function json_(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj)).setMimeType(ContentService.MimeType.JSON);
}
