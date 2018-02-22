"""
Copyright ©2018. The Regents of the University of California (Regents). All Rights Reserved.

Permission to use, copy, modify, and distribute this software and its documentation
for educational, research, and not-for-profit purposes, without fee and without a
signed licensing agreement, is hereby granted, provided that the above copyright
notice, this paragraph and the following two paragraphs appear in all copies,
modifications, and distributions.

Contact The Office of Technology Licensing, UC Berkeley, 2150 Shattuck Avenue,
Suite 510, Berkeley, CA 94720-1620, (510) 643-7201, otl@berkeley.edu,
http://ipira.berkeley.edu/industry-info for commercial licensing opportunities.

IN NO EVENT SHALL REGENTS BE LIABLE TO ANY PARTY FOR DIRECT, INDIRECT, SPECIAL,
INCIDENTAL, OR CONSEQUENTIAL DAMAGES, INCLUDING LOST PROFITS, ARISING OUT OF
THE USE OF THIS SOFTWARE AND ITS DOCUMENTATION, EVEN IF REGENTS HAS BEEN ADVISED
OF THE POSSIBILITY OF SUCH DAMAGE.

REGENTS SPECIFICALLY DISCLAIMS ANY WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE. THE
SOFTWARE AND ACCOMPANYING DOCUMENTATION, IF ANY, PROVIDED HEREUNDER IS PROVIDED
"AS IS". REGENTS HAS NO OBLIGATION TO PROVIDE MAINTENANCE, SUPPORT, UPDATES,
ENHANCEMENTS, OR MODIFICATIONS.
"""


from boac import db, std_commit
from boac.lib import http
from boac.lib.mockingbird import fixture
from boac.models.json_cache import JsonCache
from flask import current_app as app


LAST_SYNC_DATE_KEY = 'asc_athletes_last_sync'


def asc_feed_key(sync_date):
    return f'asc_athletes_{sync_date}'


def confirm_sync(sync_date):
    if JsonCache.query.filter_by(key=LAST_SYNC_DATE_KEY).first():
        db.session.query(JsonCache).filter(JsonCache.key == LAST_SYNC_DATE_KEY).delete()
    db.session.add(JsonCache(key=LAST_SYNC_DATE_KEY, json=sync_date))
    std_commit()


def get_current_feed():
    response = _get_current_feed()
    if not response or not hasattr(response, 'json'):
        return None
    # The API responds with a hash whose values correspond to the rows of a CSV or TSV.
    asc_hash = response.json()
    rows = [r for r in asc_hash.values()]
    return rows


@fixture('asc_athletes')
def _get_current_feed(mock=None):
    url = app.config['ASC_ATHLETES_API_URL']
    with mock(url):
        headers = {
            'Accept': 'application/json',
        }
        auth_params = {
            'ETSkey': app.config['ASC_ATHLETES_API_KEY'],
        }
        return http.request(url, headers, auth_params=auth_params)


def get_last_sync_date():
    item = JsonCache.query.filter_by(key=LAST_SYNC_DATE_KEY).first()
    return item and item.json


def get_past_feed(date):
    item = JsonCache.query.filter_by(key=asc_feed_key(date)).first()
    return item and item.json


def get_updates():
    last_sync_date = get_last_sync_date()
    current_rows = get_current_feed()
    sync_date = current_rows[0]['SyncDate']
    if sync_date != current_rows[-1]['SyncDate']:
        msg = f'Conflicting SyncDate values in ASC Athletes API: {current_rows[0]} vs. {current_rows[-1]}'
        app.logger.error(msg)
        return {
            'error': msg,
        }
    if last_sync_date != sync_date:
        stash_feed(current_rows)
    else:
        app.logger.warning(f'Current SyncDate {sync_date} matches last SyncDate; existing cache will not be overwritten')
    return {
        'last_sync_date': last_sync_date,
        'this_sync_date': sync_date,
        'feed': current_rows,
    }


def stash_feed(rows):
    sync_date = rows[0]['SyncDate']
    key = asc_feed_key(sync_date)
    if JsonCache.query.filter_by(key=key).first():
        db.session.query(JsonCache).filter(JsonCache.key == key).delete()
    db.session.add(JsonCache(key=key, json=rows))
    std_commit()
