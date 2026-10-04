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
    ss.getSheetByName(ALL_TAB).appendRow([date, time, service, source, body.emailId || '', tapId]);
    return json_({ ok: true, message: service + ' logged ' + date + ' ' + time });
  } catch (err) {
    return json_({ ok: false, error: String(err) });
  } finally {
    lock.releaseLock();
  }
}

function doGet() { return json_({ ok: true, message: 'Home Services Log endpoint is up' }); }

function json_(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj)).setMimeType(ContentService.MimeType.JSON);
}
